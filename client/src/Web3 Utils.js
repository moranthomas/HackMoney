/*jshint esversion: 6 */
const Web3 = require('web3');
const axios = require('axios');
const fs = require('fs');

let infuraUrl = "https://mainnet.infura.io/v3/53dbf207e63c42e99cacb63c2d41ec4f";
let ganacheUrl = "http://localhost:8545";
let web3Provider = new Web3.providers.HttpProvider(ganacheUrl);
let web3 = new Web3(web3Provider);

getGasPrice();

let devAccount = "0x08076ef44737edC609E1dDbb05cfe142cA1ceF17";
getAddressBalance(devAccount);

// These Uniswap deployment addresses are the same for mainnet, ropsten, rinkeby, goerli and kovan
UNIVERSAL_UNISWAP_FACTORY_ADDRESS = web3.main.to_checksum_address('0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f')
UNIVERSAL_UNISWAP_ROUTER_ADDRESS = web3.main.to_checksum_address('0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D')


/* Get Current Average Gas Price */
function getGasPrice() {
  web3.eth.getGasPrice().then(function(gasPrice) {
    console.log(`Average Gas Price in GWei: ${gasPrice / 1000000000}`);
  });
}

/* Convert ETH To USD */
function getAddressBalance(address) {
    axios.get('https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd')
    .then(response => {
      let ethPriceinUSD = response.data.ethereum.usd;
        web3.eth.getBalance(address).then(result => {
          let balanceinEther = web3.utils.fromWei(result, 'ether');
          console.log(` Balance in Ether: ${balanceinEther}`);
          console.log(` Balance in USD: ${balanceinEther * ethPriceinUSD}`);
      });
    })
    .catch(error => {
      console.log(error);
    }
  );
}

/* Get Contract ABI */
function getContractABI(JsonFile) {
  const contractJSON = JSON.parse(fs.readFileSync(JsonFile, 'utf8'));
  const abiString = JSON.stringify(contractJSON.abi);
  return contractJSON.abi;
}

/* Execute Swap */
function swapExactETHForTokens () { }

    uniSwapRouter.current = new web3.current.eth.Contract(
      uniRouterAbi,
      "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    );

    var swap = UniswapV2Router02Contract.methods.swapExactETHForTokens(amountOutMin, [WETH[activeChain].address, token.address], devAccount.address, timeStamp)
    var encodedABI = swap.encodeABI()
    var ethAmount = 1.5

    var tx = {
        from: devAccount.address,
        to: UniswapV2RouterAddress,
        gas: 200000,
        data: encodedABI,
        value: ethAmount
      };

    var signedTx = await devAccount.signTransaction(tx)

    web3.eth.sendSignedTransaction(signedTx.rawTransaction)
    .on('transactionHash', function(hash){

    })
    .on('confirmation', function(confirmationNumber, receipt){

    })
    .on('receipt', function(receipt){

    })
    .on('error', function(error, receipt) {
        // If the transaction was rejected by the network with a receipt, the second parameter will be the receipt.
        console.error("Error:", error, "Receipt:", receipt)
    });
}
