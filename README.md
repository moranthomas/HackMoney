# Convexity Protocol

Convexity enables users to create fixed rate deposits and stable rate borrowing. Rather than creating an entirely new fixed rate money market, Convexity adds a tokenized interest rate derivative to floating rate money market positions such as Compound or AAVE to create a fixed or stable rate exposure. The leverage inherent in the interest rate derivative enables a much larger amount of stable rate borrow or fixed rate deposit demand to be satisfied with a smaller capital pool.

## How it works

There are two main modules within Convexity. They are `ProxyWalletClone.sol` and `FutureToken.sol`. 

### ProxyWalletClone.sol

The ProxyWallet is the user's gateway to interacting with Convexity. It contains a contract factory that will create a new proxy wallet for each user in a deterministic manner that is owned by the user. Only the user will be able to withdraw from their proxy wallet. 

#### deposit

For a fixed rate deposit, users will deposit funds to the proxy wallet and the proxy wallet will in turn supply to Compound and buy a Short cToken Future Token (SFT).

### FutureToken.sol

The `FutureToken.sol` contains the logic for creating new expiries and minting long and short future tokens.

#### cTokens

Convexity leverages Compound's cToken exchange rate mechanism to create fixed rate deposits and stable rate borrowing. When a user supplies assets they mint cTokens. The user is exposed to the exchange rate risk between the cToken and the asset they had supplied. The amount of underlying asset the user receives at redeem will be determined by the exchange rate at that time. Since the cToken exchange rate is a function of the supply rates in a given Compound market (barring any fatal bug or hack), the user is thus exposed to the fluctuations of the interest rate. In order to hedge this, the user can *sell* their cTokens forward at a fixed price and a fixed value date/time. This guarantees the user a fixed rate deposit.

#### cToken Futures

The difference between a forward and a future is in its standardization. By standardizing the expiry dates, Convexity creates a market for **cToken futures**. Our current implementation uses the Uniswap AMM infrastructure to provide liquidity in these instruments. In order to do so, we have tokensized the long and short future positions, which is discussed in more detail below.

#### getOrCreateExpiryClassLongShort - Future Class, Long, Short Tokens

The getOrCreateExpiryClassLongShort method creates 3 smart contracts:

- The FutureClass 
- LongFuture token (LFT)
- ShortFuture token (SFT)

For the Hackathon, a script is used to invoke `getOrCreateExpiryClassLongShort` and to provide liquidity to uniswap pair pools.
The Long and short future tokens names follow the convention: 

**CVX/ _underlyingAsset_ / _expiryInHexadecimal_ / _L_ for Long, _S_ for Short**

The CVX stands for Convexity. For example a cUSDC Long and short Future token that expires on block 12,746,752 will have the names

- **CVX/cUSDC/0x00c28000/L** for long
- **CVX/cUSDC/0x00c28000/S** for short

**Expiries** are currently limited to multiples of 4,096 blocks in block height. I.e. if the current block height is 12,744,514, the next possible expiry is 12,746,752.

#### How are these long and short tokens used?

When a user deposits USDC, that user's proxywallet contract will supply funds to Compound, minting cUSDC, and then using a portion of the cUSDC, will buy short future tokens (e.g. CVX/cUSDC/0x00c28000/S) from the uniswap amm pair that contains the short future tokens and cUSDC tokens. 

## Running the repo

This uses `brownie`. If you don't have brownie installed follow documentation [here](https://eth-brownie.readthedocs.io/en/stable/install.html).

### Setting up brownie - API key and `Chain_id`

Once `brownie` is installed, you will need to make at least 2 changes for this project. 

- Change the config file `~/.brownie/network-config.yaml` to include your API key here by changing `$WEB3_INFURA_PROJECT_ID`.
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
- Make sure the forked chain is running with a `chain_id` that is not 1. The `helper.py` script that deploys the `ProxyWallet` and `FutureToken` check that we accidentally do not deploy on mainnet. If you have not done so, include the line

`chain_id : 1337` 

under `cmd_settings` for Ganache-CLI (Mainnet fork).

### Helper Scripts

There are helper scripts to load the mainnet contracts to make it easier for development. You can call these scripts when you are launching a brownie development fork instance.

`$ brownie run --interactive --network mainnet-fork helper`

This creates a local fork of the mainnet and also runs the `helper.py` script that does the following:

- Deploy `ProxyWallet` and instantiate a contract object `PW`
- Deploy `FutureToken` and instantiate a contract object `FUT`
- Create contract object dictionary `CONTRACTS`
- Creates several contract objects such as `WETH, USDC, CUSDC, UNISWAP`. 
 
The `UNISWAP` contract object will reference the `uniswap-v2-router` contract.

Creating new contract objects within the brownie console are now easier. For example, creating a contract object to interact with cDAI can be done as the following:

`>>>CDAI = CONTRACTS['compound-cdai']`

The deployed address of the contracts in brownie version 1.14.6 is stored under `/client/src/artifacts/deployments/map.json`

### Creating Clones

To create a clone, you can create a `ProxyWallet` contract object for the address returned by `getOrCreateClone`

`>>> p0 = ProxyWallet.at(p.getOrCreateClone({'from':a[0]}).return_value)`

`p0.isClone()` should return true (whereas `PW.isClone()` should return false)

### Creating Contract Objects from Explorer

Within `brownie` you can also pull existing contracts like so by using the Compound Comptroller contract address`0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B` from etherscan api. This scrapes the abi and exposes the methods of the Contract objects, making them easier to interact with in CLI.

`>>>comp = Contract.from_explorer('0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B')`
