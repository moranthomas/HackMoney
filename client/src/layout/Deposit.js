import React, { Component } from 'react'
import styled from "styled-components";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faInfoCircle, faNetworkWired, faSync} from '@fortawesome/free-solid-svg-icons';
import getWeb3 from "../getWeb3";
export class Deposit extends Component {

    state = {
        amountEth: '',
        chosenCurrency: '',
        web3: '',
        amountValue: ''
    };

    componentDidMount = async () => {
        try {
            const web3 = await getWeb3();
            this.setState({ web3: web3 });
        } catch (error) {
            // Catch any errors for any of the above operations.
            alert(
            `Failed to load web3, accounts, or contract. Check console for details.`,
            );
            console.error(error);
        }
    };

    handleChangeCurrencyDropdown = async(event) => {
        event.preventDefault();
        var value = event.target.value;
        console.log('new value = ' + value)
        this.setState({ chosenCurrency: value });

    }

    handleChangeInputAmount = async(event) => {
        const amount  = event.target.value;
        console.log(amount);
        this.setState({ amountValue: amount});
    }

    handleSubmitDeposit = async(event) => {
        event.preventDefault();
        const { accounts, contract } = this.state;
        var amtEthValue = Number(this.state.amountEth);
        amtEthValue = this.state.amountValue;

        console.log('amountEth: ' + amtEthValue );
        console.log('depositing to proxy contract!' + this.props.walletContract)

        // TODO Where should we put the approve function ??

        const from = this.props.accounts[0];
        const count = await this.state.web3.eth.getTransactionCount(from);
        //const gasPrice = this.state.web3.eth.gasPrice.toNumber();
        const gasPrice = 80;
        const nonce = 4;

        const rawTx = {
            "from": from,
            "nonce": nonce,
            "gas": 210000,          //(optional == gasLimit)
            // "gasPrice": 4500000,  (optional)
            // "data": 'For testing' (optional)
        };
        // Always use arrow functions to avoid scoping and 'this' issues like having to use 'self'
        // in general we should probably use .transfer() over .send() method
        const depositResponse = await this.props.walletContract.methods.deposit(
            amtEthValue, '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE').send(rawTx);

        console.log('depositResponse: ' + JSON. stringify(depositResponse) );
        // // Update state with the result
        // var updatedAmountEth = Number(this.state.amountEth) + amtEthValue;
        // this.setState({ amountEth: updatedAmountEth });
    }


    render() {
        const Select = styled.select`
            width: 100%;
            height: 35px;
            background: white;
            color: gray;
            padding-left: 5px;
            font-size: 14px;
            border: none;
            margin-left: 10px;

        option {
            color: black;
            background: white;
            display: flex;
            white-space: pre;
            min-height: 20px;
            padding: 0px 2px 1px;
        }
        `;

        const Input = styled.input`
            padding-left: 5px;
            margin-left: 5px;
            font-size: 8px;
            font-weight: 200;
            width: 85%;
            color: gray;
            background: white;
            border: none;
            border-radius: 2px;
        `;



        return (
            <div className="container-borrow">
            <form onSubmit={this.handleSubmit}>
                <FontAwesomeIcon icon={faSync} size="2x" spin />
                <div className="wrapper">


                    <div className="box a">
                            <Select value={this.state.chosenCurrency} onChange={this.handleChangeCurrencyDropdown}>
                                <option value="" hidden> Currency </option>
                                <option value="USDC">USDC</option>
                                <option value="DAI">DAI</option>
                                <option value="ETH">ETH</option>
                            </Select>
                            {/* <input type="submit" value="Submit" /> */}
                    </div>
                    <div className="box b">
                            Max Value of Wallet: {this.state.chosenCurrency == 'ETH' && this.props.balanceInEth}
                            {this.state.chosenCurrency}
                    </div>
                    <div className="box c">
                            <div>Deposit Funds: </div>
                    </div>
                    <div className="box c">
                        <Input
                        value={this.state.amountValue}
                        type="text" onChange={this.handleChangeInputAmount} />
                    </div>
                    <div className="box e">

                            <Select>
                                <option value="" hidden>
                                Select Maturity Block
                                </option>
                                <option value="1">{this.props.expiryBlock}</option>
                                <option value="2">Quarter 2</option>
                                <option value="3">Quarter 3</option>
                                <option value="4">Quarter 4</option>
                            </Select>
                    </div>

                    <div className="box f">
                            Estimated Maturity Date/Time
                    </div>

                </div>

                <div className="info-icon-box">
                    <FontAwesomeIcon icon={faInfoCircle} size="2x" />
                </div>

                <div className="implied-rate-box">
                     Estimated Fixed Implied Rate: 26%
                </div>

                <div>
                    <button id="Deposit" className="lock-in-fixed-rate" onClick={this.handleSubmitDeposit.bind(this)}> Lock in Fixed Rate</button>
                </div>
                </form>
            </div>
        )
    }
}
export default Deposit
