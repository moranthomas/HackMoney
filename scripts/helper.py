# SPDX-License-Identifier: UNLICENSED
import os
import json
import decimal
import lzma
import base64
import itertools
from pathlib import Path
from typing import Any, Mapping, Union
import brownie

UINT256_MAX = (1<<256)-1

# Disable CDAI and/or CETH to speed up script
_ENABLE_CDAI = False
_ENABLE_CUSDC = True
_ENABLE_CETH = False

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

def _get_interfaces_dir() -> Path:
    for project in brownie.project.main.get_loaded_projects():
        return project._path.joinpath(project._structure['interfaces'])

def print_text_box(text: str, padding: int=1):
    inside_width = len(text) + 2*padding
    box = (
        f"╔{'═' * inside_width}╗",
        f"║{text:^{inside_width}}║",
        f"╚{'═' * inside_width}╝",
    )
    print('\n'.join(box))

def token_int_to_dec(amount: int, token: brownie.Contract) -> decimal.Decimal:
    decimals = token.decimals.call()
    assert 0 <= decimals <= 18
    quantum = decimal.Decimal((0, (1,), -decimals))
    return amount * quantum

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
        for suffix in ('', '-1', '-2', '-3'):
            new_name = f'{name}{suffix}'
            if new_name in results:
                continue
            results[new_name] = contract
            break
        else:
            assert False, f'duplicate name: {name}'
    return results

