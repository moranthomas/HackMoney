import  React, { useState } from 'react';
import { Link } from 'react-router-dom';
import convexityLogoLight from '../ConvexityLogoLight.png';
import { Route } from 'react-router-dom';
import Deposit from './Deposit';
import Borrow from './Borrow.js';

export default function Navbar(props) {

    // Declare a new state variable, which we'll call "fromAccount"
    const [fromAccount, setFromAccount] = useState();
    const [networkId, setNetworkId] = useState();
    const b2x = props.blocksToExpiry;
    const exb = props.expiryBlock;
    const balanceInEth = props.balanceInEth;
    const balanceInUSDC = props.balanceInUSDC;

    return (
        <header style={headerStyle}>
            <div style={centerFlex}>
            <Link to="/deposit">
                <img src={convexityLogoLight} style={logoStyle} alt=''/>
                </Link>
            </div>
            <div>
                <Link style={linkStyle} to="/deposit"> Deposit </Link>
                | <Link style={linkStyle} to="/borrow"> Borrow </Link>

                {/* <Route path="/" component={Home} /> */}
                {/* <Route path="/home" component={Home} /> */}
                <Route path="/deposit" render={(props) => (
                    <Deposit {...props}
                        blocksToExpiry={b2x}
                        expiryBlock={exb}
                        balanceInEth={balanceInEth}
                        balanceInUSDC={balanceInUSDC}
                    />
                )}/>
                <Route path="/borrow" component={Borrow} />


            </div>
            <div style={blockchainInfoStyle}>
                <p style = {accountsStyle} >Account: {props.displayAccount}</p>
                <p style = {accountsStyle} >Network ID: {props.networkId}</p>
                <p style = {accountsStyle} >Chain ID: {props.chainId} </p>
                <p style = {accountsStyle} >USDC Exchange Rate: {props.cUSDCxr} </p>
                <p style = {accountsStyle} >ETH Balance: {props.balanceInEth} </p>
                <p style = {accountsStyle} >USDC Balance: {props.balanceInUSDC} </p>
                <p style = {accountsStyle} >User Wallet: {props.proxyWalletDisplay} </p>
            </div>

        </header>
    )
}

const accountsStyle = { fontSize: 16, marginBottom: '15px' };

const blockchainInfoStyle = {
    position: 'fixed',
    top: '15%',
    right: '10%',
    color: '#372b25',
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
