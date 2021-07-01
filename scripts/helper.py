# SPDX-License-Identifier: UNLICENSED
import json
import decimal
from pathlib import Path
from typing import Mapping, Union
import brownie

def _get_interfaces_dir() -> Path:
    for project in brownie.project.main.get_loaded_projects():
        return project._path.joinpath(project._structure['interfaces'])

def load_mainnet_contract(name: str) -> brownie.Contract:
    interfaces_dir = _get_interfaces_dir()
    assert not any(c in name for c in '*?/\\')
    path, = interfaces_dir.glob(f'mainnet.0x*.{name}.abi')
    assert path.name.startswith('mainnet.0x')
    assert path.name.endswith('.abi')
    addr, name_from_path = path.name[8:-4].split('.', 1)
    assert name == name_from_path
    addr = brownie.convert.EthAddress(addr)
    with path.open() as fd:
        abi = json.load(fd)
    contract = brownie.Contract.from_abi(name=name, address=addr, abi=abi)
    return contract

def load_mainnet_contracts(*args) -> Mapping[str, brownie.Contract]:
    if args:
        return dict(
            (name, load_mainnet_contract(name))
            for name in args
        )
    results = {}
    interfaces_dir = _get_interfaces_dir()
    for path in interfaces_dir.glob(f'mainnet.0x*.*.abi'):
        assert path.name.startswith('mainnet.0x')
        assert path.name.endswith('.abi')
        addr, name = path.name[8:-4].split('.', 1)
        addr = brownie.convert.EthAddress(addr)
        with path.open() as fd:
            abi = json.load(fd)
        contract = brownie.Contract.from_abi(name=name, address=addr, abi=abi)
        results[name] = contract
    return results

def D(x: int, decimals: int = 0):
    '''Convert integer to scaled decimal'''
    y = decimal.Decimal(x)
    y /= 10**decimals
    return y

class Wrapper:
    def __init__(self):
        names = {
            'token-weth': '_weth',
            'token-usdc': '_usdc',
            'compound-cusdc': '_cusdc',
            'uniswap-v2-router': '_uni',
        }
        contracts = load_mainnet_contracts(*names)
        for name, attr in names.items():
            setattr(self, attr, contracts[name])
        self._decimals = {}
        self._symbol = {}

    @property
    def WETH(self) -> brownie.Contract:
        return self._weth

    @property
    def USDC(self) -> brownie.Contract:
        return self._usdc

    @property
    def cUSDC(self) -> brownie.Contract:
        return self._cusdc

    @property
    def UNI(self) -> brownie.Contract:
        return self._uni

    def decimals(self, contract: brownie.Contract) -> int:
        try:
            return self._decimals[contract]
        except KeyError:
            decimals = self._decimals[contract] = contract.decimals()
        return decimals

    def symbol(self, contract: brownie.Contract) -> str:
        try:
            return self._symbol[contract]
        except KeyError:
            symbol = self._symbol[contract] = contract.symbol()
        return symbol

    def balanceOf(self, contract: brownie.Contract, *args, **kwargs) -> str:
        return self.to_dec(contract, contract.balanceOf(*args, **kwargs))

    def to_int(self, contract: brownie.Contract, amount: Union[decimal.Decimal, brownie.Fixed]) -> int:
        return int(amount * 10**self.decimals(contract))

    def to_dec(self, contract: brownie.Contract, amount: int) -> decimal.Decimal:
        return decimal.Decimal(amount) / 10**self.decimals(contract)

def main():
    global CONTRACTS
    global WETH
    global USDC
    global CUSDC
    global UNISWAP
    CONTRACTS = load_mainnet_contracts()
    WETH = CONTRACTS['token-weth']
    USDC = CONTRACTS['token-usdc']
    CUSDC = CONTRACTS['compound-cusdc']
    UNISWAP = CONTRACTS['uniswap-v2-router']
