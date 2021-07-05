import React, { Component } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import Navbar from './layout/Navbar';
import Banner from './layout/Banner';
import './App.css';
import getWeb3 from "./getWeb3";
import map from "./artifacts/deployments/map.json";               // map gets created on brownie deploy
import ProxyWalletJSON from "./artifacts/contracts/ProxyWallet.json";   // for Abi
import FutureTokenJSON from "./artifacts/contracts/FutureToken.json";   // for Abi
import Compound from '@compound-finance/compound-js';
import MetaMaskOnboarding from '@metamask/onboarding'
import { OnboardingButton } from './components/OnboardingButton';

const config = require('./config/config_mainnet.json');

class App extends Component {

  state = {
    storageValue: '',
    tempValue: '',
    setValue: '',
    web3: null,
    accounts: '',
    displayAccount: '',
    networkId: '',
    chainId: '',
    contract: null,
    cUSDCxr: '',
    balanceInEth: '',
    balanceInUSDC: ''
  };
  

  isMetaMaskInstalled = () => MetaMaskOnboarding.isMetaMaskInstalled()

  componentDidMount = async () => {
    const decimals = {usdc : 6, cusdc: 8, cusdcRate : 16};
    const scaler = {
      usdc : Math.pow(10, decimals.usdc),
      cusdc : Math.pow(10, decimals.cusdc),
      cusdcRate : Math.pow(10,decimals.cusdcRate)
    }
    try {

      const web3 = await getWeb3();                     // Get network provider and web3 instance.
      this.setState({ web3: web3 });

      const userAccounts = await web3.eth.getAccounts();    // Use web3 to get the user's accounts.
      const networkId = await web3.eth.net.getId();         // Get the contract instance.
      const chainId = await web3.eth.getChainId()

      console.log("networkId: ", networkId);
      console.log("chainId: ", chainId);
      console.log("User Accounts:" , userAccounts);

      // getEthBalance
      var balance = await web3.eth.getBalance(userAccounts[0]);
      const balanceInEth = web3.utils.fromWei(balance, 'ether');
      //console.log(balanceInEth + ' ETH in wallet');
      this.setState( { balanceInEth: balanceInEth });

      // getUSDCTokenBalance
      const USDContractInstance = await new web3.eth.Contract(config.usdcAbi, config.usdcAddress);
      let usdcBalance = await USDContractInstance.methods.balanceOf(userAccounts[0]).call();
      //sdcBalance = web3.utils.hexToNumber(usdcBalance) / Math.pow(10, 6);
      this.setState( { balanceInUSDC: usdcBalance });
      console.log(' usdcBalance == $ ' + usdcBalance );

      let displayAccount = userAccounts[0].substring(0,8);

      this.setState({ accounts: userAccounts });
      this.setState({ displayAccount: displayAccount });
      this.setState({ networkId: networkId });
      this.setState({ chainId: chainId });

      //when brownie deploys contracts with helper, it drops in more addresses

      const proxyWalletMasterAddress = map.dev.ProxyWallet[map.dev.ProxyWallet.length-1].toString(); 
      const proxyWalletAbi = ProxyWalletJSON.abi;
      const proxyWalletMaster = new web3.eth.Contract(
        proxyWalletAbi,
        proxyWalletMasterAddress,
      );
     
      const futureTokenMasterAddress = map.dev.FutureToken[map.dev.FutureToken.length-1].toString();
      const futureTokenAbi = FutureTokenJSON.abi;
      const futureTokenMaster = new web3.eth.Contract(
        futureTokenAbi,
        futureTokenMasterAddress,

      );

      // cUSDC address and ABI
      // I've moved this up so that I can call the cUsdcAddress lower
      const cUsdcAddress = config.cUsdcAddress;
      const cUsdcAbi = config.cUsdcAbi;
      const cUsdcContract = new web3.eth.Contract(
        cUsdcAbi,
        cUsdcAddress,
      );



      console.log('proxyWalletMaster: ' + proxyWalletMaster);
      
      //Goal is to create a wallet contract instance
      //this transaction gets or creates a wallet if needed.
      //we should check if the userAccount already has a wallet deployed
      //declare a walletAddress variable
      var proxyWalletAddress = '';
      
      try {
        //try calling the getClone method. If there is no clone, then we will get an error
        proxyWalletAddress = await proxyWalletMaster.methods.getWallet().call({'from': userAccounts[0]});
      }
        catch (error){
        //on the error, ask user to send a transaction creating a clone and console print the cloneAddress
        proxyWalletAddress= await proxyWalletMaster.methods.createWalletIfNeeded().send({'from': userAccounts[0]});
      }
      console.log('wallet address is : ' + proxyWalletAddress);
      //now we have the walletAddress
      //lets create a wallet web3 contract instance that we can work with
      //the walletContract will have the same abi as the ProxyWalletInstance
      const proxyWallet = new web3.eth.Contract(
        proxyWalletAbi,
        proxyWalletAddress,
      );
      this.setState({ proxyWalletDisplay: proxyWalletAddress.substring(0,8) });
      console.log('proxyWalletAddress ' + this.state.proxyWalletDisplay);
      
      //The goal here is to find out the futureClass Token expiry block
      //We will assume that the script has run and there is an exisiting expiry
      //we need to first find out the address of the futureClass.

      //get the blockNumber to calculate the nextExpiry
      const blockNumber = await web3.eth.getBlockNumber();
      console.log('block height ' + blockNumber);
      //find out what the next Expiry block is that is at 196608 blocks from now
      var nextExpiry = await futureTokenMaster.methods.calcNextExpiryBlockAfter(196608).call(); 
      console.log('next expiry should be '+ nextExpiry);
      var futureTokens = []

      try{
        futureTokens = await futureTokenMaster.methods.getExpiryClassLongShort(cUsdcAddress,nextExpiry).call(); //with that and the cUSDC token address, we can get the three tokens
        
        //sometimes the future tokens are created right at a multiple of 4096, then the expiry might be missed
        if(futureTokens[0] === '0x0000000000000000000000000000000000000000'){
          console.log('trying again to find expiry')
          nextExpiry = nextExpiry-4096;
          futureTokens = await futureTokenMaster.methods.getExpiryClassLongShort(cUsdcAddress,nextExpiry).call();
        }

        //we have the token address, so now lets create future token class contract instances
        //const futureTokenClassAbi = futureTokenClassJson.abi;
        const futureTokenClass = new web3.eth.Contract(
          futureTokenAbi,
          futureTokens[0].toString(),
        )
        console.log('futureTokenClass ' + futureTokens[0].toString());
        //lets make futureTokenShort contract instance too
        const futureTokenShort = new web3.eth.Contract(
          futureTokenAbi,
          futureTokens[2].toString(),
        )
        console.log('futureTokenShort is good')
        


        //getting price data
        //APY calculation function
        function calcImpliedsftAPY(sft_res, ctok_res, min_xr, cxr, col, blks, bpy){
          const apy = (min_xr*(1+col/1e18-ctok_res/sft_res)/cxr-1)*bpy/blks;
          return apy;
        }

        //returns the amm price
        function ammPrice(ft_res, ctok_res){
          return ctok_res/ft_res;
        }

        //returns implied sft exchangeRate
        function ammImpSftXR(sft_res, ctok_res, min_xr, col) {
          return min_xr*(1+col/1e18-ctok_res/sft_res);
        }
        
        //getting the variables
        const prices = await proxyWallet.methods.getPricing(cUsdcAddress,nextExpiry).call();
        
        const sftReserves = prices[4];
        const cUsdcReserves = prices[5];
        const sftPrice = ammPrice(sftReserves, cUsdcReserves);
        
        const minxr = await futureTokenClass.methods.createPrice().call();
        const cxr = prices[0];
        const collatFactor = await futureTokenShort.methods.collateralFactor().call();
        const blocksToExpiry = await futureTokenClass.methods.blocksToExpiry().call();
        const sftImpXr = ammImpSftXR(sftReserves, cUsdcReserves, minxr, collatFactor);
        const blocksPerYear = 365*24*60*60/13.15;
        this.setState({expiryBlock: nextExpiry});//set state for the expiryBlock
        this.setState({blocksToExpiry: blocksToExpiry}); //set State for blocksToExpiry

        console.log(
          'sft reserves : ' + sftReserves + '\n' +
          'cusdc reserves : ' + cUsdcReserves +'\n' +
          'sft price : ' + sftPrice +'\n' +
          'sft Implied XR : ' + sftImpXr +'\n' +
          'minxr : ' + minxr +'\n' +
          'cxr : ' + cxr +'\n' +
          'collatFactor : ' + collatFactor +'\n' +
          'blocksToExpiry : ' + blocksToExpiry +'\n'
        );

        const impFixedApy = calcImpliedsftAPY(sftReserves, cUsdcReserves, minxr, cxr, collatFactor, blocksToExpiry, blocksPerYear);

        console.log('current AMM implied APY ' + impFixedApy);
        this.setState({impFixedApy : impFixedApy});

        //here we find out the proxyWallet's cToken balances - raw
        const pWalletCusdcBal = await cUsdcContract.methods.balanceOf(proxyWalletAddress).call()/scaler.cusdc;
        this.setState({pWalletCusdcBal: pWalletCusdcBal});

        //here we find out the proxyWallet's SFT balances - raw
        const pWalletSftBal = await futureTokenShort.methods.balanceOf(proxyWalletAddress).call()/scaler.cusdc;
        this.setState({pWalletSftBal: pWalletSftBal});

        //SFT value is SFT balances * Sftprice -raw
        const sftValue = pWalletSftBal * sftPrice;
        //and the value of the whole wallet is SFT + cTokens -raw
        const pWalletValueCusdc = sftValue + pWalletCusdcBal;
        //and the underlying value is - raw
        const pWalletValueUsdc = pWalletValueCusdc*prices[0]/scaler.cusdcRate;      
        this.setState({pWalletValueUsdc: pWalletValueUsdc});
        //the expected USDC value at maturity is current cUSDC value times SFT AMM price
        const pWalletValueMat = pWalletValueCusdc*sftImpXr/scaler.cusdcRate;
        
        this.setState({pWalletValueMat: pWalletValueMat});
        const hedgeRatio = pWalletSftBal/(pWalletCusdcBal + sftPrice*pWalletSftBal);
        console.log('hedge Ratio is ' + hedgeRatio);

      }
        catch(error){
          console.log('looks like the future tokens were not instantiated. Check the Expiry Block')
        }



      console.log('future class ' + futureTokens[0].toString());

      console.log('next expiry is ' + nextExpiry + ' block')

      //console.log('proxyClone: ' + JSON.stringify(proxyClone) );

      console.log('futureTokenMaster: ' + futureTokenMaster);
      //const futureTokenSupply = await FutureTokenInstance.methods.supply(20).call();

      //this.CompoundSupplyRatePerBlock();
      //const cUsdtAddress = Compound.util.getAddress(Compound.cUSDT);
      //console.log('Compound cUsdtAddress: ' + cUsdtAddress);



      // consts and formulae
      const owner = "0xbcd4042de499d14e55001ccbb24a551f3b954096"; //owner of the Contract is also the market maker
      const expiryDateObject = new Date('June 5 2022');
      const today = new Date();
      const msPerYear = 24 * 60 * 60 * 1000 *365; // Number of milliseconds per year


      //returns the current exchange rate from cUSDC contract
      async function cUSDCExchangeRate () {
        const xr = await cUsdcContract.methods.exchangeRateCurrent().call()/scaler.cusdcRate;
        return xr
      }

      const cUSDCxr = await cUSDCExchangeRate();
      this.setState({ cUSDCxr: parseFloat(cUSDCxr).toFixed(4)});




      //Set web3, accounts, and contract to the state - for more flexiblility.
      //this.setState({ web3, accounts, contract: instance }, this.runExample);

    } catch (error) {
      // Catch any errors for any of the above operations.
      alert(
        `Failed to load web3, accounts, or contract. Check console for details.`,
      );
      console.error(error);
    }
  };

