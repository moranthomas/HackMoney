// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.6;

import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/IERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/extensions/IERC20Metadata.sol";
import {Clones} from "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/proxy/Clones.sol";
import {Address} from "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/utils/Address.sol";
import "contracts/CTokenInterfaces.sol";
import "contracts/ICErc20.sol";
import "contracts/ICEther.sol";
import "interfaces/ComptrollerInterface.sol";
import "interfaces/IWETH.sol";
import "interfaces/IUniswapV2Factory.sol";
import "interfaces/IUniswapV2Pair.sol";
import "interfaces/IUniswapV2Router02.sol";
import "interfaces/IUniswapV2Router02.sol";
import "contracts/FutureToken.sol";

address constant ETH_TOKEN_ADDRESS = address(0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE);

abstract contract ProxyWalletData {
    address internal _owner;
    address internal _proxy_wallet;

    function _initialize(address newOwner) internal {
	assembly { if gt(_owner.slot, 0) { revert(0, 0) } } // dev: owner slot is not zero
	require(_owner == address(0)); // dev: contract already initialized

	_owner = newOwner;
	_proxy_wallet = msg.sender;
    }
}

abstract contract ProxyWalletImpl is ProxyWalletData {
    event WalletAllocated(address indexed owner, address wallet);
    event WalletCreated(address indexed owner, address wallet);
    event WalletDestroyed(address indexed owner, address wallet);
    event WalletDeposit(
	address indexed _from,
	address indexed _deposit_token,
	address indexed _ctoken,
	uint _deposit_value,
	uint _ctoken_value,
	uint _rate_before,
	uint _rate_after
    );
    event WalletWithdraw(
	address indexed _to,
	address indexed _withdraw_token,
	address indexed _ctoken,
	uint _withdraw_value,
	uint _ctoken_value,
	uint _rate_before,
	uint _rate_after
    );
    event WalletShortHedge(
	address indexed _to,
	address indexed _hedge_token,
	address indexed _ctoken,
	uint _hedge_value,
	uint _ctoken_value,
	uint _rate_before,
	uint _rate_after
    );

    modifier onlyOwner() {
        require(_owner == msg.sender); // dev: Ownable: caller is not the owner
        _;
    }

    modifier onlyIfOriginal() {
        require(_proxy_wallet == address(0)); // dev: only callable on original contract
        _;
    }

    function owner() view public returns (address) { return _owner; }

    function isProxy() view public returns (bool result) {
	assembly {
	    result := iszero(eq(codesize(), extcodesize(address())))
	}
    }

    function extractProxyAddress() view public returns (address a) {
	assembly {
	    extcodecopy(address(), 0, 0, 32)
	    codecopy(32, 0, 32)
	    a := mload(0)
	    if eq(a, mload(32)) { a := 0 }
	    a := shr(16, a)
	}
    }
}

