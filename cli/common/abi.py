# SPDX-License-Identifier: UNLICENSED
import sys
import json
from pathlib import Path
from typing import Iterable, Mapping, Optional
import web3

_SEARCH_PATH = Path(sys.path[0]) / '..' / 'interfaces'

def load_contracts(w3: web3.providers.base.BaseProvider, network: str = 'mainnet') -> Mapping[str, web3.contract.Contract]: 
    results = {}
    for path in _SEARCH_PATH.glob(f'{network}.0x*.*.abi'):
        assert path.name.startswith(f'{network}.0x')
        assert path.name.endswith('.abi')
        addr, name = path.name[len(network)+1:-4].split('.', 1)
        addr = web3.main.to_checksum_address(addr)
        with path.open() as fd:
            abi = json.load(fd)
        contract = w3.eth.contract(address=addr, abi=abi)
        results[name] = contract
    return results

def load_contract_by_name(w3: web3.providers.base.BaseProvider, name: str, network: str = 'mainnet') -> web3.contract.Contract:
    assert not any(c in name for c in '?/*\\')
    result = None
    for path in _SEARCH_PATH.glob(f'{network}.0x*.{name}.abi'):
        assert path.name.startswith(f'{network}.0x')
        assert path.name.endswith('.abi')
        addr, name_from_path = path.name[len(network)+1:-4].split('.', 1)
        assert name == name_from_path
        addr = web3.main.to_checksum_address(addr)
        with path.open() as fd:
            abi = json.load(fd)
        contract = w3.eth.contract(address=addr, abi=abi)
        assert result is None
        result = contract
    return result

def load_contracts_by_name(w3: web3.providers.base.BaseProvider, names: Optional[Iterable[str]] = None, network: str = 'mainnet') -> Mapping[str, web3.contract.Contract]: 
    if names is None:
        return load_contracts(w3, network)
    return dict((name, load_contract_by_name(w3, name=name, network=network)) for name in names)
