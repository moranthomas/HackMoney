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


def test_proxy_wallet_create(accounts, ProxyWallet, proxy_wallet, proxy_wallet_0, proxy_wallet_1):
    """
    Test if the storage variable can be changed.
    """

    assert not proxy_wallet.isClone()
    assert proxy_wallet.proxyAddress() == brownie.ZERO_ADDRESS
    assert proxy_wallet_0.isClone()
    assert proxy_wallet_0.proxyAddress() == proxy_wallet
    assert proxy_wallet_1.isClone()
    assert proxy_wallet_1.proxyAddress() == proxy_wallet

    assert proxy_wallet_0 == proxy_wallet.getClone({'from': accounts[0]})
    assert proxy_wallet_1 == proxy_wallet.getClone({'from': accounts[1]})
    with brownie.reverts():
        proxy_wallet.getClone({'from': accounts[2]})

    assert proxy_wallet_0 == proxy_wallet.getCloneOrNull({'from': accounts[0]})
    assert proxy_wallet_1 == proxy_wallet.getCloneOrNull({'from': accounts[1]})
    assert brownie.ZERO_ADDRESS == proxy_wallet.getCloneOrNull({'from': accounts[2]})

    with brownie.reverts():
        proxy_wallet_0.getClone({'from': accounts[0]})

    assert proxy_wallet_0.owner() == accounts[0]
    assert proxy_wallet_0.get() == 5

    with brownie.reverts():
        proxy_wallet.set(20, {'from': accounts[0]})

    with brownie.reverts():
        proxy_wallet_0.set(21, {'from': accounts[1]})
    assert proxy_wallet_0.get() == 5

    proxy_wallet_0.set(22, {'from': accounts[0]})
    assert proxy_wallet_0.get() == 22

    assert proxy_wallet_1.get() == 5
