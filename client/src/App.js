import React, { Component } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import Navbar from './layout/Navbar';
import Banner from './layout/Banner';
import './App.css';
import getWeb3 from "./getWeb3";

class App extends Component {

  state = {
    storageValue: '',
    tempValue: '',
    setValue: '',
    web3: null,
    accounts: '',
    displayAccount: '',
    networkId: '',
    contract: null
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

      // const deployedNetwork = SimpleStorageContract.networks[networkId];
      // const instance = new web3.eth.Contract(
      //   SimpleStorageContract.abi,
      //   deployedNetwork && deployedNetwork.address,
      // );

      // Set web3, accounts, and contract to the state, and then proceed with an
      // example of interacting with the contract's methods.
      //this.setState({ web3, accounts, contract: instance }, this.runExample);

    } catch (error) {
      // Catch any errors for any of the above operations.
      alert(
        `Failed to load web3, accounts, or contract. Check console for details.`,
      );
      console.error(error);
    }
  };



  render() {
    return (
        <div>
            <Router>
              <Navbar
                userAccounts={this.state.accounts}
                displayAccount={this.state.displayAccount}
                web3={this.state.web3}
                networkId={this.state.networkId} />
              <Banner />
            </Router>
        </div>
    );
  }
}

export default App;
