// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.6;

import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/IERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/extensions/IERC20Metadata.sol";
import {Clones} from "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/proxy/Clones.sol";
import {Address} from "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/utils/Address.sol";
import {CTokenInterface} from "contracts/CTokenInterfaces.sol";

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
    CTokenInterface internal _class_ctoken;
    uint32 internal _class_create_block;
    uint32 internal _class_expiry_block;
    uint32 internal _class_settle_block;
    uint8 internal _class_ctoken_decimals;
    uint256 internal _class_create_price;
    uint256 internal _class_settle_price;
    //    uint256 internal _class_margin_ratio;
    FutureToken internal _class_series_short;
    FutureToken internal _class_series_long;
}

abstract contract FutureTokenSeriesData {
    FutureToken internal _series_class_owner;
    mapping(address => uint256) internal _series_balances;
    mapping(address => mapping(address => uint256)) internal _series_allowances;
    string internal _series_symbol;
    //    string internal _series_name;
    uint256 internal _series_totalSupply;
}

abstract contract FutureTokenBase is FutureTokenBaseData {
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    //    uint8 constant internal SERIES_DECIMALS = 18;
    uint256 constant internal SERIES_MARGIN_RATIO_DIVISOR = 1_000000_000000_000000;
    uint256 constant internal SERIES_MARGIN_RATIO_MULTIPLIER = 25000_000000_000000;
    uint8 constant internal SERIES_EXPIRY_BITS = 12;
    uint256 constant internal SERIES_EXPIRY_INTERVAL = 1 << SERIES_EXPIRY_BITS;
    uint256 constant internal POW_10_18 = 1_000_000_000_000_000_000;
    uint256 constant internal POW_10_18_MINUS_1 = POW_10_18 - 1;

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
    function _calcCollateralFactor(uint32 expiry_block, uint32 current_block) pure internal returns (uint256) {
	if (current_block >= expiry_block) return 0;
	uint256 interval_delta = 1 + ((expiry_block - 1) >> SERIES_EXPIRY_BITS) - (current_block >> SERIES_EXPIRY_BITS);
	//return interval_delta * 8 * 43 / 684375; // 8*43/684375 == 4096*258/2102400000 ~= 4,096 blocks * 25.8% / 2,102,400 blocks per year
	// 10**13 * 256 * 43 / 219 == 10**18 * (8*43/684375) == 10**18 * (4096*258/2102400000) ~= 10**18 * 4,096 blocks * 25.8% / 2,102,400 blocks per year
	return interval_delta * 10_000_000_000_000 * 256 * 43 / 219;
    }

    function collateralFactor() view external returns (uint256) {
	return _calcCollateralFactor(_class_expiry_block, _class_create_block);
    }

    function ctoken() external view /*onlyIfClass*/ returns (CTokenInterface) {	return _class_ctoken; }
    function ctokenDecimals() external view /*onlyIfClass*/ returns (uint8) { return _class_ctoken_decimals; }
    function seriesShort() external view /*onlyIfClass*/ returns (FutureToken) { return _class_series_short; }
    function seriesLong() external view /*onlyIfClass*/ returns (FutureToken) {	return _class_series_long; }
    function createBlock() external view /*onlyIfClass*/ returns (uint256) { return _class_create_block; }
    function expiryBlock() external view /*onlyIfClass*/ returns (uint256) { return _class_expiry_block; }
    function settleBlock() external view /*onlyIfClass*/ returns (uint256) { return _class_settle_block; }
    function isExpired() external view returns (bool) {	return _class_settle_block == 0; }
    function createPrice() external view /*onlyIfClass*/ returns (uint256) { return _class_create_price; }
    function settlePrice() external view /*onlyIfClass*/ returns (uint256) { return _class_settle_price; }

    function blocksToExpiry() external view /*onlyIfClass*/ returns (uint256) {
	if (block.number < _class_expiry_block)
	    return _class_expiry_block - block.number;
	return 0;
    }

    function calcExpiryBlock(uint256 blocks) public pure returns (uint256) {
	require(blocks < (1<<32)); // dev: block too big
	return (((blocks - 1) >> SERIES_EXPIRY_BITS) + 1) << SERIES_EXPIRY_BITS;
    }

    function calcNextExpiryBlockAfter(uint256 after_blocks) public view returns (uint256) {
	after_blocks += block.number;
	return calcExpiryBlock(after_blocks);
    }

    function expireClass() public onlyIfClass returns (bool) {
	require(block.number >= _class_expiry_block); // dev: class has not yet expired
	require(_class_settle_block == 0); // dev: class has already been expired
	_class_settle_block = uint32(block.number);
	_class_settle_price = _class_ctoken.exchangeRateCurrent();
	return true;
    }

    function mintPairs(uint256 mint_amount, uint256 collateral_limit) external returns (bool) {
	require(mint_amount > 0); // dev: amount must be non-zero
	uint256 factor = _calcCollateralFactor(_class_expiry_block, _class_create_block);
	uint256 collateral = (mint_amount * factor + POW_10_18_MINUS_1) / POW_10_18; // round up
	require(collateral <= collateral_limit); // dev: required collateral exceeds limit
	require(_class_ctoken.transferFrom(msg.sender, address(this), collateral)); // dev: inbound transfer of ctokens failed
	require(FutureToken(_class_series_short).mint(msg.sender, mint_amount)); // dev: minting short tokens failed
	require(FutureToken(_class_series_long).mint(msg.sender, mint_amount)); // dev: minting long tokens failed
	return true;
    }

    function redeemPairs(uint256 burn_amount) external returns (bool) {
	require(burn_amount > 0); // dev: amount must be non-zero
	uint256 factor = _calcCollateralFactor(_class_expiry_block, _class_create_block);
	uint256 collateral = burn_amount * factor / POW_10_18; // truncate
	require(_class_series_short.burn(msg.sender, burn_amount)); // dev: burning short tokens failed
	require(_class_series_long.burn(msg.sender, burn_amount)); // dev: burning long tokens failed
	require(_class_ctoken.transfer(msg.sender, collateral)); // dev: outbound transfer of ctokens failed
	return true;
    }
}

