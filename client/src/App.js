import React, { Component } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import Navbar from './layout/Navbar';
import Banner from './layout/Banner';
import './App.css';
import getWeb3 from "./getWeb3";
import map from "./artifacts/deployments/map.json";               // map gets created on brownie deploy
import ProxyWallet from "./artifacts/contracts/ProxyWallet.json";   // for Abi
import FutureToken from "./artifacts/contracts/FutureToken.json";   // for Abi
import Compound from '@compound-finance/compound-js';
import MetaMaskOnboarding from '@metamask/onboarding'
import { OnboardingButton } from './components/OnboardingButton';

//here are the changes as far as pwclone goes in terms of imports
import futureTokenClassJson from "./artifacts/contracts/FutureTokenClass.json"; //import futureTokenClass Abi
import futureTokenSeriesJson from "./artifacts/contracts/FutureTokenSeries.json"; //import futureTokenClass Abi

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
    cUSDCxr: ''
  };

  isMetaMaskInstalled = () => MetaMaskOnboarding.isMetaMaskInstalled()

  componentDidMount = async () => {
    try {

     // console.log('isMetaMaskInstalled() = '+ this.isMetaMaskInstalled());

      const web3 = await getWeb3();                     // Get network provider and web3 instance.
      this.setState({ web3: web3 });

      const userAccounts = await web3.eth.getAccounts();    // Use web3 to get the user's accounts.
      const networkId = await web3.eth.net.getId();         // Get the contract instance.
      const chainId = await web3.eth.getChainId()

      console.log("networkId: ", networkId);
      console.log("chainId: ", chainId);
      console.log("User Accounts:" , userAccounts);

      let displayAccount = userAccounts[0].substring(0,8);
      this.setState({ accounts: userAccounts });
      this.setState({ displayAccount: displayAccount });
      this.setState({ networkId: networkId });
      this.setState({ chainId: chainId });


      const ProxyWalletAddress = map.dev.ProxyWallet.toString();
      const ProxyWalletAbi = ProxyWallet.abi;
      const ProxyWalletInstance = new web3.eth.Contract(
        ProxyWalletAbi,
        ProxyWalletAddress,
      );
     
      const FutureTokenAddress = map.dev.FutureToken.toString();
      const FutureTokenAbi = FutureToken.abi;
      const FutureTokenInstance = new web3.eth.Contract(
        FutureTokenAbi,
        FutureTokenAddress,
      );

      // cUSDC address and ABI
      // I've moved this up so that I can call the cUsdcAddress lower
      const cUsdcAddress = config.cUsdcAddress;
      const cUsdcAbi = config.cUsdcAbi;
      const cUsdcContract = new web3.eth.Contract(
        cUsdcAbi, 
        cUsdcAddress,
      );


      console.log('proxyWalletInstance: ' + ProxyWalletInstance);
      
      //Goal is to create a clone contract instance
      //this transaction gets or creates a clone.
      //we should check if the userAccount already has a clone deployed
      //declare a cloneAddress variable
      var cloneAddress = '';
      
      try {
        //try calling the getClone method. If there is no clone, then we will get an error
        cloneAddress = await ProxyWalletInstance.methods.getClone().call({'from': userAccounts[0]});
      }
        catch (error){
        //on the error, ask user to send a transaction creating a clone and console print the cloneAddress
        cloneAddress= await ProxyWalletInstance.methods.getOrCreateClone().send({'from': userAccounts[0]});
      }
      console.log('clone address is : ' + cloneAddress);
      //now we have the cloneAddress
      //lets create a clone web3 contract instance that we can work with
      //the cloneContract will have the same abi as the ProxyWalletInstance
      const cloneContract = new web3.eth.Contract(
        ProxyWalletAbi,
        cloneAddress,
      );
      const check = await cloneContract.methods.proxyAddress().call();
      console.log('proxywallet address is ' + ProxyWalletAddress);
      console.log('proxyAddress of clone is ' + check.toString());
      
      //The goal here is to find out the futureClass Token expiry block
      //We will assume that the script has run and there is an exisiting expiry
      //we need to first find out the address of the futureClass.
      //Make sure to have run the xyz script!
      const blockNumber = await web3.eth.getBlockNumber(); //get the blockNumber to calculate the nextExpiry
      const nextExpiry = await FutureTokenInstance.methods.calcExpiry(blockNumber).call(); //find out what the next Expiry block is
      var futureTokens = []
      try{
        futureTokens = await FutureTokenInstance.methods.getExpiryClassLongShort(cUsdcAddress,nextExpiry).call(); //with that and the cUSDC token address, we can get the three tokens
        this.setState({expiryBlock: nextExpiry});//set state for the expiryBlock
        this.setState({blocksToExpiry: nextExpiry-blockNumber}); //set State for blocksToExpiry
        //we have the token address, so now lets create future token class contract instances
        //const futureTokenClassAbi = futureTokenClassJson.abi;
        const futureTokenClass = new web3.eth.Contract(
          futureTokenClassJson.abi,
          futureTokens[0].toString(),
        )
        //lets make futureTokenShort contract instance too
        const futureTokenShort = new web3.eth.Contract(
          futureTokenSeriesJson.abi,
          futureTokens[2].toString(),
        )
      }
        catch(error){
          console.log('looks like the future tokens were not instantiated')
        }



      console.log('future class ' + futureTokens[0].toString());

      console.log('next expiry is ' + nextExpiry + ' block')

      //console.log('proxyClone: ' + JSON.stringify(proxyClone) );

      console.log('FutureTokenInstance: ' + FutureTokenInstance);
      //const futureTokenSupply = await FutureTokenInstance.methods.supply(20).call();

      this.CompoundSupplyRatePerBlock();
      const cUsdtAddress = Compound.util.getAddress(Compound.cUSDT);
      console.log('Compound cUsdtAddress: ' + cUsdtAddress);

      

      // consts and formulae
      const owner = "0xbcd4042de499d14e55001ccbb24a551f3b954096"; //owner of the Contract is also the market maker
      const expiryDateObject = new Date('June 5 2022');
      const today = new Date();
      const msPerYear = 24 * 60 * 60 * 1000 *365; // Number of milliseconds per year
      const decimals = {usdc : 6, cusdc: 8, cusdcRate : 16};
      const scaler = {
        usdc : Math.pow(10, decimals.usdc),
        cusdc : Math.pow(10, decimals.cusdc),
        cusdcRate : Math.pow(10,decimals.cusdcRate)
      }

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
                />
                

                {/* <button onClick={async () => {
                  console.log(this.CompoundSupplyRatePerBlock())
                   }} >
                    Get Compound USDT rate
                </button> */}

                <OnboardingButton></OnboardingButton>

              <Banner />
            </Router>
        </div>
    );
  }
}

export default App;
