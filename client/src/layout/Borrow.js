import React, { Component } from 'react'
import { AddTransaction}  from '../components/AddTransaction';
import { Balance } from '../components/Balance.js';
import { IncomeExpenses } from '../components/IncomeExpenses';
import { TransactionList } from '../components/TransactionList';

export class Borrow extends Component {
    render() {
        return (
            <div className="container">
              <Balance />
              <IncomeExpenses />
              <TransactionList />
              <AddTransaction />
            </div>
        )
    }
}

export default Borrow