contract ProxyWallet is ProxyWalletImpl {
    using Clones for address;
    using Address for address;

    FutureToken internal _future_token;
    ComptrollerInterface _compound_comptroller;
    IUniswapV2Router02 internal _uniswap_router;

    mapping(address => CTokenInterface) internal _token_to_ctoken;
    ICEther internal _cether;

    constructor(FutureToken future_token,
		ComptrollerInterface compound_comptroller,
		IUniswapV2Router02 uniswap_router) {
	_owner = msg.sender;
	//_proxy_wallet = this;
	_future_token = future_token;
	_compound_comptroller = compound_comptroller;
	_uniswap_router = uniswap_router;

	// Code below moved to separate post construction functions due to gas limits
	/*
	address[] memory ctokens = compound_comptroller.getAllMarkets();
	uint num_ctokens = ctokens.length;
	for (uint i = 0; i < num_ctokens; ++i) {
	    address ctoken = ctokens[i];
	    _token_to_ctoken[ctoken] = CTokenInterface(ctoken);
	    ICErc20 ctoken_as_erc20 = ICErc20(ctoken);
	    try ctoken_as_erc20.underlying() returns (address underlying) {
		_token_to_ctoken[underlying] = CTokenInterface(ctoken);
	    } catch {
		// CEther doesn't have an underlying() method
		_token_to_ctoken[ETH_TOKEN_ADDRESS] = CTokenInterface(ctoken);
		_cether = ICEther(payable(ctoken));
	    }
	}
	*/
    }

    function addCEtherToken(ICEther cether) external onlyOwner onlyIfOriginal {
	require(address(cether) != address(0)); // dev: argument must be non-zero
	require(address(_cether) == address(0)); // dev: CEther already added
	_token_to_ctoken[address(cether)] = CTokenInterface(cether);
	_token_to_ctoken[ETH_TOKEN_ADDRESS] = CTokenInterface(cether);
	_cether = cether;
    }

    function addCErc20Token(ICErc20 ctoken) external onlyOwner onlyIfOriginal {
	require(address(ctoken) != address(0)); // dev: argument must be non-zero
	require(address(_token_to_ctoken[address(ctoken)]) == address(0)); // dev: CToken already added
	address underlying = ctoken.underlying();
	require(underlying != address(0)); // dev: missing underlying
	_token_to_ctoken[address(ctoken)] = ctoken;
	_token_to_ctoken[underlying] = ctoken;
    }

    struct PricingData {
	uint exchange_rate;
	uint expiry;
	uint reserves_fut_long;
	uint reserves_ctoken_long;
	uint reserves_fut_short;
	uint reserves_ctoken_short;
	uint32 timestamp_fut_ctoken_long;
	uint32 timestamp_fut_ctoken_short;
	address ctoken;
	address fut_class;
	address fut_long;
	address fut_short;
	address uni_fut_ctoken_long;
	address uni_fut_ctoken_short;
    }

    function getPricing(address token, uint blocks) external returns (PricingData memory x) {
	ProxyCommonData memory data = _getProxyCommonData(token);
	x.ctoken = address(data.ctoken);
	x.exchange_rate = data.ctoken.exchangeRateCurrent();
	x.expiry = data.future_token_master.calcExpiryBlock(blocks);
	(x.fut_class, x.fut_long, x.fut_short) = data.future_token_master.getExpiryClassLongShort(data.ctoken, x.expiry);
	if (x.fut_long != address(0)) {
	    x.uni_fut_ctoken_long = data.uniswap_factory.getPair(x.fut_long, x.ctoken);
	    if (x.uni_fut_ctoken_long != address(0)) {
		(x.reserves_fut_long, x.reserves_ctoken_long, x.timestamp_fut_ctoken_long) = IUniswapV2Pair(x.uni_fut_ctoken_long).getReserves();
		if (x.fut_long > x.ctoken) {
		    (x.reserves_fut_long, x.reserves_ctoken_long) = (x.reserves_ctoken_long, x.reserves_fut_long);
		}
	    }
	}
	if (x.fut_short != address(0)) {
	    x.uni_fut_ctoken_short = data.uniswap_factory.getPair(x.fut_short, x.ctoken);
	    if (x.uni_fut_ctoken_short != address(0)) {
		(x.reserves_fut_short, x.reserves_ctoken_short, x.timestamp_fut_ctoken_short) = IUniswapV2Pair(x.uni_fut_ctoken_short).getReserves();
		if (x.fut_short > x.ctoken) {
		    (x.reserves_fut_short, x.reserves_ctoken_short) = (x.reserves_ctoken_short, x.reserves_fut_short);
		}
	    }
	}
    }

    function getBalance(address token) view external returns (uint) {
	if (token == ETH_TOKEN_ADDRESS)
	    return address(this).balance;
	else
	    return IERC20(token).balanceOf(address(this));
    }

    struct BalanceData {
	uint balance_token;
	uint balance_ctoken;
	uint balance_future_long;
	uint balance_future_short;
	uint expiry;
	address token;
	address ctoken;
	address fut_class;
	address fut_long;
	address fut_short;
    }

    function getBalancesForTokenExpiry(address token, uint blocks) view external returns (BalanceData memory x) {
	ProxyCommonData memory data = _getProxyCommonData(token);
	x.expiry = data.future_token_master.calcExpiryBlock(blocks);
	if (data.ctoken == _cether) {
	    x.token = ETH_TOKEN_ADDRESS;
	    x.balance_token = address(this).balance;
	} else {
	    x.token = ICErc20(address(data.ctoken)).underlying();
	    x.balance_token = IERC20(token).balanceOf(address(this));
	}
	(x.fut_class, x.fut_long, x.fut_short) = data.future_token_master.getExpiryClassLongShort(data.ctoken, x.expiry);
	x.balance_future_long = FutureToken(x.fut_long).balanceOf(address(this));
	x.balance_future_short = FutureToken(x.fut_short).balanceOf(address(this));
    }

    function approveTokenForOwner(uint amount, IERC20 token) external onlyOwner returns (bool) {
	require(address(token) != address(0)); // dev: token must be non-zero
	require(token.approve(msg.sender, amount)); // dev: approve failed
	return true;
    }

    function transferEtherToOwner(uint amount) external onlyOwner returns (bool) {
	require(amount > 0); // dev: amount is zero
	(bool sent, bytes memory data) = msg.sender.call{value: amount}("");
	require(sent); // dev: failed to refund excess deposit amount
	return true;
    }

    function transferTokenToOwner(uint amount, IERC20 token) external onlyOwner returns (bool) {
	require(address(token) != address(0)); // dev: token must be non-zero
	require(token.transfer(msg.sender, amount)); // dev: token transfer failed
	return true;
    }

    function withdraw(uint amount, address token) external onlyOwner returns (bool) {
	ProxyCommonData memory data = _getProxyCommonData(token);
	CTokenInterface ctoken_intf = data.ctoken;

	if (token == ETH_TOKEN_ADDRESS || ctoken_intf == _cether)
	    return _withdraw_ether(amount, token, ICEther(payable(address(ctoken_intf))));

	return _withdraw_erc20(amount, IERC20(token), ICErc20(address(ctoken_intf)));
    }

    function _withdraw_ether(uint amount, address token, ICEther cether) internal returns (bool) {
	require(amount > 0); // dev: amount is zero

	uint balance_eth_before = address(this).balance;
	uint balance_ceth_before = cether.balanceOf(address(this));
	uint rate_before = cether.exchangeRateCurrent();
	{
	    uint rc = token == address(cether)
		? cether.redeem(amount)
		: cether.redeemUnderlying(amount);
	    if (rc != 0) {
		bytes memory text = "deposit:3:\x00";
		text[10] = bytes1(64 + (uint8(rc) & 0x1f));
		revert(string(text));
	    }
	}
	uint balance_eth_redeemed = address(this).balance - balance_eth_before;
	uint balance_ceth_redeemed = balance_ceth_before - cether.balanceOf(address(this));
	uint rate_after = cether.exchangeRateCurrent();
	require(balance_eth_redeemed > 0); // dev: nothing minted (eth)
	require(balance_ceth_redeemed > 0); // dev: nothing minted (ceth)

	(bool sent, bytes memory data) = msg.sender.call{value: balance_eth_redeemed}("");
	require(sent); // dev: failed to return withdrawn eth

	emit WalletWithdraw(msg.sender,
			    ETH_TOKEN_ADDRESS,
			    address(cether),
			    balance_eth_redeemed,
			    balance_ceth_redeemed,
			    rate_before,
			    rate_after);
	return true;
    }

    function _withdraw_erc20(uint amount, IERC20 token, ICErc20 ctoken) internal returns (bool) {
	require(amount > 0); // dev: amount is zero

	uint balance_token_before = token.balanceOf(address(this));
	uint balance_ctoken_before = ctoken.balanceOf(address(this));
	uint rate_before = ctoken.exchangeRateCurrent();
	{
	    uint rc = address(token) == address(ctoken)
		? ctoken.redeem(amount)
		: ctoken.redeemUnderlying(amount);
	    if (rc != 0) {
		bytes memory text = "deposit:3:\x00";
		text[10] = bytes1(64 + (uint8(rc) & 0x1f));
		revert(string(text));
	    }
	}
	uint balance_token_redeemed = token.balanceOf(address(this)) - balance_token_before;
	uint balance_ctoken_redeemed = balance_ctoken_before - ctoken.balanceOf(address(this));
	uint rate_after = ctoken.exchangeRateCurrent();
	require(balance_token_redeemed > 0); // dev: nothing minted (token)
	require(balance_ctoken_redeemed > 0); // dev: nothing minted (ctoken)

	require(token.transfer(msg.sender, balance_token_redeemed)); // dev: token transfer failed

	emit WalletWithdraw(msg.sender,
			    address(token),
			    address(ctoken),
			    balance_token_redeemed,
			    balance_ctoken_redeemed,
			    rate_before,
			    rate_after);
	return true;
    }

    function deposit(uint amount, address token) external payable onlyOwner returns (bool) {
	ProxyCommonData memory data = _getProxyCommonData(token);
	CTokenInterface ctoken_intf = data.ctoken;

	if (token == ETH_TOKEN_ADDRESS) {
	    assert(amount >= msg.value); // dev: supplied ether less than amount required
	    if (amount < msg.value) {
		uint refund = msg.value - amount;
		(bool sent, /*bytes memory data*/) = msg.sender.call{value: refund}("");
		require(sent); // dev: failed to refund excess deposit amount
	    }
	    ICEther cether = ICEther(payable(address(ctoken_intf)));
	    require(_deposit_ether(amount, cether) > 0); // dev: nothing minted
	    return true;
	}

	// for token deposits, refund any/all ETH sent
	if (msg.value > 0) {
	    (bool sent, /*bytes memory data*/) = msg.sender.call{value: msg.value}("");
	    require(sent); // dev: failed to refund excess deposit amount
	}

	address ctoken = address(ctoken_intf);
	if (token != ctoken)
	    require(_deposit_erc20(amount, IERC20(token), ICErc20(ctoken)) > 0); // dev: nothing minted
	else
	    require(_deposit_ctoken(amount, ICErc20(ctoken)) > 0); // dev: nothing minted
	return true;
    }

    function _deposit_ether(uint amount, ICEther cether) internal returns (uint) {
	require(amount > 0); // dev: amount is zero

	uint balance_before = cether.balanceOf(address(this));
	uint rate_before = cether.exchangeRateCurrent();
	cether.mint{value: amount}();
	uint balance_minted = cether.balanceOf(address(this)) - balance_before;
	uint rate_after = cether.exchangeRateCurrent();
	require(balance_minted > 0); // dev: nothing minted

	emit WalletDeposit(msg.sender, ETH_TOKEN_ADDRESS, address(cether), amount, balance_minted, rate_before, rate_after);
	return balance_minted;
    }

    function _deposit_erc20(uint amount, IERC20 token, ICErc20 ctoken) internal returns (uint) {
	require(amount > 0); // dev: amount is zero
	require(address(token) != address(ctoken)); // dev: token cannot be a ctoken

	require(token.transferFrom(msg.sender, address(this), amount)); // dev: token transfer failed
	require(token.approve(address(ctoken), amount)); //dev : approve ctoken failed
	uint balance_before = ctoken.balanceOf(address(this));
	uint rate_before = ctoken.exchangeRateCurrent();
	{
	    uint rc = ctoken.mint(amount);
	    if (rc != 0) {
		bytes memory text = "deposit:3:\x00";
		text[10] = bytes1(64 + (uint8(rc) & 0x1f));
		revert(string(text));
	    }
	}
	uint balance_minted = ctoken.balanceOf(address(this)) - balance_before;
	uint rate_after = ctoken.exchangeRateCurrent();
	require(balance_minted > 0); // dev: nothing minted

	emit WalletDeposit(msg.sender, address(token), address(ctoken), amount, balance_minted, rate_before, rate_after);
	return balance_minted;
    }

    function _deposit_ctoken(uint amount, ICErc20 ctoken) internal returns (uint) {
	require(amount > 0); // dev: amount is zero

	uint balance_before = ctoken.balanceOf(address(this));
	uint rate_before = ctoken.exchangeRateCurrent();
	require(ctoken.transferFrom(msg.sender, address(this), amount)); // dev: token transfer failed
	uint balance_minted = ctoken.balanceOf(address(this)) - balance_before;
	uint rate_after = ctoken.exchangeRateCurrent();
	require(balance_minted > 0); // dev: nothing minted

	emit WalletDeposit(msg.sender, address(ctoken), address(ctoken), amount, balance_minted, rate_before, rate_after);
	return balance_minted;
    }

    function depositAndHedge(uint amount, address token, uint blocks, uint max_slippage, uint deadline) external payable onlyOwner returns (bool) {
	ProxyCommonData memory data = _getProxyCommonData(token);

	uint balance_minted;
	if (token == ETH_TOKEN_ADDRESS) {
	    assert(amount >= msg.value); // dev: supplied ether less than amount required
	    if (amount < msg.value) {
		uint refund = msg.value - amount;
		(bool sent, /*bytes memory data*/) = msg.sender.call{value: msg.value}("");
		require(sent); // dev: failed to refund excess deposit amount
	    }
	    ICEther cether = ICEther(payable(address(data.ctoken)));
	    balance_minted = _deposit_ether(amount, cether);
	} else {
	    // for token deposits, refund any/all ETH sent
	    if (msg.value > 0) {
		(bool sent, /*bytes memory data*/) = msg.sender.call{value: msg.value}("");
		require(sent); // dev: failed to refund excess deposit amount
	    }

	    address ctoken = address(data.ctoken);
	    if (token != ctoken)
		balance_minted = _deposit_erc20(amount, IERC20(token), ICErc20(ctoken));
	    else
		balance_minted = _deposit_ctoken(amount, ICErc20(ctoken));
	}

	_hedge(balance_minted, blocks, max_slippage, deadline, data);
	return true;
    }

    /*
      @KP  To get the % price slippage limit from a yield slippage limit :

      User indicates that they are willing to tolerate a maximum of 5 basis point slippage in yield:

      ySlipLimit = 0.0005
      min = minExchangeRate
      cxr = currentExchangeRate
      tf = timeFactor = blocksToExpiry/BlocksInYear
      indic = indic SFT price from reserves

      pSlipLimit as a percentage = (ySlipLimit  * timeFactor * cxr ) / (min * indic)
    */

    //    function calcHedgePrice(uint hedge_amount, uint exchange_rate_current, uint ctoken_reserves, future_reserves, uint max_slippage) pure public returns (uint) {
    //    }

    function _hedge(uint amount, uint blocks, uint max_slippage, uint deadline, ProxyCommonData memory data) internal returns (uint amount_out, uint amount_in) {
	require(amount > 0); // dev: amount must be non-zero
	CTokenInterface ctoken = data.ctoken;

	address fut_short; {
	    uint expiry = data.future_token_master.calcExpiryBlock(blocks);
	    (,, fut_short) = data.future_token_master.getExpiryClassLongShort(ctoken, expiry);
	    require(fut_short != address(0)); // dev: no future for given expiry exists
	}

	uint amountInMax = amount; // slippage control not currently implemented
	address[] memory path = new address[](2); {
	    path[0] = address(ctoken);
	    path[1] = fut_short;
	}

	uint rate_before = ctoken.exchangeRateCurrent();

	require(ctoken.approve(address(data.uniswap_router), amountInMax)); // dev: set ctoken allowance for uniswap failed
	uint[] memory amounts = data.uniswap_router.swapTokensForExactTokens(amount, amountInMax, path, address(this), deadline);
	require(amounts.length == 2); // dev: unexpected number of amounts returned from uniswap.swapTokensForExactTokens

	amount_out = amounts[0];
	amount_in = amounts[1];

	if (amount_out < amountInMax)
	    require(ctoken.approve(address(data.uniswap_router), 0)); // dev: reset ctoken allowance for uniswap failed

	uint rate_after = ctoken.exchangeRateCurrent();

	emit WalletShortHedge(msg.sender,
			      fut_short,
			      address(ctoken),
			      amount_in,
			      amount_out,
			      rate_before,
			      rate_after);
    }

    struct ProxyCommonData {
	FutureToken future_token_master;
	IUniswapV2Router02 uniswap_router;
	IUniswapV2Factory uniswap_factory;
	CTokenInterface ctoken;
     }

    function _getProxyCommonData(address asset) view internal returns (ProxyCommonData memory) {
	address master_proxy_wallet = _proxy_wallet;
	if (master_proxy_wallet != address(0))
	    return ProxyWallet(payable(master_proxy_wallet)).getProxyCommonDataLocal(asset);
	return _getProxyCommonDataLocal(asset);
    }

    function _getProxyCommonDataLocal(address asset) view internal returns (ProxyCommonData memory x) {
	address factory = _uniswap_router.factory();
	address ctoken = address(_token_to_ctoken[asset]);
	require(ctoken != address(0)); // dev: asset not recognised
	x.future_token_master = _future_token;
	x.uniswap_router = _uniswap_router;
	x.uniswap_factory = IUniswapV2Factory(factory);
	x.ctoken = CTokenInterface(ctoken);
    }

    function getProxyCommonDataLocal(address asset) view external returns (ProxyCommonData memory ) {
        return _getProxyCommonDataLocal(asset);
    }

    fallback(bytes calldata /*_input*/) external payable returns (bytes memory /*_output*/) { revert(); } // dev: no fallback

    receive() external payable { revert(); } // dev: no receive

    function initializeWallet(address owner) external {
	require(Clones.predictDeterministicAddress(msg.sender,
						   bytes32(uint256(uint160(owner))),
						   msg.sender) == address(this)); // dev: must be called by deployer
	super._initialize(owner);
	emit WalletCreated(owner, address(this));
    }

    function getWalletAddress() view public returns (address) {
	return Clones.predictDeterministicAddress(address(this), bytes32(uint256(uint160(msg.sender))));
    }

    function getWalletOrNull() view external returns (ProxyWallet) {
	address addr = getWalletAddress();
	if (!addr.isContract()) addr = address(0);
	return ProxyWallet(payable(addr));
    }

    function getWallet() view external returns (ProxyWallet) {
	address addr = getWalletAddress();
	require(addr.isContract()); // dev: clone not created
	return ProxyWallet(payable(addr));
    }

    function destroyWallet() external {
	require(_owner == msg.sender); // dev: Ownable: caller is not the owner
	require(isProxy()); // dev: only proxies can be destroyed
	selfdestruct(payable(msg.sender));
	emit WalletCreated(msg.sender, address(this));
    }

    function createWalletIfNeeded() external returns (ProxyWallet) {
	address addr = getWalletAddress();
	if (!addr.isContract()) {
            require(!isProxy()); // dev: cannot create clone from clone
	    Clones.cloneDeterministic(address(this), bytes32(uint256(uint160(msg.sender))));
	    emit WalletAllocated(msg.sender, addr);
	    ProxyWallet(payable(addr)).initializeWallet(msg.sender);
	}
	return ProxyWallet(payable(addr));
    }
}