def create_uniswap_v2_pair_contract(name: str, address: Any) -> brownie.Contract:
    return brownie.Contract.from_abi(name=name, address=address, abi=_ABI_IUniswapV2Pair)

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
    from brownie import FutureToken, ProxyWallet, accounts, interface
    CONTRACTS = load_mainnet_contracts()
    WETH = CONTRACTS['token-weth']
    USDC = CONTRACTS['token-usdc']
    DAI = CONTRACTS['token-dai']
    CETH = CONTRACTS['compound-ceth']
    CUSDC = CONTRACTS['compound-cusdc']
    CDAI = CONTRACTS['compound-cdai']
    COMPTROLLER = CONTRACTS['compound-comptroller']
    UNISWAP = CONTRACTS['uniswap-v2-router']
    UNISWAP_FACTORY = CONTRACTS['uniswap-v2-factory']

    # Make sure we have the later version of DAI
    assert CDAI.address == '0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643'
    assert DAI.address == '0x6B175474E89094C44Da98b954EedeAC495271d0F'

    METAMASK_ACCOUNT = os.environ.get('METAMASK_PRIVATE_KEY')
    if METAMASK_ACCOUNT:
        print_text_box(f'ADDING METAMASK ACCOUNT {METAMASK_ACCOUNT}')
        METAMASK_ACCOUNT = accounts.add(METAMASK_ACCOUNT)

    network = brownie.network.main.show_active()
    CUSDC.exchangeRateCurrent({'from': accounts[0]}) #initialize the exchangeRateCurrent so that we don't get revert error
    if brownie.network.chain.id >= 1000 and (network == 'development' or network.find('fork') >= 0):
        print_text_box('DEPLOYING FUTURE TOKEN')
        FUT = FutureToken.deploy({'from': accounts[0]})
        print_text_box('DEPLOYING PROXY WALLET')
        PW = ProxyWallet.deploy(FUT, COMPTROLLER, UNISWAP, {'from': accounts[0]})
        if _ENABLE_CETH:
            print_text_box('PROXY WALLET: ADDING CETH')
            PW.addCEtherToken(CETH, {'from': accounts[0]})
        if _ENABLE_CUSDC:
            print_text_box('PROXY WALLET: ADDING CUSDC')
            PW.addCErc20Token(CUSDC, {'from': accounts[0]})
        if _ENABLE_CDAI:
            print_text_box('PROXY WALLET: ADDING CDAI')
            PW.addCErc20Token(CDAI, {'from': accounts[0]})

        # Create three proxy wallets for accounts 1 - 3
        print_text_box('CREATING PROXY WALLETS FOR ACCOUNTS 1 - 3')
        PW1 = ProxyWallet.at(PW.createWalletIfNeeded({'from': accounts[1]}).return_value)
        PW2 = ProxyWallet.at(PW.createWalletIfNeeded({'from': accounts[2]}).return_value)
        PW3 = ProxyWallet.at(PW.createWalletIfNeeded({'from': accounts[3]}).return_value)

        print_text_box('BUYING USDC FROM UNISWAP INTO ACCOUNTS 1 - 3')
        # Buy $10,000, $50,000, and $100,000 of USDC into accounts 1 - 3
        for acct, amount in zip(accounts[1:4], (10000, 50000, 100000)):
            raw_amount = amount * 10**USDC.decimals()
            raw_amount_eth = int(amount * 10**18 / 1000)
            deadline = brownie.chain.time() + 300
            UNISWAP.swapETHForExactTokens(raw_amount, [WETH, USDC], acct, deadline, {'from': acct, 'value': raw_amount_eth})

        # Determine next expiry at least 196,608 blocks away (48 chunks i.e. ~1 month) & create new future class, long and short
        EXP = FUT.calcNextExpiryBlockAfter(48*4096)
        if _ENABLE_CUSDC:
            print_text_box(f'CREATING CUSDC FUTURES FOR EXPIRY {EXP}')
            FCU, FLU, FSU = (
                FutureToken.at(addr)
                for addr in FUT.getOrCreateExpiryClassLongShort(
                                CUSDC,
                                EXP,
                                {'from': accounts[0]}).return_value)
        if _ENABLE_CETH:
            print_text_box(f'CREATING CDAI FUTURES FOR EXPIRY {EXP}')
            FCD, FLD, FSD = (
                FutureToken.at(addr)
                for addr in FUT.getOrCreateExpiryClassLongShort(
                                CDAI,
                                EXP,
                                {'from': accounts[0]}).return_value)
        if _ENABLE_CETH:
            print_text_box(f'CREATING CETH FUTURES FOR EXPIRY {EXP}')
            FCE, FLE, FSE = (
                FutureToken.at(addr)
                for addr in FUT.getOrCreateExpiryClassLongShort(
                                CETH,
                                EXP,
                                {'from': accounts[0]}).return_value)

        print_text_box(f'CREATING UNISWAP LIQUIDITY POOLS FOR FUTURES')
        # Create Uniswap long/short, long/ctoken, short/ctoken pools
        token_sets = []
        if _ENABLE_CETH: token_sets.append((FLE, FSE, CETH))
        if _ENABLE_CUSDC: token_sets.append((FLU, FSU, CUSDC))
        if _ENABLE_CDAI: token_sets.append((FLD, FSD, CDAI))
        for tok0, tok1 in itertools.chain.from_iterable(
            itertools.combinations(x, 2) for x in token_sets
        ):
            UNISWAP_FACTORY.createPair(tok0, tok1, {'from': accounts[0]})

        if _ENABLE_CETH:
            FLE_FSE = brownie.interface.IUniswapV2Pair(UNISWAP_FACTORY.getPair(FLE, FSE))
            FLE_CETH = brownie.interface.IUniswapV2Pair(UNISWAP_FACTORY.getPair(FLE, CETH))
            FSE_CETH = brownie.interface.IUniswapV2Pair(UNISWAP_FACTORY.getPair(FSE, CETH))

        if _ENABLE_CUSDC:
            FLU_FSU = brownie.interface.IUniswapV2Pair(UNISWAP_FACTORY.getPair(FLU, FSU))
            FLU_CUSDC = brownie.interface.IUniswapV2Pair(UNISWAP_FACTORY.getPair(FLU, CUSDC))
            FSU_CUSDC = brownie.interface.IUniswapV2Pair(UNISWAP_FACTORY.getPair(FSU, CUSDC))

        if _ENABLE_CDAI:
            FLD_FSD = brownie.interface.IUniswapV2Pair(UNISWAP_FACTORY.getPair(FLD, FSD))
            FLD_CDAI = brownie.interface.IUniswapV2Pair(UNISWAP_FACTORY.getPair(FLD, CDAI))
            FSD_CDAI = brownie.interface.IUniswapV2Pair(UNISWAP_FACTORY.getPair(FSD, CDAI))

        print_text_box('MAKING ACCOUNT 5 A USDC MINTER')
        # Make account 5 a USDC minter with a $1 billion limit
        USDC_MASTER_MINTER = USDC.masterMinter.call()
        USDC.configureMinter(accounts[5], 1_000_000_000_000000, {'from': USDC_MASTER_MINTER})

        print_text_box('FUNDING ACCOUNT 4 WITH NEWLY MINTED USDC')
        # Fund account 4 with newly minted $10 million of USDC
        USDC.mint(accounts[4], 10_000_000_000000, {'from': accounts[5]})

        if METAMASK_ACCOUNT:
            print_text_box(f'FUNDING METAMASK ACCOUNT {METAMASK_ACCOUNT}')
            accounts[5].transfer(METAMASK_ACCOUNT, 1_000*10**18)
            USDC.mint(METAMASK_ACCOUNT, 1_000_000_000000, {'from': accounts[5]})

            print_text_box(f'CREATING PROXY WALLET FOR METAMASK ACCOUNT {METAMASK_ACCOUNT}')
            PW_META = ProxyWallet.at(PW.createWalletIfNeeded({'from': METAMASK_ACCOUNT}).return_value)

            print_text_box(f'SETTING ALLOWANCES FOR METAMAST ACCOUNT {METAMASK_ACCOUNT}')
            USDC.approve(CUSDC, UINT256_MAX, {'from': METAMASK_ACCOUNT})
            USDC.approve(PW_META, UINT256_MAX, {'from': METAMASK_ACCOUNT})
            CUSDC.approve(PW_META, UINT256_MAX, {'from': METAMASK_ACCOUNT})
            CUSDC.approve(FCU, UINT256_MAX, {'from': METAMASK_ACCOUNT})
            CUSDC.approve(UNISWAP, UINT256_MAX, {'from': METAMASK_ACCOUNT})
            FLU.approve(UNISWAP, UINT256_MAX, {'from': METAMASK_ACCOUNT})
            FSU.approve(UNISWAP, UINT256_MAX, {'from': METAMASK_ACCOUNT})

        amount = 2_000_000_000000
        print_text_box(f'MINTING CUSDC FROM {token_int_to_dec(amount, USDC):,} USDC')
        txdict = {'from': accounts[4]}
        amount_cusdc = CUSDC.balanceOf(accounts[4])
        assert amount_cusdc == 0, "CUSDC balance of account should be zero"
        USDC.approve(CUSDC, amount, txdict)
        CUSDC.mint(amount, txdict)
        amount_cusdc = CUSDC.balanceOf(accounts[4])
        assert amount_cusdc > 0, "CUSDC balance of account should be greater than zero"
        amount_cusc_orig = amount_cusdc

        COL_FAC = decimal.Decimal(FCU.collateralFactor()) / 10**18
        amount_cusdc = amount_cusdc // 2 # use half rounded down for minting, remainder for liquidity provision
        amount_ftoken_pairs = int(amount_cusdc / COL_FAC) # note amount_cusdc already scaled; future tokens have same decimals as underlying ctokens
        print_text_box(f'MINTING {token_int_to_dec(amount_ftoken_pairs, FLU):,} LONG & SHORT FUTURE TOKENS FROM {token_int_to_dec(amount_cusdc, CUSDC):,} USDC FOR EXPIRY {EXP}')
        CUSDC.approve(FCU, amount_cusdc, txdict)
        FCU.mintPairs(amount_ftoken_pairs, amount_cusdc, txdict)
        amount_flu = FLU.balanceOf(accounts[4])
        amount_fsu = FSU.balanceOf(accounts[4])
        assert amount_flu == amount_ftoken_pairs, f'FLU balance: expected {amount_ftoken_pairs:,} actual {amount_fcl,}'
        assert amount_fsu == amount_ftoken_pairs, f'FSU balance: expected {amount_ftoken_pairs:,} actual {amount_fcs,}'

        amount_cusdc = amount_cusc_orig - amount_cusdc
        COL_LONG_SPLIT = decimal.Decimal('0.3')
        amount_cusdc_long = int(amount_cusdc * COL_LONG_SPLIT)
        amount_cusdc_short = amount_cusdc - amount_cusdc_long
        assert amount_cusdc_long >= 0
        assert amount_cusdc_short >= 0
        assert amount_cusdc_long + amount_cusdc_short == amount_cusdc

        print_text_box(f'ADDING FLU/CUSDC LIQUIDITY {token_int_to_dec(amount_flu, FLU):,} FLU + {token_int_to_dec(amount_cusdc_long, CUSDC):,} CUSDC FOR EXPIRY {EXP}')

        deadline = brownie.chain.time() + 300
        amount_flu_cusdc = FLU_CUSDC.balanceOf(accounts[4])
        amount_fsu_cusdc = FSU_CUSDC.balanceOf(accounts[4])
        assert amount_flu_cusdc == 0, "FLU/CUSDC balance of account should be zero"
        assert amount_fsu_cusdc == 0, "FSU/CUSDC balance of account should be zero"

        FLU.approve(UNISWAP, amount_flu, txdict)
        CUSDC.approve(UNISWAP, amount_cusdc_long, txdict)
        UNISWAP.addLiquidity(FLU, CUSDC,
                             amount_flu, amount_cusdc_long,
                             amount_flu, amount_cusdc_long,
                             accounts[4], deadline, txdict)
        amount_flu_cusdc = FLU_CUSDC.balanceOf(accounts[4])
        assert amount_flu_cusdc > 0, "FLU/CUSDC balance of account should be greater than zero"

        print_text_box(f'ADDING FSU/CUSDC LIQUIDITY {token_int_to_dec(amount_fsu, FSU):,} FSU + {token_int_to_dec(amount_cusdc_short, CUSDC):,} CUSDC FOR EXPIRY {EXP}')

        FSU.approve(UNISWAP, amount_fsu, txdict)
        CUSDC.approve(UNISWAP, amount_cusdc_short, txdict)
        UNISWAP.addLiquidity(FSU, CUSDC,
                             amount_fsu, amount_cusdc_short,
                             amount_fsu, amount_cusdc_short,
                             accounts[4], deadline, txdict)
        amount_fsu_cusdc = FSU_CUSDC.balanceOf(accounts[4])
        assert amount_fsu_cusdc > 0, "FSU/CUSDC balance of account should be greater than zero"
