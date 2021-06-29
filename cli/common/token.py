# SPDX-License-Identifier: UNLICENSED
import sys
import json
from decimal import Decimal
from pathlib import Path
from typing import Mapping, Optional
import web3

class Token:
    def __init__(self, contract: web3.contract.Contract):
        self.__contract = contract
        self.__symbol = None
        self.__name = None
        self.__decimals = None
        self.__multiplier = None
        self.__quantum = None

    def to_int(self, amount: Decimal) -> int:
        if isinstance(amount, int):
            amount = Decimal(amount)
        assert isinstance(amount, Decimal), type(amount)
        assert amount == amount.quantize(self.quantum)
        return int(amount * self.multiplier)

    def to_dec(self, amount: int) -> Decimal:
        return Decimal(amount) * self.quantum

    @property
    def address(self) -> str:
        return self.__contract.address

    @property
    def symbol(self) -> str:
        if self.__symbol is None:
            self.__symbol = self.__contract.functions.symbol().call()
            if isinstance(self.__symbol, bytes):
                self.__symbol = self.__symbol.rstrip(b'\0').decode()
        return self.__symbol

    @property
    def name(self) -> str:
        if self.__name is None:
            self.__name = self.__contract.functions.name().call()
            if isinstance(self.__name, bytes):
                self.__name = self.__name.rstrip(b'\0').decode()
        return self.__name

    @property
    def decimals(self) -> str:
        if self.__decimals is None:
            self.__decimals = self.__contract.functions.decimals().call()
        return self.__decimals

    @property
    def multiplier(self) -> Decimal:
        if self.__multiplier is None:
            self.__multiplier = Decimal((0, (1,), self.decimals))
        return self.__multiplier

    @property
    def quantum(self) -> Decimal:
        if self.__quantum is None:
            self.__quantum = Decimal((0, (1,), -self.decimals))
        return self.__quantum

    def balanceOf(self, address: str) -> Decimal:
        assert web3.main.is_address(address), address
        function = self.__contract.functions.balanceOf(address)
        balance = function.call()
        return self.to_dec(balance)

    def allowance(self, owner: str, spender: str) -> Decimal:
        assert web3.main.is_address(owner), owner
        assert web3.main.is_address(spender), spender
        function = self.__contract.functions.allowance(owner, spender)
        allowance = function.call()
        return self.to_dec(allowance)

    def totalSupply(self) -> Decimal:
        function = self.__contract.functions.totalSupply()
        supply = function.call()
        return self.to_dec(supply)

    def approve(self, spender: str, value: Decimal, tx_from: Optional[str] = None, transact: bool = False, tx: Mapping = {}) -> bool:
        assert web3.main.is_address(spender), spender
        tx_from = tx_from or tx.get('from') or self.__contract.web3.eth.default_account
        assert web3.main.is_address(tx_from), tx_from
        raw_value = self.to_int(value)
        function = self.__contract.functions.approve(spender, raw_value)
        tx_dict = tx.copy(); tx_dict.update({'from': tx_from})
        if transact:
            tx_hash = function.transact(tx_dict)
            receipt = self.__contract.web3.eth.get_transaction_receipt(tx_hash)
            return receipt
        else:
            return function.call(tx_dict)

    def decreaseAllowance(self, spender: str, decrement: Decimal, tx_from: Optional[str] = None, transact: bool = False, tx: Mapping = {}) -> bool:
        assert web3.main.is_address(spender), spender
        tx_from = tx_from or tx.get('from') or self.__contract.web3.eth.default_account
        assert web3.main.is_address(tx_from), tx_from
        raw_decrement = self.to_int(decrement)
        function = self.__contract.functions.decreaseAllowance(spender, raw_decrement)
        tx_dict = tx.copy(); tx_dict.update({'from': tx_from})
        if transact:
            tx_hash = function.transact(tx_dict)
            receipt = self.__contract.web3.eth.get_transaction_receipt(tx_hash)
            return receipt
        else:
            return function.call(tx_dict)

    def increaseAllowance(self, spender: str, increment: Decimal, tx_from: Optional[str] = None, transact: bool = False, tx: Mapping = {}) -> bool:
        assert web3.main.is_address(spender), spender
        tx_from = tx_from or tx.get('from') or self.__contract.web3.eth.default_account
        assert web3.main.is_address(tx_from), tx_from
        raw_increment = self.to_int(increment)
        function = self.__contract.functions.increaseAllowance(spender, raw_increment)
        tx_dict = tx.copy(); tx_dict.update({'from': tx_from})
        if transact:
            tx_hash = function.transact(tx_dict)
            receipt = self.__contract.web3.eth.get_transaction_receipt(tx_hash)
            return receipt
        else:
            return function.call(tx_dict)

    def transfer(self, to: str, value: Decimal, tx_from: Optional[str] = None, transact: bool = False, tx: Mapping = {}) -> bool:
        assert web3.main.is_address(to), to
        assert tx_from is None or web3.main.is_address(tx_from), tx_from
        tx_from = tx_from or tx.get('from') or self.__contract.web3.eth.default_account
        assert web3.main.is_address(tx_from), tx_from
        raw_value = self.to_int(value)
        function = self.__contract.functions.transfer(to, raw_value)
        tx_dict = tx.copy(); tx_dict.update({'from': tx_from})
        if transact:
            tx_hash = function.transact(tx_dict)
            receipt = self.__contract.web3.eth.get_transaction_receipt(tx_hash)
            return receipt
        else:
            return function.call(tx_dict)

    def transferFrom(self, from_: str, to: str, value: Decimal, tx_from: Optional[str] = None, transact: bool = False, tx: Mapping = {}) -> bool:
        assert web3.main.is_address(from_), from_
        assert web3.main.is_address(to), to
        tx_from = tx_from or tx.get('from') or self.__contract.web3.eth.default_account
        assert web3.main.is_address(tx_from), tx_from
        raw_value = self.to_int(value)
        function = self.__contract.functions.transfer(to, raw_value)
        tx_dict = tx.copy(); tx_dict.update({'from': tx_from})
        if transact:
            tx_hash = function.transact(tx_dict)
            receipt = self.__contract.web3.eth.get_transaction_receipt(tx_hash)
            return receipt
        else:
            return function.call(tx_dict)
