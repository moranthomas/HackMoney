import React, { Component } from 'react'
import styled from "styled-components";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faInfoCircle, faNetworkWired, faSync} from '@fortawesome/free-solid-svg-icons';
export class Deposit extends Component {


    // constructor() {
    //     super();
    //     this.handleChangeCurrencyDropdown = this.handleChangeCurrencyDropdown.bind(this);
    //     //this.handleSubmit = this.handleSubmit.bind(this);
    // }

    state = {
        amountEth: '',
        chosenCurrency: ''
    };

    handleChangeCurrencyDropdown = async(event) => {
        event.preventDefault();
        var value = event.target.value;
        console.log('value = ' + value)
        this.setState({ chosenCurrency: value });

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


        return (
            <div className="container-borrow">

                <FontAwesomeIcon icon={faSync} size="2x" spin />
                <div className="wrapper">
                    <div className="box a">
                        <form onSubmit={this.handleSubmit}>
                            <Select value={this.state.chosenCurrency} onChange={this.handleChangeCurrencyDropdown}>
                                <option value="" hidden> Currency </option>
                                <option value="USDC">USDC</option>
                                <option value="DAI">DAI</option>
                                <option value="ETH">ETH</option>
                            </Select>
                            {/* <input type="submit" value="Submit" /> */}
                        </form>
                        {/* <button onClick={async () => {
                                console.log(this.eth())
                            }} >
                            Get Eth balance
                        </button> */}
                    </div>
                    <div className="box c">
                            Value of Wallet: {this.props.balanceInEth} {this.state.chosenCurrency}
                    </div>
                    <div className="box d">

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

                    <div className="box e">
                            Estimated Maturity Date/Time
                    </div>
                </div>

                <div className="info-icon-box">
                    <FontAwesomeIcon icon={faInfoCircle} size="2x" />
                </div>

                <div className="implied-rate-box">
                     Estimated Fixed Implied Rate: 26%
                </div>

                <div className="lock-in-fixed-rate">
                     Lock in Fixed Rate
                </div>
            </div>
        )
    }
}
export default Deposit
