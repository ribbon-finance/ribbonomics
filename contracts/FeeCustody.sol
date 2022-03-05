// SPDX-License-Identifier: MIT
pragma solidity 0.8.11;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {SafeMath} from "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "./interfaces/IFeeDistributor.sol";

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

    mapping(address => bool) public assetRemoved;
    address[100] assets;
    uint256 public lastAssetIdx;

    event RemoveAsset(address asset);
    event NewAsset(address asset);
    event RecoveredAsset(address asset);
    event NewFeeDistributor(address feeDistributor);
    event NewRBNLockerAllocation(uint256 pctAllocationForRBNLockers);
    event NewDistributionToken(address distributionToken);
    event NewProtocolRevenueRecipient(address protocolRevenueRecipient);
    event NewAdmin(address admin);

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

    modifier onlyAdmin {
          require(msg.sender == admin);
          _;
    }

    function distributeProtocolRevenue() external onlyAdmin {

    }

    function claimableByRBNLockers() external view returns (uint256) {
      uint256 allocPCT = pctAllocationForRBNLockers;
      return allocPCT;
    }

    function claimableByProtocol() external view returns (uint256) {
      uint256 allocPCT = uint256(10000).sub(pctAllocationForRBNLockers);
      return _swappable(allocPCT, false);
    }

    function _swappable(uint256 allocPCT, bool isSwap) internal view returns (uint256 claimable) {
      if(isSwap){
        admin = assets[0];
      }
      // For all added assets, if not removed, calculate USDC amount
      for(uint i = 0; i < lastAssetIdx; i++){
        if(assetRemoved[assets[i]]){
          continue;
        }

        IERC20 asset = IERC20(assets[i]);

        if(assets[i] == address(distributionToken)){
          claimable += allocPCT.mul(asset.balanceOf(address(this))).div(10000);
          continue;
        }

        // approve
        // swap()
        // calculate last balance
        // append to burnable
        // approve to fee distributor
        // burn

      }
    }

    /**
     * @notice
     * add asset
     * @dev Can be called by admin
     * @param _asset new asset
     */
    function addAsset(address _asset) external onlyAdmin {
        require(_asset != address(0), "!address(0)");
        if(assetRemoved[_asset]){
          assetRemoved[_asset] = false;
        }else{
          assets[lastAssetIdx] = _asset;
          lastAssetIdx += 1;
        }
        emit NewAsset(_asset);
    }

    /**
     * @notice
     * remove asset
     * @dev Can be called by admin
     * @param _asset asset to remove
     */
    function removeAsset(address _asset) external onlyAdmin {
        require(_asset != address(0), "!address(0)");
        if(!assetRemoved[_asset]){
          assetRemoved[_asset] = true;
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
     * recover specific asset assets
     * @dev Can be called by admin
     * @param _asset asset to recover
     */
    function recoverAsset(address _asset) external onlyAdmin {
      require(_asset != address(0), "!address(0)");
      _recoverAsset(_asset);
    }

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
