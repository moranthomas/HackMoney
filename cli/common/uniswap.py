# SPDX-License-Identifier: UNLICENSED
import sys
import json
import time
from decimal import Decimal
from pathlib import Path
from typing import Mapping, Optional, Sequence
import web3
from .token import Token

class Uniswap:
    def __init__(self, contract: web3.contract.Contract):
        self.__contract = contract
        self.__factory = None
        self.__weth = None

    def to_int(self, amount: Decimal) -> int:
        assert amount == amount.quantize(self.quantum)
        return int(amount * self.multiplier)

    def to_dec(self, amount: int) -> Decimal:
        return Decimal(amount) * self.quantum

    @property
    def address(self) -> str:
        return self.__contract.address

    @property
    def weth(self) -> str:
        if self.__weth is None:
            self.__weth = self.WETH()
        return self.__weth

    def factory(self) -> str:
        if self.__factory is None:
            self.__factory = self.__contract.functions.factory().call()
        return self.__factory

    def WETH(self) -> str:
        return self.__contract.functions.WETH().call()

    def getAmountIn(self, amountOut: Decimal, reserveIn: Decimal, reserveOut: Decimal, tokenIn: Token, tokenOut: Token) -> Decimal:
        raw_amountOut = tokenOut.to_int(amountOut)
        raw_reserveIn = tokenIn.to_int(reserveIn)
        raw_reserveOut = tokenOut.to_int(reserveOut)
        function = self.__contract.functions.getAmountIn(raw_amountOut, raw_reserveIn, raw_reserveOut)
        raw_amountIn = function.call()
        amountIn = tokenIn.to_dec(raw_amountIn)
        return amountIn

    def getAmountOut(self, amountIn: Decimal, reserveIn: Decimal, reserveOut: Decimal, tokenIn: Token, tokenOut: Token) -> Decimal:
        raw_amountIn = tokenIn.to_int(amountIn)
        raw_reserveIn = tokenIn.to_int(reserveIn)
        raw_reserveOut = tokenOut.to_int(reserveOut)
        function = self.__contract.functions.getAmountOut(raw_amountIn, raw_reserveIn, raw_reserveOut)
        raw_amountOut = function.call()
        amountOut = tokenOut.to_dec(raw_amountOut)
        return amountOut

    def getAmountsIn(self, amountOut: Decimal, path: Sequence[Token]) -> Sequence[Decimal]:
        raw_amountOut = path[-1].to_int(amountOut)
        raw_path = [token.address for token in path]
        function = self.__contract.functions.getAmountsIn(raw_amountOut, raw_path)
        raw_amounts = function.call()
        amounts = tuple(token.to_dec(raw_amount) for token, raw_amount in zip(path, raw_amounts))
        return amounts

    def getAmountsOut(self, amountIn: Decimal, path: Sequence[Token]) -> Sequence[Decimal]:
        raw_amountIn = path[0].to_int(amountIn)
        raw_path = [token.address for token in path]
        function = self.__contract.functions.getAmountsOut(raw_amountIn, raw_path)
        raw_amounts = function.call()
        amounts = tuple(token.to_dec(raw_amount) for token, raw_amount in zip(path, raw_amounts))
        return amounts

    def swapETHForExactTokens(self,
                              amountOut: Decimal,
                              amountInMax: Decimal,
                              path: Sequence[Token],
                              to: Optional[str] = None,
                              deadline: Optional[int] = None,
                              tx_from: Optional[str] = None,
                              relative_deadline: Optional[int] = None,
                              transact: bool = False,
                              tx: Mapping = {}):
        assert path[0].address == self.weth
        assert path[0].decimals == 18
        assert deadline is None or relative_deadline is None
        tx_from = tx_from or tx.get('from') or self.__contract.web3.eth.default_account
        assert web3.main.is_address(tx_from), tx_from
        to = to or tx_from
        assert web3.main.is_address(to)
        if deadline is None:
            if relative_deadline is None:
                relative_deadline = 0
            deadline = int(time.time()) + relative_deadline
        raw_amountOut = path[-1].to_int(amountOut)
        raw_amountInMax = path[0].to_int(amountInMax)
        raw_path = [token.address for token in path]
        function = self.__contract.functions.swapETHForExactTokens(raw_amountOut, raw_path, to, deadline)
        tx_dict = tx.copy(); tx_dict.update({'from': tx_from, 'value': raw_amountInMax})
        if transact:
            tx_hash = function.transact(tx_dict)
            receipt = self.__contract.web3.eth.get_transaction_receipt(tx_hash)
            return receipt
        else:
            raw_amounts = function.call(tx_dict)
            amounts = tuple(token.to_dec(raw_amount) for token, raw_amount in zip(path, raw_amounts))
            return amounts

    def swapExactETHForTokens(self,
                              amountIn: Decimal,
                              amountOutMin: Decimal,
                              path: Sequence[Token],
                              to: Optional[str] = None,
                              deadline: Optional[int] = None,
                              tx_from: Optional[str] = None,
                              relative_deadline: Optional[int] = None,
                              transact: bool = False,
                              tx: Mapping = {}):
        assert path[0].address == self.weth
        assert path[0].decimals == 18
        assert deadline is None or relative_deadline is None
        tx_from = tx_from or tx.get('from') or self.__contract.web3.eth.default_account
        assert web3.main.is_address(tx_from), tx_from
        to = to or tx_from
        assert web3.main.is_address(to)
        if deadline is None:
            if relative_deadline is None:
                relative_deadline = 0
            deadline = int(time.time()) + relative_deadline
        raw_amountOutMin = path[-1].to_int(amountOutMin)
        raw_amountIn = path[0].to_int(amountIn)
        raw_path = [token.address for token in path]
        function = self.__contract.functions.swapExactETHForTokens(raw_amountOutMin, raw_path, to, deadline)
        tx_dict = tx.copy(); tx_dict.update({'from': tx_from, 'value': raw_amountIn})
        if transact:
            tx_hash = function.transact(tx_dict)
            receipt = self.__contract.web3.eth.get_transaction_receipt(tx_hash)
            return receipt
        else:
            raw_amounts = function.call(tx_dict)
            amounts = tuple(token.to_dec(raw_amount) for token, raw_amount in zip(path, raw_amounts))
            return amounts

    def swapTokensForExactETH(self,
                              amountOut: Decimal,
                              amountInMax: Decimal,
                              path: Sequence[Token],
                              to: Optional[str] = None,
                              deadline: Optional[int] = None,
                              tx_from: Optional[str] = None,
                              relative_deadline: Optional[int] = None,
                              approve: bool = False,
                              transact: bool = False,
                              tx: Mapping = {}):
        assert path[-1].address == self.weth
        assert path[-1].decimals == 18
        assert deadline is None or relative_deadline is None
        tx_from = tx_from or tx.get('from') or self.__contract.web3.eth.default_account
        assert web3.main.is_address(tx_from), tx_from
        to = to or tx_from
        assert web3.main.is_address(to)
        if deadline is None:
            if relative_deadline is None:
                relative_deadline = 0
            deadline = int(time.time()) + relative_deadline
        if transact and approve and path[0].allowance(tx_from, self.address) < amountInMax:
            path[0].increaseAllowance(self.address, amountInMax, tx_from=tx_from, transact=transact, tx=tx)
        raw_amountOut = path[-1].to_int(amountOut)
        raw_amountInMax = path[0].to_int(amountInMax)
        raw_path = [token.address for token in path]
        function = self.__contract.functions.swapTokensForExactETH(raw_amountOut, raw_amountInMax, raw_path, to, deadline)
        tx_dict = tx.copy(); tx_dict.update({'from': tx_from})
        if transact:
            tx_hash = function.transact(tx_dict)
            receipt = self.__contract.web3.eth.get_transaction_receipt(tx_hash)
            return receipt
        else:
            raw_amounts = function.call(tx_dict)
            amounts = tuple(token.to_dec(raw_amount) for token, raw_amount in zip(path, raw_amounts))
            return amounts

    def swapExactTokensForETH(self,
                              amountIn: Decimal,
                              amountOutMin: Decimal,
                              path: Sequence[Token],
                              to: Optional[str] = None,
                              deadline: Optional[int] = None,
                              tx_from: Optional[str] = None,
                              relative_deadline: Optional[int] = None,
                              approve: bool = False,
                              transact: bool = False,
                              tx: Mapping = {}):
        assert path[-1].address == self.weth
        assert path[-1].decimals == 18
        assert deadline is None or relative_deadline is None
        tx_from = tx_from or tx.get('from') or self.__contract.web3.eth.default_account
        assert web3.main.is_address(tx_from), tx_from
        to = to or tx_from
        assert web3.main.is_address(to)
        if deadline is None:
            if relative_deadline is None:
                relative_deadline = 0
            deadline = int(time.time()) + relative_deadline
        if transact and approve and path[0].allowance(tx_from, self.address) < amountIn:
            path[0].increaseAllowance(self.address, amountIn, tx_from=tx_from, transact=transact, tx=tx)
        raw_amountOutMin = path[-1].to_int(amountOutMin)
        raw_amountIn = path[0].to_int(amountIn)
        raw_path = [token.address for token in path]
        function = self.__contract.functions.swapExactTokensForETH(raw_amountIn, raw_amountOutMin, raw_path, to, deadline)
        tx_dict = tx.copy(); tx_dict.update({'from': tx_from})
        if transact:
            tx_hash = function.transact(tx_dict)
            receipt = self.__contract.web3.eth.get_transaction_receipt(tx_hash)
            return receipt
        else:
            raw_amounts = function.call(tx_dict)
            amounts = tuple(token.to_dec(raw_amount) for token, raw_amount in zip(path, raw_amounts))
            return amounts

"WETH"
"addLiquidity"
"addLiquidityETH"
"factory"
"getAmountIn"
"getAmountOut"
"getAmountsIn"
"getAmountsOut"
"quote"
"removeLiquidity"
"removeLiquidityETH"
"removeLiquidityETHSupportingFeeOnTransferTokens"
"removeLiquidityETHWithPermit"
"removeLiquidityETHWithPermitSupportingFeeOnTransferTokens"
"removeLiquidityWithPermit"
"swapETHForExactTokens"
"swapExactETHForTokens"
"swapExactETHForTokensSupportingFeeOnTransferTokens"
"swapExactTokensForETH"
"swapExactTokensForETHSupportingFeeOnTransferTokens"
"swapExactTokensForTokens"
"swapExactTokensForTokensSupportingFeeOnTransferTokens"
"swapTokensForExactETH"
"swapTokensForExactTokens"
