import  React, { useState } from 'react';
import { Link } from 'react-router-dom';
import convexityLogoLight from '../ConvexityLogoLight.png';
import { Route } from 'react-router-dom';
import Deposit from './Deposit';
import Market from './Market.js';
import Borrow from './Borrow.js';


export default function Navbar(props) {

    // Declare a new state variable, which we'll call "fromAccount"
    const [fromAccount, setFromAccount] = useState();
    const [networkId, setNetworkId] = useState();

    return (
        <header style={headerStyle}>
            <div style={centerFlex}>
                <img src={convexityLogoLight} style={logoStyle} alt=''/>
            </div>
            <div>
                <Link style={linkStyle} to="/deposit"> Deposit </Link>
                | <Link style={linkStyle} to="/borrow"> Borrow </Link>
                | <Link style={linkStyle} to="/market"> Market </Link>

                {/* <Route path="/" component={Deposit} /> */}
                <Route path="/deposit" component={Deposit} />
                <Route path="/borrow" component={Borrow} />
                <Route path="/market" component={Market} />
            </div>
            <div style={connectorStyle}>
                <button style={connectWalletBtn} onClick={() => setFromAccount("0x123")}>
                    Connect Wallet
                </button>
                <p style = {accountsStyle} >Account: {props.displayAccount}</p>
                <p style = {accountsStyle} >NetworkID: {props.networkId}</p>
                {/* <p style = {accountsStyle} >Your account balance: {this.state.accountBalance} Eth </p> */}
            </div>

        </header>
    )
}

const accountsStyle = { fontSize: 16, marginBottom: '15px' };

const connectorStyle = {
    position: 'fixed',
    top: '10%',
    right: '10%',
    color: '#372b25',
}

const connectWalletBtn = {
    marginBottom: '15px',
    padding: '10px',
    borderRadius: '5px',
    borderColor: 'white',
    color: 'white',
    backgroundColor: '#BE9325'
  }

const centerFlex = {
    position: 'fixed',
    top: '7%',
    left: '8%',
    transform: 'translate( -50%)',
    width: '120px'
}

const logoStyle = {
    textAlign: 'left',
    padding: '0px',
    float: 'left',
    width: '160px'
}

const headerStyle = {
    background: '#372b25',
    color: '#fff',
    textAlign: 'center',
    padding: '40px',
    marginTop: '40px',
    boxShadow: 'var(--box-shadow)',
    display: 'flex',
    justifyContent: 'space-between'
}

const linkStyle = {
    fontSize: '20px',
    color: '#fff',
    textDecoration: 'none',
    marginLeft: '20px',
    marginRight: '20px'
}
