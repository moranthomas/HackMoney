import React, { Component } from 'react'
import styled from "styled-components";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faInfoCircle, faSync} from '@fortawesome/free-solid-svg-icons';
export class Deposit extends Component {

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

                <div class="wrapper">
                    <div class="box a">

                    <Select>
                            <option value="" hidden>
                            Currency
                            </option>
                            <option value="1">USDC</option>
                            <option value="2">DAI</option>
                            <option value="3">ETH</option>
                        </Select>
                    </div>
                    <div class="box c">
                        <card>
                            Value of wallet
                        </card>
                    </div>
                    <div class="box d">
                        <card>
                            <Select>
                                <option value="" hidden>
                                Select Maturity
                                </option>
                                <option value="1">Quarter 1</option>
                                <option value="2">Quarter 2</option>
                                <option value="3">Quarter 3</option>
                                <option value="4">Quarter 4</option>
                            </Select>
                        </card>
                    </div>
                    <div class="box e">
                        <card>
                            Estimated Maturity Date/Time
                        </card>
                    </div>
                </div>

                <div class="info-icon-box">
                    <FontAwesomeIcon icon={faInfoCircle} size="2x" />
                </div>

                <div class="implied-rate-box">
                    <card>
                     Estimated Fixed Implied Rate: 26%
                    </card>
                </div>

                <div class="lock-in-fixed-rate">
                    <card>
                     Lock in Fixed Rate
                    </card>
                </div>

            </div>
        )
    }
}
export default Deposit
