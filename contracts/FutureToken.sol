// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.6;

import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/IERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/extensions/IERC20Metadata.sol";
import {Clones} from "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/proxy/Clones.sol";
import {Address} from "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/utils/Address.sol";

enum InstanceType {
    None,  // 0x0 0b000
    Base,  // 0x1 0b001
    Long,  // 0x2 0b010
    Short, // 0x3 0b011
    Class  // 0x4 0b100
}

abstract contract FutureTokenBaseData {
    InstanceType internal _instance_type;
    address internal _owner;
}

abstract contract FutureTokenClassData {
    IERC20Metadata internal _class_ctoken;
    uint256 internal _class_expiry;
    //    uint256 internal _class_margin_ratio;
    FutureToken internal _class_series_short;
    FutureToken internal _class_series_long;
}

abstract contract FutureTokenSeriesData {
    address internal _series_class_owner;
    mapping(address => uint256) internal _series_balances;
    mapping(address => mapping(address => uint256)) internal _series_allowances;
    string internal _series_symbol;
    //    string internal _series_name;
    //    uint8 internal _series_decimal;
    uint256 internal _series_totalSupply;
}

abstract contract FutureTokenBase is FutureTokenBaseData {
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    uint8 constant internal SERIES_DECIMALS = 18;
    uint256 constant internal SERIES_MARGIN_RATIO_DIVISOR = 1_000000_000000_000000;
    uint256 constant internal SERIES_MARGIN_RATIO_MULTIPLIER = 25000_000000_000000;

    function instanceType() external view returns (InstanceType) {
	return _instance_type;
    }

    function owner() external view onlyIfBase returns (address) {
        return _owner;
    }

    function renounceOwnership() external onlyIfBase onlyOwner {
        emit OwnershipTransferred(_owner, address(0));
        _owner = address(0);
    }

    function transferOwnership(address newOwner) external onlyIfBase onlyOwner {
	require(newOwner != address(0)); // dev: FutureTokenBase: new owner is the zero address
	emit OwnershipTransferred(_owner, newOwner);
	_owner = newOwner;
    }

    modifier onlyOwner() {
        require(_owner == msg.sender); // dev: FutureTokenBase: caller is not the owner
	_;
    }

    modifier onlyIfBase() {
        require(_instance_type == InstanceType.Base); // dev: FutureTokenData: only valid for base
	_;
    }

    modifier onlyIfClass() {
        require(_instance_type == InstanceType.Class); // dev: FutureTokenData: only valid for class
	_;
    }

    modifier onlyIfSeries() {
        require(uint(_instance_type) >> 1 == 1); // dev: FutureTokenData: only valid for series
	_;
    }
}

abstract contract FutureTokenClass is
    FutureTokenBase,
    FutureTokenClassData
{
    function ctoken() external view /*onlyIfClass*/ returns (IERC20Metadata) {
	return _class_ctoken;
    }

    function expiry() external view /*onlyIfClass*/ returns (uint256) {
	return _class_expiry;
    }

    function seriesShort() external view /*onlyIfClass*/ returns (FutureToken) {
	return _class_series_short;
    }

    function seriesLong() external view /*onlyIfClass*/ returns (FutureToken) {
	return _class_series_long;
    }

    function supply(uint256 amount) external returns (bool) {
	require(amount > 0); // dev: amount must be non-zero
	require(_class_ctoken.transferFrom(msg.sender, address(this), amount)); // dev: inbound transfer of ctokens failed
	uint256 mint_amount = amount * 1000_000_000_000 * SERIES_MARGIN_RATIO_DIVISOR / SERIES_MARGIN_RATIO_MULTIPLIER;
	require(FutureToken(_class_series_short).mint(msg.sender, mint_amount)); // dev: minting short tokens failed
	require(FutureToken(_class_series_long).mint(msg.sender, mint_amount)); // dev: minting long tokens failed
    }

    function redeem(uint256 burn_amount) external returns (bool) {
	IERC20 class_ctoken = _class_ctoken;
	FutureToken class_series_short = _class_series_short;
	FutureToken class_series_long = _class_series_long;
	require(burn_amount > 0); // dev: amount must be non-zero
	require(class_series_short.burn(msg.sender, burn_amount)); // dev: burning short tokens failed
	require(class_series_long.burn(msg.sender, burn_amount)); // dev: burning long tokens failed
	uint256 amount = burn_amount * SERIES_MARGIN_RATIO_MULTIPLIER / SERIES_MARGIN_RATIO_DIVISOR / 1000_000_000_000;
	require(class_ctoken.transfer(msg.sender, amount)); // dev: outbound transfer of ctokens failed
    }
}

