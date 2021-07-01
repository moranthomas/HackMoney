#!/usr/bin/env python
import common
import sys
import json
import web3
from decimal import Decimal
from pprint import pprint
from typing import Any, Mapping

RELATIVE_DEADLINE = 300

def xlate_attr_dict(x: Any) -> Mapping:
    if isinstance(x, web3.datastructures.AttributeDict) or isinstance(x, dict):
        return dict(
            (k, xlate_attr_dict(v))
            for k,v in x.items()
        )
    if isinstance(x, tuple):
        return tuple(map(xlate_attr_dict, x))
    if isinstance(x, list):
        return list(map(xlate_attr_dict, x))
    if isinstance(x, web3.types.HexBytes):
        return x.hex()
    return x

def dump_tx_receipt(x):
    try:
        y = xlate_attr_dict(x)
        del y['blockHash']
        del y['blockNumber']
        del y['transactionIndex']
        del y['contractAddress']
        del y['logs']
        del y['logsBloom']
        if y['cumulativeGasUsed'] == y['gasUsed']:
            del y['cumulativeGasUsed']
        print('{%s}' % (' '.join(f'{x!s}:{y!s}' for x,y in y.items()),))
    except Exception as exc:
        print(exc)
        print(x)
        raise

def dump_account_balances(accounts, tokens):
    for account in accounts:
        for token in tokens:
            if token is None:
                symbol = 'ETH'
                decimals = 18
                balance = WETH.to_dec(w3.eth.get_balance(account))
            else:
                symbol = token.symbol
                decimals = token.decimals
                balance = token.balanceOf(account)
            print('%s %-28s [%02d] %32s' % (account, symbol, decimals, balance,))

w3 = web3.Web3(web3.HTTPProvider())

CONTRACTS = common.abi.load_contracts(w3)
TOKENS = dict(
    (contract.address, common.token.Token(contract))
    for name, contract in CONTRACTS.items()
    if name.startswith('token-') or (
        name.startswith('compound-') and name != 'compound-comptroller'
    ))
UNISWAP = common.uniswap.Uniswap(
    router=CONTRACTS['uniswap-v2-router'],
    factory=CONTRACTS['uniswap-v2-factory'],
    tokens=TOKENS,
)
WETH = TOKENS[CONTRACTS['token-weth'].address]
USDC = TOKENS[CONTRACTS['token-usdc'].address]
CUSDC = TOKENS[CONTRACTS['compound-cusdc'].address]
FUT = common.abi.load_deployed_FutureToken(w3)

A = w3.eth.accounts[1]

print(f'Ethereum block: {w3.eth.block_number}')
print()

if 1:
    EXPIRY = FUT.functions.calcNextExpiryAfter(512).call()
    cls = FUT.functions.getExpiryClassLongShort(CUSDC.address, EXPIRY).call()
    cls_check = tuple(any(web3.main.to_bytes(hexstr=text)) for text in cls)
    if not any(cls_check):
        tx_hash = FUT.functions.getOrCreateExpiryClassLongShort(CUSDC.address, EXPIRY).transact({'from': A})
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        dump_tx_receipt(receipt)
        cls = FUT.functions.getExpiryClassLongShort(CUSDC.address, EXPIRY).call()
        cls_check = tuple(any(web3.main.to_bytes(hexstr=text)) for text in cls)
    assert all(cls_check)
    FUT_C, FUT_L, FUT_S = (w3.eth.contract(address=address, abi=FUT.abi) for address in cls)
    if FUT_L.address in TOKENS:
        FUTL = TOKENS[FUT_L.address]
    else:
        FUTL = TOKENS[FUT_L.address] = common.token.Token(FUT_L)
    if FUT_S.address in TOKENS:
        FUTS = TOKENS[FUT_S.address]
    else:
        FUTS = TOKENS[FUT_S.address] = common.token.Token(FUT_S)

