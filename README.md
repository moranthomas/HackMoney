# HackMoney
HackMoney June-July 2021

## Checking out KP/one

```$ git checkout kp/one```

Install dependencies

```$ npm install```

This uses `brownie`. If you don't have brownie installed follow documentation [here](https://eth-brownie.readthedocs.io/en/stable/install.html).

## Helper Scripts

There are helper scripts to load the mainnet contracts to make it easier for development.

`$ brownie run --interactive --network mainnet-fork helper`

This creates a local fork of the mainnet and also runs the `helper.py` script that creates a few contract objects, such as `WETH, USDC, CUSDC, UNISWAP`. The `UNISWAP` contract object will reference the `uniswap-v2-router` contract.

Creating new contract objects within the brownie console are now easier. For example, creating a contract object to interact with cDAI can be done as the following:

`>>>CDAI = CONTRACTS['compound-cdai']`

## Deploying `ProxyWallet` and `FutureContract`

You can deploy the `ProxyWallet` contract as the following and declare a contract object `p` that allows you to interact with methods in the command line.

`>>> p=ProxyWallet.deploy({'from':a[0]})`

Deploying `FutureContract` is done similarly.

`>>> ft = FutureContract.deploy({'from':a[0]})`

The deployed address of the contracts in brownie version 1.14.6 is stored under `/client/src/artifacts/deployments/map.json`

## Creating Clones

To create a clone, you can create a `ProxyWallet` contract object for the address returned by `getOrCreateClone`

`>>> p0 = ProxyWallet.at(p.getOrCreateClone({'from':a[0]}).return_value)`

`p0.isClone()` should return true (whereas `p.isClone()` should return false)

## Creating Contract Objects from Explorer

Within `brownie` you can also pull existing contracts like so by using the Compound Comptroller contract address`0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B` from etherscan api. This scrapes the abi and exposes the methods of the Contract objects, making them easier to interact with in CLI.

`>>>comp = Contract.from_explorer('0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B')`

Create a cUSDC and cETH Contract object:

`>>>cusdc = Contract.from_explorer('0x39AA39c021dfbaE8faC545936693aC917d5E7563')`

`>>>ceth = Contract.from_explorer('0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5')`

and once that's done this will get you the underlying usdc contract  
`>>>usdc = Contract.from_explorer(cusdc.underlying())`

Now, we can do things like :

```
>>> cusdc.totalSupply() / 10**cusdc.decimals()
133659923056.00108
>>> cusdc.totalBorrows() / 10**usdc.decimals()
1646513467.957993
```
And mint cETH like so

```
>>> ceth.mint({'from':a[0],'value':1*10**18})
Transaction sent: 0x46b140cfbb74bd7e2c9f58263b7cf1bf25e130a9c09980edc8831c81325a4ef5
  Gas price: 0.0 gwei   Gas limit: 12000000   Nonce: 3
  Transaction confirmed - Block: 12692881   Gas used: 164037 (1.37%)

<Transaction '0x46b140cfbb74bd7e2c9f58263b7cf1bf25e130a9c09980edc8831c81325a4ef5'> 
>>> ceth.balanceOf(a[0])
4988760262
```
