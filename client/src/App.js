import React, { Component } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import Navbar from './layout/Navbar';
import Banner from './layout/Banner';
import './App.css';
import getWeb3 from "./getWeb3";
//my brownie instance drops in a "map" file when deployed on brownie
import map from "./artifacts/deployments/map.json";
//and the abi is found under contracts within ProxyWallet.json
import ProxyWallet from "./artifacts/contracts/ProxyWallet.json";
import Compound from '@compound-finance/compound-js';
// const Compound = props => (
  //<ScriptTag type="text/javascript" src="https://cdn.jsdelivr.net/npm/@compound-finance/compound-js@0.2.5/dist/browser/compound.min.js" />);
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
    contract: null,
    cUSDCxr: ''
  };

  componentDidMount = async () => {
    try {
      const web3 = await getWeb3();                     // Get network provider and web3 instance.
      this.setState({ web3: web3 });

      const userAccounts = await web3.eth.getAccounts();    // Use web3 to get the user's accounts.
      const networkId = await web3.eth.net.getId();         // Get the contract instance.
      console.log("neteworkId: ", networkId);
      console.log("User Accounts:" , userAccounts);

      let displayAccount = userAccounts[0].substring(0,8);
      this.setState({ accounts: userAccounts });
      this.setState({ displayAccount: displayAccount });
      this.setState({ networkId: networkId });
      const ProxyWalletAddress = map.dev.ProxyWallet.toString();
      const ProxyWalletInstance = new web3.eth.Contract(
        ProxyWallet.abi,
        ProxyWalletAddress,
      );

      console.log(ProxyWalletInstance);

      //const compound = new Compound(window.ethereum);
      this.CompoundSupplyRatePerBlock();
      const cUsdtAddress = Compound.util.getAddress(Compound.cUSDT);
      console.log('Compound cUsdtAddress: ' + cUsdtAddress);

      // const getBalanceResponse = await ProxyWalletInstance.methods.getContractBalanceOfEther().call();
      // console.log('getBalanceResponse: ' + getBalanceResponse );

      const proxyClone = await ProxyWalletInstance.methods.getOrCreateClone().call();
      console.log('proxyClone: ' + JSON.stringify(proxyClone) );

      // cUSDC address and ABI
      const cUsdcAddress = config.cUsdcAddress;
      const cUsdcAbi = config.cUsdcAbi;
      const cUsdcContract = new web3.eth.Contract(cUsdcAbi, cUsdcAddress);

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



      //here we build the USDC contract and ABI
      var usdcAddress = config.usdcAddress;
      const usdcAbi = config.usdcAbi;
      const usdcContract = new web3.eth.Contract(usdcAbi, usdcAddress);


      // Set web3, accounts, and contract to the state - for more flexiblility.
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
                networkId={this.state.networkId} />

                <button onClick={async () => {
                  console.log(this.CompoundSupplyRatePerBlock())
                   }} >
                    Get Compound USDT rate
                </button>

              <Banner />
            </Router>
        </div>
    );
  }
}

export default App;
