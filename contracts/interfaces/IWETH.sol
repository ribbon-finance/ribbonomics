// SPDX-License-Identifier: MIT
pragma solidity 0.8.11;
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IWETH is IERC20 {
    function balanceOf(address) external view returns (uint256);

    function deposit() external payable;

    function withdraw(uint256) external;

}
