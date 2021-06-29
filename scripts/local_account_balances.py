#!/usr/bin/env python3
'''
Iterates and print accounts on the Ethereum node.
For a local node (forked or otherwise) there should be 20 accounts with 10,000 ETH each.
'''
import decimal
import datetime
from decimal import Decimal
from typing import Any, Mapping, Optional, Sequence, Tuple, Union
from brownie import Contract, Fixed, accounts, chain
from .helper import D, Wrapper, load_mainnet_contracts

def main():
    W = Wrapper()

    block_number = chain.height

    print()
    print('# Ethereum')
    print(f'{"chain_id":<24} {chain.id}')
    print(f'{"block_number":<24} {chain.height:,d}')
    print(f'{"block_time":<24} {datetime.datetime.utcfromtimestamp(chain.time())!s:<19s} / {chain.time():,d}')
    print(f'{"accounts":<24} {len(accounts)}')
    print()
    for token in (W.WETH, W.USDC, W.cUSDC):
        print(f'{W.symbol(token):<24} {W.decimals(token):>3}    {token.address}')
    print()
    print(f'{"#":<2}    {"Account":<42}    {"ETH":>24}    {"WETH":>24}    {"USDC":>24}    {"cUSDC":>24}')
    for i, account in enumerate(accounts):
        eth_balance = account.balance()
        weth_balance = W.balanceOf(W.WETH, account)
        usdc_balance = W.balanceOf(W.USDC, account)
        cusdc_balance = W.balanceOf(W.cUSDC, account)
        print(f'{i:<2}    {account!s:<42s}    {D(eth_balance, 18):>24.18f}    {weth_balance:>24.18f}    {usdc_balance:>24.6f}    {cusdc_balance:>24.8f}')
    print()
