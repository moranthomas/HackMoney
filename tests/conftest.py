import pytest


@pytest.fixture(autouse=True)
def setup(fn_isolation):
    """
    Isolation setup fixture.
    This ensures that each test runs against the same base environment.
    """
    pass


@pytest.fixture(scope="module")
def vyper_storage(accounts, VyperStorage):
    """
    Yield a `Contract` object for the VyperStorage contract.
    """
    yield accounts[0].deploy(VyperStorage)


@pytest.fixture(scope="module")
def solidity_storage(accounts, SolidityStorage):
    """
    Yield a `Contract` object for the SolidityStorage contract.
    """
    yield accounts[0].deploy(SolidityStorage)


@pytest.fixture(scope="module")
def proxy_wallet(accounts, ProxyWallet):
    """
    Yield a `Contract` object for the ProxyWallet contract.
    """
    yield accounts[0].deploy(ProxyWallet)


@pytest.fixture(scope="module")
def proxy_wallet_0(accounts, ProxyWallet, proxy_wallet):
    """
    Yield a `Contract` object for the ProxyWallet contract.
    """
    yield ProxyWallet.at(proxy_wallet.getOrCreateClone({'from': accounts[0]}).return_value)


@pytest.fixture(scope="module")
def proxy_wallet_1(accounts, ProxyWallet, proxy_wallet):
    """
    Yield a `Contract` object for the ProxyWallet contract.
    """
    yield ProxyWallet.at(proxy_wallet.getOrCreateClone({'from': accounts[1]}).return_value)