if 1:
    FUTL_CUSDC = UNISWAP.getOrCreatePair(FUTL, CUSDC, tx_from=A, transact=True)
    FUTS_CUSDC = UNISWAP.getOrCreatePair(FUTS, CUSDC, tx_from=A, transact=True)
    FUTL_FUTS = UNISWAP.getOrCreatePair(FUTL, FUTS, tx_from=A, transact=True)
    dump_account_balances((A,), (None, WETH, USDC, CUSDC, FUTL, FUTS, FUTL_CUSDC, FUTS_CUSDC, FUTL_FUTS))
    print()

    balance = CUSDC.balanceOf(A)
    if balance < 10_000:
        receipt = UNISWAP.swapETHForExactTokens(10_000 - balance, Decimal('0.25'), [WETH, CUSDC], tx_from=A, relative_deadline=RELATIVE_DEADLINE, transact=True)
        dump_tx_receipt(receipt)
    dump_account_balances((A,), (None, WETH, USDC, CUSDC, FUTL, FUTS, FUTL_CUSDC, FUTS_CUSDC, FUTL_FUTS))
    print()

    balance = min(FUTL.balanceOf(A), FUTS.balanceOf(A))
    if balance < 100_000:
        amount = (100_000 - balance) / 40
        CUSDC.approve(FUT_C.address, amount, tx_from=A, transact=True)
        tx_hash = FUT_C.functions.supply(CUSDC.to_int(amount)).transact({'from': A})
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        dump_tx_receipt(receipt)
    dump_account_balances((A,), (None, WETH, USDC, CUSDC, FUTL, FUTS, FUTL_CUSDC, FUTS_CUSDC, FUTL_FUTS))
    print()

    balance = FUTL_FUTS.balanceOf(A)
    if balance <= 0:
        amount = min(FUTL.balanceOf(A), FUTS.balanceOf(A))
        amount /= 2
        receipt = UNISWAP.addLiquidity(FUTL, FUTS, amount, amount, amount, amount, tx_from=A, relative_deadline=RELATIVE_DEADLINE, approve=True, transact=True)
        dump_tx_receipt(receipt)
    dump_account_balances((A,), (None, WETH, USDC, CUSDC, FUTL, FUTS, FUTL_CUSDC, FUTS_CUSDC, FUTL_FUTS))
    print()

    balance = FUTL_CUSDC.balanceOf(A)
    if balance <= 0:
        amount = FUTL.balanceOf(A)
        amount_cusdc = amount * Decimal('0.0005')
        receipt = UNISWAP.addLiquidity(FUTL, CUSDC, amount, amount_cusdc, amount, amount_cusdc, tx_from=A, relative_deadline=RELATIVE_DEADLINE, approve=True, transact=True)
        dump_tx_receipt(receipt)
    dump_account_balances((A,), (None, WETH, USDC, CUSDC, FUTL, FUTS, FUTL_CUSDC, FUTS_CUSDC, FUTL_FUTS))
    print()

    balance = FUTS_CUSDC.balanceOf(A)
    if balance <= 0:
        amount = FUTS.balanceOf(A)
        amount_cusdc = amount * Decimal('0.0005')
        receipt = UNISWAP.addLiquidity(FUTS, CUSDC, amount, amount_cusdc, amount, amount_cusdc, tx_from=A, relative_deadline=RELATIVE_DEADLINE, approve=True, transact=True)
        dump_tx_receipt(receipt)
    dump_account_balances((A,), (None, WETH, USDC, CUSDC, FUTL, FUTS, FUTL_CUSDC, FUTS_CUSDC, FUTL_FUTS))
    print()

    for pair in (FUTL_FUTS, FUTL_CUSDC, FUTS_CUSDC):
        balance0, balance1, liquidity = pair.getReserves()
        print('%s %-8s %-28s [%02d] %32s' % (A, pair.symbol, pair.token0.symbol, pair.token0.decimals, balance0,))
        print('%s %-8s %-28s [%02d] %32s' % (A, pair.symbol, pair.token1.symbol, pair.token1.decimals, balance1,))
        print('%s %-8s %-28s [%02d] %32s' % (A, pair.symbol, '', pair.decimals, liquidity,))
        print()

print(f'Ethereum block: {w3.eth.block_number}')