  CompoundSupplyRatePerBlock() {
    const cUsdtAddress = Compound.util.getAddress(Compound.cUSDT);
      (async function() {
        let supplyRatePerBlock = await Compound.eth.read(
          cUsdtAddress,
          'function supplyRatePerBlock() returns (uint)',
          [], // [optional] parameters
          {}  // [optional] call options, provider, network, ethers.js "overrides"
        );
        console.log('USDT supplyRatePerBlock:', supplyRatePerBlock.toString());
      })().catch(console.error);
  }

  render() {
    return (
        <div>
            <Router>
              <Navbar
                userAccounts={this.state.accounts}
                displayAccount={this.state.displayAccount}
                web3={this.state.web3}
                cUSDCxr={this.state.cUSDCxr}
                networkId={this.state.networkId}
                chainId={this.state.chainId}
                //pass blocksToExpiry and expiryBlock as props so that we can display it in the deposit page
                blocksToExpiry={this.state.blocksToExpiry}
                expiryBlock={this.state.expiryBlock}
                balanceInEth={this.state.balanceInEth}
                balanceInUSDC={this.state.balanceInUSDC}
                //add userWallet as a prop
                proxyWalletDisplay={this.state.proxyWalletDisplay}
                pWalletCusdcBal={this.state.pWalletCusdcBal}
                pWalletSftBal={this.state.pWalletSftBal}
                pWalletValueUsdc={this.state.pWalletValueUsdc}
                pWalletValueMat={this.state.pWalletValueMat}
                impFixedApy={this.state.impFixedApy}
                />

                <OnboardingButton></OnboardingButton>

              <Banner />
            </Router>
        </div>
    );
  }
}

export default App;
