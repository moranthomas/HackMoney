// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.6;

import {Clones} from "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/proxy/Clones.sol";
import {Address} from "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/utils/Address.sol";

abstract contract ProxyOwnableData {
    address private _owner;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    function _initializeData(address newOwner) internal virtual {
	assembly { if gt(_owner.slot, 0) { revert(0, 0) } } // dev: owner slot is not zero
	require(_owner == address(0)); // dev: contract already initialized
	emit OwnershipTransferred(address(0), newOwner);
	_owner = newOwner;
    }

    function owner() public view virtual returns (address) {
        return _owner;
    }

    modifier onlyOwner() {
        require(owner() == msg.sender); // dev: Ownable: caller is not the owner
        _;
    }

    function renounceOwnership() public virtual onlyOwner {
        emit OwnershipTransferred(_owner, address(0));
        _owner = address(0);
    }

    function transferOwnership(address newOwner) public virtual onlyOwner {
	require(newOwner != address(0)); // dev: Ownable: new owner is the zero address
	emit OwnershipTransferred(_owner, newOwner);
	_owner = newOwner;
    }
}

abstract contract ProxyWalletData is ProxyOwnableData {
    uint256 internal storedData;

    function _initializeData(address newOwner) internal override {
        super._initializeData(newOwner);
	storedData = 5;
    }

    function set(uint256 _x) public onlyOwner {
        storedData = _x;
    }

    function get() public view returns (uint256) {
        return storedData;
    }
}

contract ProxyWallet is ProxyWalletData {
    using Clones for address;
    using Address for address;

    constructor() {
	super._initializeData(address(~uint160(0)));
    }

    function initializeProxy(address owner) external {
	require(Clones.predictDeterministicAddress(msg.sender,
						   bytes32(uint256(uint160(owner))),
						   msg.sender) == address(this)); // dev: must be called by deployer
	super._initializeData(owner);
    }

    function destroyClone() external onlyOwner {
	require(isClone()); // dev: only proxies can be destroyed
	selfdestruct(payable(msg.sender));
    }

    function isClone() view public returns (bool result) {
	assembly {
	    result := iszero(eq(codesize(), extcodesize(address())))
	}
    }

    function proxyAddress() view public returns (address) {
	address a;
	assembly {
	    extcodecopy(address(), 0, 0, 32)
	    codecopy(32, 0, 32)
	    a := mload(0)
	    if eq(a, mload(32)) { a := 0 }
	    a := shr(16, a)
	}
	return a;
    }

    function getCloneAddress() view public returns (address) {
	return Clones.predictDeterministicAddress(address(this), bytes32(uint256(uint160(msg.sender))));
    }

    function getCloneOrNull() view external returns (ProxyWallet) {
	address addr = getCloneAddress();
	if (!addr.isContract()) addr = address(0);
	return ProxyWallet(addr);
    }

    function getClone() view external returns (ProxyWallet) {
	address addr = getCloneAddress();
	require(addr.isContract()); // dev: clone not created
	return ProxyWallet(addr);
    }

    function getOrCreateClone() external returns (ProxyWallet) {
	address addr = getCloneAddress();
	if (!addr.isContract()) {
            require(!isClone()); // dev: cannot create clone from clone
	    Clones.cloneDeterministic(address(this), bytes32(uint256(uint160(msg.sender))));
	    ProxyWallet(addr).initializeProxy(msg.sender);
	}
	return ProxyWallet(addr);	
    }
}
