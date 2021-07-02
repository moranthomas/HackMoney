# SPDX-License-Identifier: UNLICENSED
import sys
import json
import time
import lzma
import base64
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Tuple
import web3
from .token import Token

_ABI = dict(
    (k, json.loads(lzma.decompress(base64.b64decode(v))))
    for k, v in {
        'IUniswapV2Pair': '''
/Td6WFoAAATm1rRGAgAhARwAAAAQz1jM4BygAuddAC2ewEYTrpli4wX8vZ68M4cU8L7DOree15Te
wo664KUulwrmBrrjxKklWzXLVxxBh70PHSlhMa+WWTHneuVWkuEDdmbZsTE5IZOI62K0pgbpGQDy
blIwSUizppxOzal3+oi9LGGmK4wmxOzqUTSDVrCn+Az4yQ+RnhAZWQ0bzOE4//ooO0MuRo0rOnKc
koIqDoJJDTeDoOCZ4VRB2lXbvnY+opp6UT33QpHjlT7cbUr57kv5qbVRSsB27fJyAaQvPqYvE6YX
IJ7s/CcVP6pbdiFj/hmXqp2tDOqCKqDBGJiDcCyB9Rb7V64CQd7d4E/XAC5ca893lDLz73XRR4TU
ovUE1jZMTdsDtc6KOhi1bqplziDBK5UdXxdxfbjnFvcfrxcd7zypyQ0bAzNzEk+El56gIrJ6dmcH
/qGpM7NVlcaj/vo9VyJogcE8LHGsXPjP45U2unlfEFyog4uV12l3dX9zwCOFXrnB5DVCJEI31Dxj
rQ4jByQYu4nFtxaBnBF8NrXKaRepyWi2BluF7rO/S/o16IMiunNwccQJzUt7Y7TIjvOBSpuYPjY1
L8DJ1LQFXpBkJpzuvxdshS+a5rnfplGGdE8CVSwwmKhGuoxjj50GHpQ+zv9jRoO390JsFWWkGpRK
SXqT/9MKGoxl7RCldmZ9dxDkPZpjWTx1AJ+cYOdcblZTKmU1nN/48sdQKYRu/PzkW9wb0DG7IFdA
TGz2VyS8bV7UdD/Y0jDJ/lGjbFnK9lrMqdKmsnWmZEORFf3jh5jutIWm3Do8VYiLN7OMw3qLRDaf
nQxNU5bov+pCCiqTnsVZXPcWE5VQF3VvQhO1+QU9V1ZH9I8Y44VmktiAWpwoLjDgsv0Uh0eWVgkt
luRPrHfFI0cYnheRd8+sBa6gGNRU6fA+5NQycIfs8Kvqkx8PyEq3VfGRVsOuSQFG+CjANgociVFP
ZTj6JpO1k8uw8gWeD9P8TtHuwDqfY6MQcEZYJP1hvQAAAAAl0pBXmKWlygABgwahOQAAdOdcCrHE
Z/sCAAAAAARZWg==
''',
        'IERC20': '''
/Td6WFoAAATm1rRGAgAhARwAAAAQz1jM4AlyAU9dAC2ewEYTrpli4wX8vZ68M4cU8L7DOree15Te
wo664KUulwrmBrrjxKklWzXLVxxBh70PHSlhMa+WWTHneuVWkuEDdmbZsTE5IZOI62K0pgbpGQDy
blIwSUizppxOzal3+oi9LGGmK4wmxOzqUTSDVrCn+Az4yQ+RnhAZWQ0bzOE4//ooKdT3dvBHgZs1
URT9A0sYTMG3V7kvU3oLiLxZtG8cQaZ+Bi5kpid4eQ5PLTl/o3qRK/Xo9zz27AWibABGxNHkqdmd
y+zhNCJMKMSxSg1ZlMmrgJTMRpyFOa3XhPOyx1wJEznO84NW436qzudDcDgzu3BhI/KQ5PgQadVj
YqU/tTm6MW+Jp/AdELheaTTROIC97U7WDqemq/L4ncGuMt2kmWHwh42jtyaFy6Sw8zug2UGrjh0O
APpkKpqrCkQl6gQHxNmdQwUuJS7DICQAAACWH8Bla/tjYAAB6wLzEgAAq6JnTrHEZ/sCAAAAAARZ
Wg==
''',
    }.items())