abstract contract FutureTokenSeries is
    IERC20,
    IERC20Metadata,
    FutureTokenBase,
    FutureTokenSeriesData
{
    modifier onlyClassOwner() {
        require(_series_class_owner == msg.sender); // dev: FutureTokenSeries: caller is not the class owner
	_;
    }

    function name() external view override onlyIfSeries returns (string memory) {
        return _series_symbol; //_series_name;
    }

    function symbol() external view override onlyIfSeries returns (string memory) {
        return _series_symbol;
    }

    function decimals() public pure override /*onlyIfSeries*/ returns (uint8) {
        return SERIES_DECIMALS;
    }

    function totalSupply() external view override returns (uint256) {
        return _series_totalSupply;
    }

    function balanceOf(address _owner) external view override onlyIfSeries returns (uint256) {
        return _series_balances[_owner];
    }

    function allowance(address _owner, address _spender) external view override onlyIfSeries returns (uint256) {
        return _series_allowances[_owner][_spender];
    }

    function approve(address spender, uint256 amount) external override onlyIfSeries returns (bool) {
        _approve(msg.sender, spender, amount);
        return true;
    }

    function transfer(address recipient, uint256 amount) external override onlyIfSeries returns (bool) {
        _transfer(msg.sender, recipient, amount);
        return true;
    }

    function transferFrom(address sender, address recipient, uint256 amount) external override onlyIfSeries returns (bool) {
        _transfer(sender, recipient, amount);

        uint256 currentAllowance = _series_allowances[sender][msg.sender];
        require(currentAllowance >= amount, "ERC20: transfer amount exceeds allowance");
        _approve(sender, msg.sender, currentAllowance - amount);

        return true;
    }

    function increaseAllowance(address spender, uint256 addedValue) external onlyIfSeries returns (bool) {
        _approve(msg.sender, spender, _series_allowances[msg.sender][spender] + addedValue);
        return true;
    }

    function decreaseAllowance(address spender, uint256 subtractedValue) external onlyIfSeries returns (bool) {
        uint256 currentAllowance = _series_allowances[msg.sender][spender];
        require(currentAllowance >= subtractedValue, "ERC20: decreased allowance below zero");
        _approve(msg.sender, spender, currentAllowance - subtractedValue);

        return true;
    }

    function mint(address account, uint256 amount) external onlyIfSeries onlyClassOwner returns (bool) {
        _mint(account, amount);
	return true;
    }

    function burn(address account, uint256 amount) external onlyIfSeries onlyClassOwner returns (bool) {
        _burn(account, amount);
	return true;
    }

    function _approve(address owner, address spender, uint256 amount) private {
        require(owner != address(0), "ERC20: approve from the zero address");
        require(spender != address(0), "ERC20: approve to the zero address");

        _series_allowances[owner][spender] = amount;
        emit Approval(owner, spender, amount);
    }

    function _transfer(address sender, address recipient, uint256 amount) private {
        require(sender != address(0), "ERC20: transfer from the zero address");
        require(recipient != address(0), "ERC20: transfer to the zero address");

//        _beforeTokenTransfer(sender, recipient, amount);

        uint256 senderBalance = _series_balances[sender];
        require(senderBalance >= amount, "ERC20: transfer amount exceeds balance");
        _series_balances[sender] = senderBalance - amount;
        _series_balances[recipient] += amount;

        emit Transfer(sender, recipient, amount);
    }

    function _mint(address account, uint256 amount) private {
        require(account != address(0), "ERC20: mint to the zero address");

//        _beforeTokenTransfer(address(0), account, amount);

        _series_totalSupply += amount;
        _series_balances[account] += amount;
        emit Transfer(address(0), account, amount);
    }

    function _burn(address account, uint256 amount) private {
        require(account != address(0), "ERC20: burn from the zero address");

//        _beforeTokenTransfer(account, address(0), amount);

        uint256 accountBalance = _series_balances[account];
        require(accountBalance >= amount, "ERC20: burn amount exceeds balance");
        _series_balances[account] = accountBalance - amount;
        _series_totalSupply -= amount;

        emit Transfer(account, address(0), amount);
    }

//    function _beforeTokenTransfer(address from, address to, uint256 amount) private { }
}

