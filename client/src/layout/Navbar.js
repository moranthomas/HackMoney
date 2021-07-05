import  React from 'react';
import { Link } from 'react-router-dom';
import convexityLogoLight from '../ConvexityLogoLight.png';
import { Route } from 'react-router-dom';
import Deposit from './Deposit';
import Borrow from './Borrow.js';

export default function Navbar(props) {
    const saved_props = props;
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
                    <Deposit {...props} {...saved_props}
                        accounts={saved_props.userAccounts}
                    />
                )}/>
                <Route path="/borrow" component={Borrow} />

            </div>
            <div style={blockchainInfoStyle}>
                <table><tbody>
                <tr><td textAlign = "right" style = {accountsStyle}>Account</td><td>{props.displayAccount}</td></tr>
                <tr><td style = {accountsStyle}>Network ID</td><td>{props.networkId}</td></tr>
                <tr><td style = {accountsStyle}>Chain ID</td><td>{props.chainId}</td></tr>
                <tr><td style = {accountsStyle}>USDC Exchange Rate</td><td>{props.cUSDCxr}</td></tr>
                <tr><td style = {accountsStyle}>ETH Balance</td><td>{props.balanceInEth}</td></tr>
                <tr><td style = {accountsStyle}>USDC Balance</td><td>{props.balanceInUSDC}</td></tr>
                <tr><td style = {accountsStyle}>Proxy Wallet</td><td>{props.proxyWalletDisplay}</td></tr>
                <tr><td style = {accountsStyle}>Proxy Wallet cUSDC</td><td>{props.pWalletCusdcBal}</td></tr>
                <tr><td style = {accountsStyle}>Proxy Wallet SFT</td><td>{props.pWalletSftBal}</td></tr>
                <tr><td style = {accountsStyle}>Proxy Wallet USDC value</td><td>{props.pWalletValueUsdc}</td></tr>
                <tr><td style = {accountsStyle}>Proxy Wallet USDC Maturity</td><td>{props.pWalletValueMat}</td></tr>
                </tbody></table>
            </div>

        </header>
    )
}

const accountsStyle = { fontSize: 16, marginBottom: '15px', textAlign: 'right' };

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