_ABI_IUniswapV2Pair = _ABI['IUniswapV2Pair']
_ABI_IERC20 = _ABI['IERC20']

class UniswapToken(Token):
    def __init__(self, contract: web3.contract.Contract, tokens: Optional[Mapping[str, Token]] = None):
        super().__init__(contract)
        self.__token0 = None
        self.__token1 = None
        self.__tokens = tokens

    @property
    def token0(self) -> Token:
        if self.__token0 is None:
            address = self.contract.functions.token0().call()
            if self.__tokens:
                self.__token0 = self.__tokens[address]
            else:
                self.__token0 = Token(self.contract.web3.eth.contract(address=address, abi=_ABI_IERC20))
        return self.__token0

    @property
    def token1(self) -> Token:
        if self.__token1 is None:
            address = self.contract.functions.token1().call()
            if self.__tokens:
                self.__token1 = self.__tokens[address]
            else:
                self.__token1 = Token(self.contract.web3.eth.contract(address=address, abi=_ABI_IERC20))
        return self.__token1

    def getReserves(self) -> Tuple[Decimal, Decimal, Decimal]:
        raw_amount0, raw_amount1, raw_liquidity = self.contract.functions.getReserves().call()
        amount0 = self.token0.to_dec(raw_amount0)
        amount1 = self.token1.to_dec(raw_amount1)
        liquidity = self.to_dec(raw_liquidity)
        return amount0, amount1, liquidity

class Uniswap:
    def __init__(self,
                 factory: Optional[web3.contract.Contract],
                 router: Optional[web3.contract.Contract],
                 tokens: Optional[Mapping[str, Token]] = {}):
        self.__factory = factory
        self.__router = router
        self.__tokens = tokens
        self.__weth = None
        self.__factory_checked = False
        self.__uniswap_token_cache = {}

    def to_int(self, amount: Decimal) -> int:
        assert amount == amount.quantize(self.quantum)
        return int(amount * self.multiplier)

    def to_dec(self, amount: int) -> Decimal:
        return Decimal(amount) * self.quantum

    @property
    def router(self) -> web3.contract.Contract:
        return self.__router

    @property
    def factory(self) -> web3.contract.Contract:
        if not self.__factory_checked:
            factory_address = self.__router.functions.factory().call()
            if factory_address != self.__factory.address:
                raise ValueError('router/factory mismatch')
            self.__factory_checked = True
        return self.__factory

    @property
    def weth(self) -> str:
        if self.__weth is None:
            self.__weth = self.WETH()
        return self.__weth

    def calcPairAddress(self, address0: str, address1: str) -> str:
        data0 = web3.main.to_bytes(hexstr=address0)
        data1 = web3.main.to_bytes(hexstr=address1)
        if data1 < data0:
            data0, data1 = data1, data0
        data = (
            b'\xff' +
            web3.main.to_bytes(hexstr=self.factory.address) +
            web3.main.eth_utils_keccak(data0 + data1) +
            web3.main.to_bytes(hexstr='0x96e8ac4277198ff8b6f785478aa9a39f403cb768dd02cbee326c3e7da348845f')
        )
        data = web3.main.eth_utils_keccak(data)
        data = web3.main.to_hex(data[12:])
        data = web3.main.to_checksum_address(data)
        return data

#    def getPair(self, tokenA: Token, tokenB: Token) -> web3.contract.Contract:
    def getPairUnchecked(self, tokenA: Token, tokenB: Token) -> UniswapToken:
        address = self.calcPairAddress(tokenA.address, tokenB.address)