abstract contract FutureTokenSeries is
    IERC20,
    IERC20Metadata,
    FutureTokenClass,
    FutureTokenSeriesData
{
    modifier onlyClassOwner() {
        require(address(_series_class_owner) == msg.sender); // dev: FutureTokenSeries: caller is not the class owner
	_;
    }

    function classOwner() external view returns (FutureToken) { return _series_class_owner; }
    function name() external view override onlyIfSeries returns (string memory) { return _series_symbol; }
    function symbol() external view override onlyIfSeries returns (string memory) { return _series_symbol; }
    function decimals() public view override onlyIfSeries returns (uint8) { return _class_ctoken_decimals; }
    function totalSupply() external view override returns (uint256) { return _series_totalSupply; }

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

    function uint32ToHex(uint32 x) pure private returns (bytes8) {
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
 
     function initializeChild(CTokenInterface ctoken, uint8 decimals, uint32 expiry_block, InstanceType instance_type) external {
	 require(instance_type == InstanceType.Long
		 || instance_type == InstanceType.Short
		 || instance_type == InstanceType.Class); // dev: must be long, short or class
	 require(address(this) == _getAddress(msg.sender, ctoken, expiry_block, instance_type)); // dev: must be called by base
	 require(address(ctoken) != address(0)); // dev: ctoken must be non-zero
	 require(uint(expiry_block) >= block.number); // dev: expiry must not be in past
	 require(expiry_block == calcExpiryBlock(expiry_block)); // dev: expiry must be a valid expiry
	 require(_instance_type == InstanceType.None); // dev: instance type must be uninitialized
	 require(_owner == address(0)); // dev: owner must be uninitialized
	 require(_class_create_block == 0); // dev: class create block must be uninitialized
	 require(_class_expiry_block == 0); // dev: class expiry block must be uninitialized
	 require(_class_settle_block == 0); // dev: class expiry block must be uninitialized
	 require(_class_ctoken_decimals == 0); // dev: series decimal must be uninitialized
	 require(_class_create_price == 0); // dev: class create price must be uninitialized
	 require(_class_settle_price == 0); // dev: class settle price block must be uninitialized
	 require(address(_class_series_short) == address(0)); // dev: class series short must be uninitialized
	 require(address(_class_series_long) == address(0)); // dev: class series long must be uninitialized
	 require(address(_series_class_owner) == address(0)); // dev: series class owner must be uninitialized
	 require(_series_totalSupply == 0); // dev: series total supply must be uninitialized

	 _instance_type = instance_type;
	 _class_ctoken = ctoken;
	 _class_create_block = uint32(block.number);
	 _class_expiry_block = expiry_block;
	 if (instance_type == InstanceType.Class) {
	     _class_series_short = FutureToken(_getAddress(msg.sender, ctoken, expiry_block, InstanceType.Short));
	     _class_series_long = FutureToken(_getAddress(msg.sender, ctoken, expiry_block, InstanceType.Long));
	     _class_ctoken_decimals = decimals;
	     _class_create_price = ctoken.exchangeRateCurrent();
	 } else {
	     _class_ctoken_decimals = decimals;
	     _series_class_owner = FutureToken(_getAddress(msg.sender, ctoken, expiry_block, InstanceType.Class));
	     _series_symbol = string(abi.encodePacked("CVX/",
						      ctoken.symbol(),
						      "/0x",
						      uint32ToHex(expiry_block),
						      instance_type == InstanceType.Short ? "/S" :
						      instance_type == InstanceType.Long ? "/L" : "/X"));
	 }
     }

     function getExpiryClassLongShort(CTokenInterface ctoken, uint256 expiry) external view onlyIfBase returns (address, address, address) {
	 address addr_class = _getAddress(address(this), ctoken, expiry, InstanceType.Class);
	 address addr_long = _getAddress(address(this), ctoken, expiry, InstanceType.Long);
	 address addr_short = _getAddress(address(this), ctoken, expiry, InstanceType.Short);

	 if (!addr_class.isContract()) addr_class = address(0);
	 if (!addr_long.isContract()) addr_long = address(0);
	 if (!addr_short.isContract()) addr_short = address(0);

	 return (addr_class, addr_long, addr_short);
     }

     function getOrCreateExpiryClassLongShort(CTokenInterface ctoken, uint32 expiry_block) external onlyIfBase returns (address, address, address) {
	 require(address(ctoken) != address(0)); // dev: ctoken must be non-zero
	 require(uint(expiry_block) >= block.number); // dev: expiry must not be in past

	 uint8 ctoken_decimals = ctoken.decimals();
	 require(ctoken_decimals <= 18); // dev: ctokens with more than 18 decimals not supported

	 /*	 
    function supply(uint256 amount) external returns (bool) {
	require(amount > 0); // dev: amount must be non-zero
	require(_class_ctoken.transferFrom(msg.sender, address(this), amount)); // dev: inbound transfer of ctokens failed
	uint256 mint_amount = amount * 1000_000_000_000 * SERIES_MARGIN_RATIO_DIVISOR / SERIES_MARGIN_RATIO_MULTIPLIER;
	require(FutureToken(_class_series_short).mint(msg.sender, mint_amount)); // dev: minting short tokens failed
	require(FutureToken(_class_series_long).mint(msg.sender, mint_amount)); // dev: minting long tokens failed
    }
    */

	address addr_class = _getAddress(address(this), ctoken, expiry_block, InstanceType.Class);
	if (!addr_class.isContract()) {
	    require(addr_class == Clones.cloneDeterministic(address(this), _getAddressSalt(ctoken, expiry_block, InstanceType.Class))); // dev: clone created at unexpected address
	    FutureToken(addr_class).initializeChild(ctoken, ctoken_decimals, expiry_block, InstanceType.Class);
	}

	address addr_long = _getAddress(address(this), ctoken, expiry_block, InstanceType.Long);
	if (!addr_long.isContract()) {
	    require(addr_long == Clones.cloneDeterministic(address(this), _getAddressSalt(ctoken, expiry_block, InstanceType.Long))); // dev: clone created at unexpected address
	    FutureToken(addr_long).initializeChild(ctoken, ctoken_decimals, expiry_block, InstanceType.Long);
	}

	address addr_short = _getAddress(address(this), ctoken, expiry_block, InstanceType.Short);
	if (!addr_short.isContract()) {
	    require(addr_short == Clones.cloneDeterministic(address(this), _getAddressSalt(ctoken, expiry_block, InstanceType.Short))); // dev: clone created at unexpected address
	    FutureToken(addr_short).initializeChild(ctoken, ctoken_decimals, expiry_block, InstanceType.Short);
	}

	return (addr_class, addr_long, addr_short);
    }

    function _getAddressSalt(CTokenInterface ctoken, uint256 expiry_block, InstanceType instance_type) pure internal returns (bytes32) {
	return keccak256(abi.encodePacked(ctoken, expiry_block, uint8(instance_type)));
    }

    function _getAddress(address main, CTokenInterface ctoken, uint256 expiry_block, InstanceType instance_type) pure internal returns (address) {
	return Clones.predictDeterministicAddress(main, _getAddressSalt(ctoken, expiry_block, instance_type), main);
    }
}