contract FutureToken is
    FutureTokenClass,
    FutureTokenSeries
 {
     using Address for address;

     constructor() {
	 _instance_type = InstanceType.Base;
	 _owner = msg.sender;
     }

     function uint32ToHex(uint32 x) private returns (bytes8) {
	 uint256 y = x & 0xffff;
	 y |= (uint256(x) & 0xffff0000) << (128-16);
	 y *= (1<<(96+12)) | (1<<(64+8)) | (1<<(32+4)) | 1;
	 y &= 0x0f000000_000f0000_00000f00_0000000f_0f000000_000f0000_00000f00_0000000f;
	 y |= y >> 64;
	 y |= y >> 32;
	 y &= 0x00000000_00000000_00000000_ffffffff_00000000_00000000_00000000_ffffffff;
	 y |= y >> 96;
	 y &= 0xffffffff_ffffffff;
	 uint256 z = (y>>3) & ((y>>2)|(y>>1));
	 z &= 0x01010101_01010101;
	 z |= (z<<5) | (z<<2) | (z<<1);
	 y += 0x30303030_30303030;
	 y += z;
	 return bytes8(uint64(y));
     }
 
     function initializeChild(IERC20Metadata ctoken, uint256 expiry, uint256 margin_ratio, InstanceType instance_type) external {
	 require(instance_type == InstanceType.Long
		 || instance_type == InstanceType.Short
		 || instance_type == InstanceType.Class); // dev: must be long, short or class
	 require(address(this) == _getAddress(msg.sender, ctoken, expiry, instance_type)); // dev: must be called by base
	 require(address(ctoken) != address(0)); // dev: ctoken must be non-zero
	 require(expiry >= block.number); // dev: expiry must not be in past
	 require(expiry == calcExpiry(expiry)); // dev: expiry must be a valid expiry
	 require(margin_ratio > 0); // dev: margin ratio must be non-zero
	 require(_instance_type == InstanceType.None); // dev: instance type must be uninitialized
	 require(_owner == address(0)); // dev: owner must be uninitialized
	 require(_class_expiry == 0); // dev: class expiry must be uninitialized
	 require(address(_class_series_short) == address(0)); // dev: class series short must be uninitialized
	 require(address(_class_series_long) == address(0)); // dev: class series long must be uninitialized
	 require(address(_series_class_owner) == address(0)); // dev: series class owner must be uninitialized
	 //	 require(_series_decimal == 0); // dev: series decimal must be uninitialized
	 require(_series_totalSupply == 0); // dev: series total supply must be uninitialized
	 _instance_type = instance_type;
	 _class_ctoken = ctoken;
	 _class_expiry = expiry;
         //      _class_margin_ratio = margin_ratio;
	 if (instance_type == InstanceType.Class) {
	     _class_series_short = FutureToken(_getAddress(msg.sender, ctoken, expiry, InstanceType.Short));
	     _class_series_long = FutureToken(_getAddress(msg.sender, ctoken, expiry, InstanceType.Long));
	 } else {
	     _series_class_owner = _getAddress(msg.sender, ctoken, expiry, InstanceType.Class);
	     _series_symbol = string(abi.encodePacked("CVX/",
						      IERC20Metadata(ctoken).symbol(),
						      "/0x",
						      uint32ToHex(uint32(expiry)),
						      instance_type == InstanceType.Short ? "/S" :
						      instance_type == InstanceType.Long ? "/L" : "/X"));
	     //	     _series_decimal = SERIES_DECIMAL;
	 }
     }

     function calcExpiry(uint256 blocks) public pure returns (uint256) {
	 require(blocks < (1<<32)); // dev: block too big
	 return (((blocks - 1) >> 12) + 1) << 12;
     }

     function calcNextExpiryAfter(uint256 after_blocks) public view returns (uint256) {
	 after_blocks += block.number;
	 return calcExpiry(after_blocks);
     }

     function getExpiryClassLongShort(IERC20Metadata ctoken, uint256 expiry) external view onlyIfBase returns (address, address, address) {
	 address addr_class = _getAddress(address(this), ctoken, expiry, InstanceType.Class);
	 address addr_long = _getAddress(address(this), ctoken, expiry, InstanceType.Long);
	 address addr_short = _getAddress(address(this), ctoken, expiry, InstanceType.Short);
	 if (!addr_class.isContract()) addr_class = address(0);
	 if (!addr_long.isContract()) addr_long = address(0);
	 if (!addr_short.isContract()) addr_short = address(0);
	 return (addr_class, addr_long, addr_short);
     }

     function getOrCreateExpiryClassLongShort(IERC20Metadata ctoken, uint256 expiry) external onlyIfBase returns (address, address, address) {
	 require(address(ctoken) != address(0)); // dev: ctoken must be non-zero
	 require(expiry >= block.number); // dev: expiry must not be in past
	 address addr_class = _getAddress(address(this), ctoken, expiry, InstanceType.Class);
	 address addr_long = _getAddress(address(this), ctoken, expiry, InstanceType.Long);
	 address addr_short = _getAddress(address(this), ctoken, expiry, InstanceType.Short);
	 if (!addr_class.isContract()) {
	     require(addr_class == Clones.cloneDeterministic(address(this), _getAddressSalt(ctoken, expiry, InstanceType.Class))); // dev: clone created at unexpected address
	     FutureToken(addr_class).initializeChild(ctoken, expiry, SERIES_MARGIN_RATIO_MULTIPLIER, InstanceType.Class);
	 }
	 if (!addr_long.isContract()) {
	     require(addr_long == Clones.cloneDeterministic(address(this), _getAddressSalt(ctoken, expiry, InstanceType.Long))); // dev: clone created at unexpected address
	     FutureToken(addr_long).initializeChild(ctoken, expiry, SERIES_MARGIN_RATIO_MULTIPLIER, InstanceType.Long);
	 }
	 if (!addr_short.isContract()) {
	     require(addr_short == Clones.cloneDeterministic(address(this), _getAddressSalt(ctoken, expiry, InstanceType.Short))); // dev: clone created at unexpected address
	     FutureToken(addr_short).initializeChild(ctoken, expiry, SERIES_MARGIN_RATIO_MULTIPLIER, InstanceType.Short);
	 }
	 return (addr_class, addr_long, addr_short);
     }

     function _getAddressSalt(IERC20Metadata ctoken, uint256 expiry, InstanceType instance_type) pure internal returns (bytes32) {
	 return keccak256(abi.encodePacked(ctoken, expiry, uint8(instance_type)));
     }

     function _getAddress(address main, IERC20Metadata ctoken, uint256 expiry, InstanceType instance_type) pure internal returns (address) {
	 return Clones.predictDeterministicAddress(main, _getAddressSalt(ctoken, expiry, instance_type), main);
     }
}
