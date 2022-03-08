// SPDX-License-Identifier: MIT
pragma solidity 0.8.11;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {SafeMath} from "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "./interfaces/IFeeDistributor.sol";
import "./interfaces/IChainlink.sol";

import '@uniswap/v3-periphery/contracts/interfaces/ISwapRouter.sol';
import '@uniswap/v3-periphery/contracts/libraries/TransferHelper.sol';

/** @title FeeCustody
    @notice Custody Contract for Ribbon Vault Management / Performance Fees
 */

contract FeeCustody {
    using SafeERC20 for IERC20;
    using SafeMath for uint256;

    // Distribution token for fee distributor: like RBN, USDC, ETH, etc
    IERC20 public distributionToken;
    // Protocol revenue recipient
    address public protocolRevenueRecipient;
    // Address of fee distributor contract for RBN lockers to claim
    IFeeDistributor public feeDistributor;
    // Admin
    address public admin;
    // % allocation (0 - 100%) from protocol revenue to allocate to RBN lockers.
    // 2 decimals. ex: 10% = 1000
    uint256 public pctAllocationForRBNLockers;

    uint256 public constant TOTAL_PCT = 10000; // Equals 100%
    ISwapRouter public constant UNIV3_SWAP_ROUTER = ISwapRouter(0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45);

    // -1 = Removed
    // 0 = Not Added
    // -1 = Added
    mapping(address => int8) public assetStatus;

    // Intermediary path asset for univ3 swaps.
    // Empty if direct pool swap between asset and distribution asset
    // ex: for ETH -> USDC _intermediaryPath = [] (ETH -> USDC)
    // ex: for AAVE -> USDC _intermediaryPath = [ETH] (AAVE -> ETH -> USDC)
    mapping(address => address[]) public intermediaryPath;

    // Oracle between asset/usd pair for total
    // reward approximation across all assets earned
    mapping(address => address) public oracles;

    // Pool fees for Univ3 swap
    // Length 1 if direct swap between asset and distribution asset
    // Length 2 if swap with intermediary asset
    mapping(address => uint24[]) public poolFees;

    address[100] assets;
    // Index of empty slot in assets array
    uint256 public lastAssetIdx;

    // Events
    event RemoveAsset(address asset);
    event NewAsset(address asset, address[] intermediaryPath, address[] poolFees);
    event RecoveredAsset(address asset);
    event NewFeeDistributor(address feeDistributor);
    event NewRBNLockerAllocation(uint256 pctAllocationForRBNLockers);
    event NewDistributionToken(address distributionToken);
    event NewProtocolRevenueRecipient(address protocolRevenueRecipient);
    event NewAdmin(address admin);

    /**
     * @notice
     * Constructor
     * @param _pctAllocationForRBNLockers percent allocated for RBN lockers (100% = 10000)
     * @param _distributionToken asset to distribute to RBN lockers
     * @param _feeDistributor address of fee distributor where protocol revenue claimable
     * @param _protocolRevenueRecipient address of multisig
     * @param _admin admin
     */
    constructor(
        uint256 _pctAllocationForRBNLockers,
        address _distributionToken,
        address _feeDistributor,
        address _protocolRevenueRecipient,
        address _admin
    ) {
        require(_pctAllocationForRBNLockers != 0, "!0");
        require(_distributionToken != address(0), "!address(0)");
        require(_feeDistributor != address(0), "!address(0)");
        require(_protocolRevenueRecipient != address(0), "!address(0)");
        require(_admin != address(0), "!address(0)");

        pctAllocationForRBNLockers = _pctAllocationForRBNLockers;
        distributionToken = IERC20(_distributionToken);
        feeDistributor = IFeeDistributor(_feeDistributor);
        protocolRevenueRecipient = _protocolRevenueRecipient;
        admin = _admin;
    }

    // Modifier for only admin methods
    modifier onlyAdmin {
          require(msg.sender == admin);
          _;
    }

    /**
     * @notice
     * Swaps RBN locker allocation of protocol revenu to distributionToken,
     * sends the rest to the multisig
     * @dev Can be called by admin
     * @return amount of distributionToken distributed to fee distributor
     */
    function distributeProtocolRevenue() external onlyAdmin returns (uint256 toDistribute) {
      for(uint i; i < lastAssetIdx; i++){
        // If we removed asset as part of
        // protocol revenue distribution, skip
        if(assetStatus[assets[i]] == -1){
          continue;
        }

        IERC20 asset = IERC20(assets[i]);
        uint256 assetBalance = asset.balanceOf(address(this));

        uint256 multiSigRevenue = assetBalance.mul(TOTAL_PCT.sub(pctAllocationForRBNLockers)).div(TOTAL_PCT);

        // If we are holding the distributionToken itself,
        // do not swap
        if(address(asset) != address(distributionToken)){
          // Calculate RBN allocation amount to swap for distributionToken
          uint256 amountIn = assetBalance.sub(multiSigRevenue);
          _swap(asset, amountIn);
        }

        // Transfer multisig allocation of protocol revenue to multisig
        asset.transfer(protocolRevenueRecipient, multiSigRevenue);
      }

      toDistribute += distributionToken.balanceOf(address(this));
      distributionToken.safeApprove(address(feeDistributor), toDistribute);

      // Tranfer RBN locker allocation of protocol revenue to fee distributor
      feeDistributor.burn(address(distributionToken), toDistribute);
    }

    /**
     * @notice
     * Amount of _asset allocated to RBN lockers from current balance
     * @return amount allocated to RBN lockers
     */
    function claimableByRBNLockersOfAsset(address _asset) external view returns (uint256) {
      uint256 allocPCT = pctAllocationForRBNLockers;
      return IERC20(_asset).balanceOf(address(this)).mul(allocPCT).div(TOTAL_PCT);
    }

    /**
     * @notice
     * Amount of _asset allocated to multisig from current balance
     * @return amount allocated to multisig
     */
    function claimableByProtocolOfAsset(address _asset) external view returns (uint256) {
      uint256 allocPCT = TOTAL_PCT.sub(pctAllocationForRBNLockers);
      return IERC20(_asset).balanceOf(address(this)).mul(allocPCT).div(TOTAL_PCT);
    }

    /**
     * @notice
     * Total allocated to RBN lockers across all assets balances
     * @return total allocated (in USD)
     */
    function totalClaimableByRBNLockersInUSD() external view returns (uint256) {
      uint256 allocPCT = pctAllocationForRBNLockers;
      return _getSwapQuote(allocPCT);
    }

    /**
     * @notice
     * Total allocated to multisig across all assets balances
     * @return total allocated (in USD)
     */
    function totalClaimableByProtocolInUSD() external view returns (uint256) {
      uint256 allocPCT = TOTAL_PCT.sub(pctAllocationForRBNLockers);
      return _getSwapQuote(allocPCT);
    }

    /**
     * @notice
     * Total claimable across all asset balances based on allocation PCT
     * @param _allocPCT allocation percentage
     * @return total claimable (in USD)
     */
    function _getSwapQuote(uint256 _allocPCT) internal view returns (uint256 claimable) {
      for(uint i; i < lastAssetIdx; i++){
        // If we removed asset as part of
        // protocol revenue distribution, skip
        if(assetStatus[assets[i]] == -1){
          continue;
        }

        IChainlink oracle = IChainlink(oracles[assets[i]]);

        // Approximate claimable by multiplying
        // current asset balance with current asset price in USD
        claimable += IERC20(assets[i]).balanceOf(address(this))
          .mul(oracle.latestAnswer())
          .mul(_allocPCT)
          .div(oracle.decimals())
          .div(TOTAL_PCT);
      }
    }

    /**
     * @notice
     * Swaps _amountIn of _asset into distributionToken
     * @param _asset asset to swap from
     * @param _amountIn amount to swap of asset
     */
    function _swap(address _asset, uint256 _amountIn) internal {
      TransferHelper.safeApprove(asset, address(UNIV3_SWAP_ROUTER), _amountIn);

      address[] memory _intermediaryPath = intermediaryPath[_asset];
      address[] memory _poolFees = poolFees[_asset];

      // Multiple pool swaps are encoded through bytes called a `path`.
      // A path is a sequence of token addresses and poolFees that define the pools used in the swaps.
      // The format for pool encoding is (tokenIn, fee, tokenOut/tokenIn, fee, tokenOut)
      // where tokenIn/tokenOut parameter is the shared token across the pools.

      bytes pathEncoding;
      if(_intermediaryPath.length > 0){
        pathEncoding = abi.encodePacked(_asset, _poolFees[0], _intermediaryPath[0], _poolFees[1], address(distributionToken));
      }else{
        pathEncoding = abi.encodePacked(_asset, _poolFees[0], address(distributionToken));
      }

      ISwapRouter.ExactInputParams memory params =
          ISwapRouter.ExactInputParams({
              path: pathEncoding,
              recipient: msg.sender,
              deadline: block.timestamp,
              amountIn: amountIn,
              amountOutMinimum: 0
          });

      // Executes the swap.
      UNIV3_SWAP_ROUTER.exactInput(params);
    }

    /**
     * @notice
     * add asset
     * @dev Can be called by admin
     * @param _asset new asset
     * @param _oracle ASSET/USD ORACLE.
     * @param _intermediaryPath path for univ3 swap.
     * @param _poolFee fees for asset / distributionToken.
     * @param _isUpdate if we are updating existing asset / setting asset

     * If intermediary path then pool fee between both pairs
     * (ex: AAVE / ETH , ETH / USDC)
     * NOTE: if intermediaryPath empty then single hop swap
     * OR remain unchanged if asset had already been added.
     * NOTE: MUST BE ASSET / USD ORACLE
     * NOTE: 3000 = 0.3% fee for pool fees
     */
    function setAsset(address _asset, address _oracle, address[] calldata _intermediaryPath, address[] calldata _poolFees, bool _isUpdate) external onlyAdmin {
        require(_asset != address(0), "!address(0)");
        // We must be setting new valid oracle, or want to keep as is if one exists
        require((oracles[_asset] != address(0) && _oracle == address(0)) || IChainlink(oracles[_asset]).decimals() == 8, "!ASSET/USD");

        uint8 _pathLen = _intermediaryPath.length;
        uint8 _swapFeeLen = _poolFees.length;
        uint8 _assetStatus = assetStatus[_asset];

        require(_pathLen < 2, "invalid intermediary path");
        require(((_assetStatus == 0 && _swapFeeLen > 0) || _assetStatus > 0) &&  _swapFeeLen < 2, "invalid pool fees array length");

        // If not set asset
        if(_assetStatus == 0){
          assets[lastAssetIdx] = _asset;
          lastAssetIdx += 1;
        }

        assetStatus[_asset] = 1;

        // If we want to update
        if(_isUpdate){
          oracles[_asset] = _oracle;
          intermediaryPath[_asset] = _intermediaryPath;
          poolFees[_asset] = _poolFees;
        }

        emit NewAsset(_asset, _intermediaryPath, _poolFees);
    }

    /**
     * @notice
     * remove asset
     * @dev Can be called by admin
     * @param _asset asset to remove
     */
    function removeAsset(address _asset) external onlyAdmin {
        require(_asset != address(0), "!address(0)");
        if(assetStatus[_asset] > 0){
          assetStatus[_asset] = -1;
          emit RemoveAsset(_asset);
        }
    }

    /**
     * @notice
     * recover all assets
     * @dev Can be called by admin
     */
    function recoverAllAssets() external onlyAdmin {
        // For all added assets, if not removed, send to protocol revenue recipient
        for(uint i = 0; i < lastAssetIdx; i++){
          _recoverAsset(assets[i]);
        }
    }

    /**
     * @notice
     * recover specific asset
     * @dev Can be called by admin
     * @param _asset asset to recover
     */
    function recoverAsset(address _asset) external onlyAdmin {
      require(_asset != address(0), "!address(0)");
      _recoverAsset(_asset);
    }

    /**
     * @notice
     * recovers asset logic
     * @param _asset asset to recover
     */
    function _recoverAsset(address _asset) internal {
      IERC20 asset = IERC20(_asset);
      uint256 bal = asset.balanceOf(address(this));
      if(bal > 0){
        asset.transfer(protocolRevenueRecipient, bal);
        emit RecoveredAsset(_asset);
      }
    }

    /**
     * @notice
     * set fee distributor
     * @dev Can be called by admin
     * @param _feeDistributor new fee distributor
     */
    function setFeeDistributor(address _feeDistributor) external onlyAdmin {
        require(_feeDistributor != address(0), "!address(0)");
        feeDistributor = IFeeDistributor(_feeDistributor);
        emit NewFeeDistributor(_feeDistributor);
    }

    /**
     * @notice
     * set rbn locker allocation pct
     * @dev Can be called by admin
     * @param _pctAllocationForRBNLockers new allocation for rbn lockers
     */
    function setRBNLockerAllocPCT(uint256 _pctAllocationForRBNLockers) external {
        require(_pctAllocationForRBNLockers != 0, "!0");
        pctAllocationForRBNLockers = _pctAllocationForRBNLockers;
        emit NewRBNLockerAllocation(_pctAllocationForRBNLockers);
    }

    /**
     * @notice
     * set new distribution asset
     * @dev Can be called by admin
     * @param _distributionToken new distribution token
     */
    function setDistributionToken(address _distributionToken) external onlyAdmin {
        require(_distributionToken != address(0), "!address(0)");
        distributionToken = IERC20(_distributionToken);
        emit NewDistributionToken(_distributionToken);
    }

    /**
     * @notice
     * set protocol revenue recipient
     * @dev Can be called by admin
     * @param _protocolRevenueRecipient new protocol revenue recipient
     */
    function setProtocolRevenueRecipient(address _protocolRevenueRecipient) external onlyAdmin {
        require(_protocolRevenueRecipient != address(0), "!address(0)");
        protocolRevenueRecipient = _protocolRevenueRecipient;
        emit NewProtocolRevenueRecipient(_protocolRevenueRecipient);
    }


    /**
     * @notice
     * set admin
     * @dev Can be called by admin
     * @param _admin new admin
     */
    function setAdmin(address _admin) external onlyAdmin {
        require(_admin != address(0), "!address(0)");
        admin = _admin;
        emit NewAdmin(_admin);
    }
}
