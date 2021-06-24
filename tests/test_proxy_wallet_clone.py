import brownie
from brownie.convert import to_address

def test_proxy_wallet_deploy(proxy_wallet):
    """
    Test if the contract is correctly deployed.
    """
    assert proxy_wallet.owner() == to_address(b'\xff'*20)
    assert proxy_wallet.get() == 5


def test_proxy_wallet_set(accounts, proxy_wallet):
    """
    Test if the storage variable can be changed.
    """
    assert proxy_wallet.get() == 5
    with brownie.reverts():
        proxy_wallet.set(20, {'from': accounts[0]})
    assert proxy_wallet.get() == 5


def test_proxy_wallet_create(accounts, proxy_wallet, ProxyWallet):
    """
    Test if the storage variable can be changed.
    """
    with brownie.reverts():
        clone_address = proxy_wallet.getClone({'from': accounts[0]})

    clone_address = proxy_wallet.getOrCreateClone({'from': accounts[0]}).return_value
    clone = ProxyWallet.at(clone_address)

    clone_address_2 = proxy_wallet.getClone({'from': accounts[0]})
    assert clone_address == clone_address_2

    assert clone.owner() == accounts[0]
    assert clone.get() == 5

    with brownie.reverts():
        clone.set(20, {'from': accounts[1]})
    assert clone.get() == 5

    clone.set(20, {'from': accounts[0]})
    assert clone.get() == 20
