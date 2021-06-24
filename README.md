# HackMoney
HackMoney June-July 2021

## Checking out KP/one

```$ git checkout kp/one```

Install dependencies

```$ npm install```

This uses `brownie`. If you don't have brownie installed follow documentation [here](https://eth-brownie.readthedocs.io/en/stable/install.html).
Once `brownie` is installed you can change the config file `~/.brownie/network-config.yaml` to include your API key here by changing `$WEB3_INFURA_PROJECT_ID`.

```- name: Ethereum
    networks:
      - name: Mainnet (Infura)
        chainid: 1
        id: mainnet
        host: https://mainnet.infura.io/v3/$WEB3_INFURA_PROJECT_ID
        explorer: https://api.etherscan.io/api
```
If you have an Alchemy API, you can update it to 

```- name: Ethereum
    networks:
      - name: Mainnet (Alchemy)
        chainid: 1
        id: mainnet
        host: https://eth-mainnet.alchemyapi.io/v2/$YOUR_API_KEY
        explorer: https://api.etherscan.io/api
```

Then run

`$ brownie console --network mainnet-fork`

This creates a local fork of the mainnet.

You can deploy the `ProxyWallet` contract as the following and declare a contract object `p` that allows you to interact with methods within `p` in the command line.

`>>> p=ProxyWallet.deploy({'from':a[0]})`

You should see something like this

```Transaction sent: 0x3007b657b9f2f9d28209aa9a3318a042fa8d2c7f45f06870bc3ebe398086e744
  Gas price: 0.0 gwei   Gas limit: 12000000   Nonce: 0
  ProxyWallet.constructor confirmed - Block: 1   Gas used: 451186 (3.76%)
  ProxyWallet deployed at: 0xF104A50668c3b1026E8f9B0d9D404faF8E42e642
  
  >>> p
  <ProxyWallet Contract '0xF104A50668c3b1026E8f9B0d9D404faF8E42e642'>
```
To create a clone of each account, you can create a `ProxyWallet` contract object for the address returned by `getOrCreateClone`

`>>>p0=ProxyWallet.at(p.getOrCreateClone({'from':a[0]}).return_value)`

`p0.isClone()` should return true (whereas `p.isClone()` should return false)

You can also pull existing contracts like so by using the Compound Comptroller contract address`0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B` from etherscan api. 

`>>>comp = Contract.from_explorer('0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B')`

Create a cUSDC and cETH Contract object:

`>>>cusdc = Contract.from_explorer('0x39AA39c021dfbaE8faC545936693aC917d5E7563')`

`>>>ceth = Contract.from_explorer('0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5')`

and once that's done this will get you the underlying usdc contract  
`>>>usdc = Contract.from_explorer(cusdc.underlying())`