#        assert address == self.factory.functions.getPair(tokenA.address, tokenB.address).call()
        token = self.__uniswap_token_cache.get(address)
        if token is None:
            contract = self.factory.web3.eth.contract(address=address, abi=_ABI_IUniswapV2Pair)
            token = self.__uniswap_token_cache[address] = UniswapToken(contract, self.__tokens)
        return token

    def getPair(self, tokenA: Token, tokenB: Token) -> Optional[UniswapToken]:
        address = self.factory.functions.getPair(tokenA.address, tokenB.address).call()
        if any(web3.main.to_bytes(hexstr=address)):
            token = self.__uniswap_token_cache.get(address)
            if token is None:
                contract = self.factory.web3.eth.contract(address=address, abi=_ABI_IUniswapV2Pair)
                token = self.__uniswap_token_cache[address] = UniswapToken(contract, self.__tokens)
            return token
        else:
            return None

    def getPairChecked(self, tokenA: Token, tokenB: Token) -> UniswapToken:
        token = self.getPair(tokenA, tokenB)
        if not token:
            raise ValueError
        return token

    def getOrCreatePair(self, tokenA: Token, tokenB: Token, tx_from: Optional[str] = None, transact: bool = False, tx: Mapping = {}) -> UniswapToken:
        token = self.getPair(tokenA, tokenB)
        if not token:
            self.createPair(tokenA, tokenB, tx_from=tx_from, transact=transact, tx=tx)
            token = self.getPair(tokenA, tokenB)
            if not token:
                raise ValueError
        return token

    def createPair(self, tokenA: Token, tokenB: Token, tx_from: Optional[str] = None, transact: bool = False, tx: Mapping = {}) -> UniswapToken:
        tx_from, _ = self.__resolveTxFromTo(tx_from=tx_from, tx=tx)
        raw_tokenA = tokenA.address
        raw_tokenB = tokenB.address
        tx_dict = tx.copy(); tx_dict.update({'from': tx_from})
        function = self.factory.functions.createPair(raw_tokenA, raw_tokenB)
        if transact:
            tx_hash = function.transact(tx_dict)
            receipt = self.factory.web3.eth.get_transaction_receipt(tx_hash)
            return receipt
        else:
            address = function.call(tx_dict)
            return address

    def WETH(self) -> str:
        return self.__router.functions.WETH().call()

    def quote(self,
              tokenA: Token,
              tokenB: Token,
              amountA: Decimal,
              reserveA: Decimal,
              reserveB: Decimal) -> Decimal:
        raw_amountA = tokenA.to_int(amountA)
        raw_reserveA = tokenA.to_int(reserveA)
        raw_reserveB = tokenB.to_int(reserveB)
        function = self.__router.functions.quote(raw_amountA, raw_reserveA, raw_reserveB)
        raw_amountB = function.call()
        amountB = tokenB.to_dec(raw_amountB)
        return amountB

    def getAmountIn(self, amountOut: Decimal, reserveIn: Decimal, reserveOut: Decimal, tokenIn: Token, tokenOut: Token) -> Decimal:
        raw_amountOut = tokenOut.to_int(amountOut)
        raw_reserveIn = tokenIn.to_int(reserveIn)
        raw_reserveOut = tokenOut.to_int(reserveOut)
        function = self.__router.functions.getAmountIn(raw_amountOut, raw_reserveIn, raw_reserveOut)
        raw_amountIn = function.call()
        amountIn = tokenIn.to_dec(raw_amountIn)
        return amountIn

    def getAmountOut(self, amountIn: Decimal, reserveIn: Decimal, reserveOut: Decimal, tokenIn: Token, tokenOut: Token) -> Decimal:
        raw_amountIn = tokenIn.to_int(amountIn)
        raw_reserveIn = tokenIn.to_int(reserveIn)
        raw_reserveOut = tokenOut.to_int(reserveOut)
        function = self.__router.functions.getAmountOut(raw_amountIn, raw_reserveIn, raw_reserveOut)
        raw_amountOut = function.call()
        amountOut = tokenOut.to_dec(raw_amountOut)
        return amountOut

    def getAmountsIn(self, amountOut: Decimal, path: Sequence[Token]) -> Sequence[Decimal]:
        raw_amountOut = path[-1].to_int(amountOut)
        raw_path = [token.address for token in path]
        function = self.__router.functions.getAmountsIn(raw_amountOut, raw_path)
        raw_amounts = function.call()
        amounts = tuple(token.to_dec(raw_amount) for token, raw_amount in zip(path, raw_amounts))
        return amounts

    def getAmountsOut(self, amountIn: Decimal, path: Sequence[Token]) -> Sequence[Decimal]:
        raw_amountIn = path[0].to_int(amountIn)
        raw_path = [token.address for token in path]
        function = self.__router.functions.getAmountsOut(raw_amountIn, raw_path)
        raw_amounts = function.call()
        amounts = tuple(token.to_dec(raw_amount) for token, raw_amount in zip(path, raw_amounts))
        return amounts

    def swapETHForExactTokens(self,
                              amountOut: Decimal,
                              amountInMax: Decimal,
                              path: Sequence[Token],
                              to: Optional[str] = None,
                              absolute_deadline: Optional[int] = None,
                              tx_from: Optional[str] = None,
                              relative_deadline: Optional[int] = None,
                              transact: bool = False,
                              tx: Mapping = {}):
        assert path[0].address == self.weth
        assert path[0].decimals == 18
        deadline = self.__calcDeadline(absolute=absolute_deadline, relative=relative_deadline)
        tx_from, to = self.__resolveTxFromTo(tx_from=tx_from, to=to, tx=tx)
        raw_amountOut = path[-1].to_int(amountOut)
        raw_amountInMax = path[0].to_int(amountInMax)
        raw_path = [token.address for token in path]
        function = self.__router.functions.swapETHForExactTokens(raw_amountOut, raw_path, to, deadline)
        tx_dict = tx.copy(); tx_dict.update({'from': tx_from, 'value': raw_amountInMax})
        if transact:
            tx_hash = function.transact(tx_dict)
            receipt = self.__router.web3.eth.get_transaction_receipt(tx_hash)
            return receipt
        else:
            raw_amounts = function.call(tx_dict)
            amounts = tuple(token.to_dec(raw_amount) for token, raw_amount in zip(path, raw_amounts))
            return amounts

    def swapExactETHForTokens(self, *args, **kwargs):
        return self.__swapExactETHForTokens('swapExactETHForTokens', *args, **kwargs)

    def swapExactETHForTokensSupportingFeeOnTransferTokens(self, *args, **kwargs):
        return self.__swapExactETHForTokens('swapExactETHForTokensSupportingFeeOnTransferTokens', *args, **kwargs)

    def __swapExactETHForTokens(self,
                                method: str,
                                amountIn: Decimal,
                                amountOutMin: Decimal,
                                path: Sequence[Token],
                                to: Optional[str] = None,
                                absolute_deadline: Optional[int] = None,
                                tx_from: Optional[str] = None,
                                relative_deadline: Optional[int] = None,
                                transact: bool = False,
                                tx: Mapping = {}):
        assert path[0].address == self.weth
        assert path[0].decimals == 18
        deadline = self.__calcDeadline(absolute=absolute_deadline, relative=relative_deadline)
        tx_from, to = self.__resolveTxFromTo(tx_from=tx_from, to=to, tx=tx)
        raw_amountIn = path[0].to_int(amountIn)
        raw_amountOutMin = path[-1].to_int(amountOutMin)
        raw_path = [token.address for token in path]
        function = self.__router.get_function_by_name(method)
        function = function(raw_amountOutMin, raw_path, to, deadline)
        tx_dict = tx.copy(); tx_dict.update({'from': tx_from, 'value': raw_amountIn})
        if transact:
            tx_hash = function.transact(tx_dict)
            receipt = self.__router.web3.eth.get_transaction_receipt(tx_hash)
            return receipt
        else:
            raw_amounts = function.call(tx_dict)
            amounts = tuple(token.to_dec(raw_amount) for token, raw_amount in zip(path, raw_amounts))
            return amounts

    def swapExactTokensForETH(self, *args, **kwargs):
        return self.__swapExactTokensForSomething('swapExactTokensForETH', *args, **kwargs)

    def swapTokensForExactETH(self, *args, **kwargs):
        return self.__swapTokensForExactSomething('swapTokensForExactETH', *args, **kwargs)

    def swapExactTokensForTokens(self, *args, **kwargs):
        return self.__swapExactTokensForSomething('swapExactTokensForTokens', *args, **kwargs)

    def swapTokensForExactTokens(self, *args, **kwargs):
        return self.__swapTokensForExactSomething('swapTokensForExactTokens', *args, **kwargs)

    def swapExactTokensForETHSupportingFeeOnTransferTokens(self, *args, **kwargs):
        return self.__swapExactTokensForSomething('swapExactTokensForETHSupportingFeeOnTransferTokens', *args, **kwargs)

    def swapExactTokensForTokensSupportingFeeOnTransferTokens(self, *args, **kwargs):
        return self.__swapExactTokensForSomething('swapExactTokensForTokensSupportingFeeOnTransferTokens', *args, **kwargs)

    def __calcDeadline(self, absolute: Optional[int] = None, relative: Optional[int] = None) -> int:
        deadline = absolute
        if deadline is None:
            deadline = int(time.time())
        if relative:
            deadline += relative
        return deadline

    def __resolveTxFromTo(self,
                          tx_from: Optional[str] = None,
                          to: Optional[str] = None,
                          tx: Mapping = {}) -> Tuple[str, str]:
        if not tx_from:
            tx_from = tx.get('from')
        if not tx_from:
            tx_from = self.__router.web3.eth.default_account
        tx_from = web3.main.to_checksum_address(tx_from)
        if to:
            to = web3.main.to_checksum_address(to)
        else:
            to = tx_from
        return tx_from, to

    def __checkAndMaybeIncreaseAllowance(self,
                                         amount: Decimal,
                                         token: Token,
                                         tx_from: str,
                                         approve: bool = False,
                                         transact: bool = False,
                                         tx: Mapping = {}):
        if not approve:
            return
        allowance = token.allowance(tx_from, self.router.address)
        increase = amount - allowance
        if increase > 0:
            try:
                result = token.increaseAllowance(self.router.address, increase, tx_from=tx_from, transact=transact, tx=tx)
            except web3.exceptions.ABIFunctionNotFound:
                result = token.approve(self.router.address, amount, tx_from=tx_from, transact=transact, tx=tx)
            return result

    def __swapExactTokensForSomething(self,
                                      method: str,
                                      amountIn: Decimal,
                                      amountOutMin: Decimal,
                                      path: Sequence[Token],
                                      to: Optional[str] = None,
                                      absolute_deadline: Optional[int] = None,
                                      tx_from: Optional[str] = None,
                                      relative_deadline: Optional[int] = None,
                                      approve: bool = False,
                                      transact: bool = False,
                                      tx: Mapping = {}):
        deadline = self.__calcDeadline(absolute=absolute_deadline, relative=relative_deadline)
        tx_from, to = self.__resolveTxFromTo(tx_from=tx_from, to=to, tx=tx)
        self.__checkAndMaybeIncreaseAllowance(amountIn, path[0], tx_from, approve, transact, tx)
        raw_amountIn = path[0].to_int(amountIn)
        raw_amountOutMin = path[-1].to_int(amountOutMin)
        raw_path = [token.address for token in path]
        function = self.__router.get_function_by_name(method)
        function = function(raw_amountIn, raw_amountOutMin, raw_path, to, deadline)
        tx_dict = tx.copy(); tx_dict.update({'from': tx_from})
        if transact:
            tx_hash = function.transact(tx_dict)
            receipt = self.__router.web3.eth.get_transaction_receipt(tx_hash)
            return receipt
        else:
            raw_amounts = function.call(tx_dict)
            amounts = tuple(token.to_dec(raw_amount) for token, raw_amount in zip(path, raw_amounts))
            return amounts

    def __swapTokensForExactSomething(self,
                                      method: str,
                                      amountOut: Decimal,
                                      amountInMax: Decimal,
                                      path: Sequence[Token],
                                      to: Optional[str] = None,
                                      absolute_deadline: Optional[int] = None,
                                      tx_from: Optional[str] = None,
                                      relative_deadline: Optional[int] = None,
                                      approve: bool = False,
                                      transact: bool = False,
                                      tx: Mapping = {}):
        deadline = self.__calcDeadline(absolute=absolute_deadline, relative=relative_deadline)
        tx_from, to = self.__resolveTxFromTo(tx_from=tx_from, to=to, tx=tx)
        self.__checkAndMaybeIncreaseAllowance(amountInMax, path[0], tx_from, approve, transact, tx)
        raw_amountOut = path[-1].to_int(amountOut)
        raw_amountInMax = path[0].to_int(amountInMax)
        raw_path = [token.address for token in path]
        function = self.__router.get_function_by_name(method)
        function = function(raw_amountOut, raw_amountInMax, raw_path, to, deadline)
        tx_dict = tx.copy(); tx_dict.update({'from': tx_from})
        if transact:
            tx_hash = function.transact(tx_dict)
            receipt = self.__router.web3.eth.get_transaction_receipt(tx_hash)
            return receipt
        else:
            raw_amounts = function.call(tx_dict)
            amounts = tuple(token.to_dec(raw_amount) for token, raw_amount in zip(path, raw_amounts))
            return amounts

    def addLiquidity(self, *args, **kwargs) -> Tuple[Decimal, Decimal, Decimal]:
        return self.__addLiquidity('addLiquidity', *args, **kwargs)

    def addLiquidityETH(self,
                        tokenA: Token,
                        tokenB: Token,
                        amountADesired: Decimal,
                        amountBDesired: Decimal,
                        amountAMin: Decimal,
                        amountBMin: Decimal,
                        to: Optional[str] = None,
                        absolute_deadline: Optional[int] = None,
                        tx_from: Optional[str] = None,
                        relative_deadline: Optional[int] = None,
                        approve: bool = False,
                        transact: bool = False,
                        tx: Mapping = {}) -> Tuple[Decimal, Decimal, Decimal]:
        assert tokenB.address == self.weth
        assert tokenB.decimals == 18
        deadline = self.__calcDeadline(absolute=absolute_deadline, relative=relative_deadline)
        tx_from, to = self.__resolveTxFromTo(tx_from=tx_from, to=to, tx=tx)
        self.__checkAndMaybeIncreaseAllowance(amountADesired, tokenA, tx_from, approve, transact, tx)
        self.__checkAndMaybeIncreaseAllowance(amountBDesired, tokenB, tx_from, approve, transact, tx)
        raw_tokenA = tokenA.address
        raw_tokenB = tokenB.address
        raw_amountADesired = tokenA.to_int(amountADesired)
        raw_amountBDesired = tokenB.to_int(amountBDesired)
        raw_amountAMin = tokenA.to_int(amountAMin)
        raw_amountBMin = tokenB.to_int(amountBMin)
        function = self.__router.get_function_by_name('addLiquidityETH')
        function = function(raw_tokenA, raw_amountADesired, raw_amountAMin, raw_amountBMin, to, deadline)
        tx_dict = tx.copy(); tx_dict.update({'from': tx_from, 'value': raw_amountBDesired})
        if transact:
            tx_hash = function.transact(tx_dict)
            receipt = self.__router.web3.eth.get_transaction_receipt(tx_hash)
            return receipt
        else:
            raw_amountA, raw_amountB, raw_liquidity = function.call(tx_dict)
            tokenLP = self.getPair(tokenA, tokenB)
            amountA = tokenA.to_dec(raw_amountA)
            amountB = tokenB.to_dec(raw_amountB)
            liquidity = tokenLP.to_dec(raw_liquidity)
            return amountA, amountB, liquidity

    def __addLiquidity(self,
                       method: str,
                       tokenA: Token,
                       tokenB: Token,
                       amountADesired: Decimal,
                       amountBDesired: Decimal,
                       amountAMin: Decimal,
                       amountBMin: Decimal,
                       to: Optional[str] = None,
                       absolute_deadline: Optional[int] = None,
                       tx_from: Optional[str] = None,
                       relative_deadline: Optional[int] = None,
                       approve: bool = False,
                       transact: bool = False,
                       tx: Mapping = {}) -> Tuple[Decimal, Decimal, Decimal]:
        deadline = self.__calcDeadline(absolute=absolute_deadline, relative=relative_deadline)
        tx_from, to = self.__resolveTxFromTo(tx_from=tx_from, to=to, tx=tx)
        self.__checkAndMaybeIncreaseAllowance(amountADesired, tokenA, tx_from, approve, transact, tx)
        self.__checkAndMaybeIncreaseAllowance(amountBDesired, tokenB, tx_from, approve, transact, tx)
        raw_tokenA = tokenA.address
        raw_tokenB = tokenB.address
        raw_amountADesired = tokenA.to_int(amountADesired)
        raw_amountBDesired = tokenB.to_int(amountBDesired)
        raw_amountAMin = tokenA.to_int(amountAMin)
        raw_amountBMin = tokenB.to_int(amountBMin)
        function = self.__router.get_function_by_name(method)
        function = function(raw_tokenA, raw_tokenB,
                            raw_amountADesired, raw_amountBDesired,
                            raw_amountAMin, raw_amountBMin,
                            to, deadline)
        tx_dict = tx.copy(); tx_dict.update({'from': tx_from})
        if transact:
            tx_hash = function.transact(tx_dict)
            receipt = self.__router.web3.eth.get_transaction_receipt(tx_hash)
            return receipt
        else:
            raw_amountA, raw_amountB, raw_liquidity = function.call(tx_dict)
            tokenLP = self.getPair(tokenA, tokenB)
            amountA = tokenA.to_dec(raw_amountA)
            amountB = tokenB.to_dec(raw_amountB)
            liquidity = tokenLP.to_dec(raw_liquidity)
            return amountA, amountB, liquidity

    def removeLiquidity(self, *args, **kwargs) -> Tuple[Decimal, Decimal]:
        return self.__removeLiquidity(True, False, 'removeLiquidity', *args, **kwargs)

    def removeLiquidityETH(self, *args, **kwargs) -> Tuple[Decimal, Decimal]:
        return self.__removeLiquidityETH(False, 'removeLiquidityETH', *args, **kwargs)

    def removeLiquidityETHSupportingFeeOnTransferTokens(self, *args, **kwargs) -> Tuple[Decimal, Decimal]:
        return self.__removeLiquidityETH(False, 'removeLiquidityETHSupportingFeeOnTransferTokens', *args, **kwargs)

    def removeLiquidityWithPermit(self, *args, **kwargs) -> Tuple[Decimal, Decimal]:
        return self.__removeLiquidity(True, True, 'removeLiquidityWithPermit', *args, **kwargs)

    def removeLiquidityETHWithPermit(self, *args, **kwargs) -> Tuple[Decimal, Decimal]:
        return self.__removeLiquidityETH(True, 'removeLiquidityETHWithPermit', *args, **kwargs)

    def removeLiquidityETHWithPermitSupportingFeeOnTransferTokens(self, *args, **kwargs) -> Tuple[Decimal, Decimal]:
        return self.__removeLiquidityETH(True, 'removeLiquidityETHWithPermitSupportingFeeOnTransferTokens', *args, **kwargs)

    def __removeLiquidityETH(self, with_avrs: bool, method: str, *args, **kwargs) -> Tuple[Decimal, Decimal]:
        try:
            tokenB = args[1]
        except IndexError:
            tokenB = kwargs['tokenB']
        assert tokenB.address == self.weth
        assert tokenB.decimals == 18
        return self.__removeLiquidity(False, with_avrs, method, *args, **kwargs)

    def __removeLiquidity(self,
                          with_token_b: bool,
                          with_avrs: bool,
                          method: str,
                          tokenA: Token,
                          tokenB: Token,
                          liquidity: Decimal,
                          amountAMin: Decimal,
                          amountBMin: Decimal,
                          to: Optional[str] = None,
                          absolute_deadline: Optional[int] = None,
                          tx_from: Optional[str] = None,
                          relative_deadline: Optional[int] = None,
                          approve: bool = False,
                          transact: bool = False,
                          avrs: Optional[Tuple[Any, Any, Any, Any]] = (),
                          tx: Mapping = {}) -> Tuple[Decimal, Decimal, Decimal]:
        assert len(avrs) == 4 if with_avrs else not avrs
        deadline = self.__calcDeadline(absolute=absolute_deadline, relative=relative_deadline)
        tx_from, to = self.__resolveTxFromTo(tx_from=tx_from, to=to, tx=tx)
        tokenLP = self.getPair(tokenA, tokenB)
        self.__checkAndMaybeIncreaseAllowance(liquidity, tokenLP, tx_from, approve, transact, tx)
        raw_tokenA = tokenA.address
        raw_tokenB = tokenB.address
        raw_liquidity = tokenLP.to_int(liquidity)
        raw_amountAMin = tokenA.to_int(amountAMin)
        raw_amountBMin = tokenB.to_int(amountBMin)
        function = self.__router.get_function_by_name(method)
        function_arguments = raw_tokenA,
        if with_token_b:
            function_arguments += raw_tokenB,
        function_arguments += (
            raw_liquidity, raw_amountAMin, raw_amountBMin,
            to, deadline,
        )
        function_arguments += tuple(avrs)
        function = function(*function_arguments)
        print(function_arguments)
        tx_dict = tx.copy(); tx_dict.update({'from': tx_from})
        if transact:
            tx_hash = function.transact(tx_dict)
            receipt = self.__router.web3.eth.get_transaction_receipt(tx_hash)
            return receipt
        else:
            raw_amountA, raw_amountB = function.call(tx_dict)
            amountA = tokenA.to_dec(raw_amountA)
            amountB = tokenB.to_dec(raw_amountB)
            return amountA, amountB
"quote"
"removeLiquidityETHWithPermit"
"removeLiquidityETHWithPermitSupportingFeeOnTransferTokens"
"removeLiquidityWithPermit"

