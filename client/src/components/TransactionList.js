import React, {useContext} from 'react'
import { GlobalContext } from '../context/GlobalState'
import { Transaction } from './Transaction';

export const TransactionList = () => {

    // We can access the entire global context/state from this component
    /*const context = useContext(GlobalContext);;*/

    // Or else we can just get the transactions out using destructuring...
    const { transactions } = useContext(GlobalContext);

    return (
        <>
            <h3>Transaction History</h3>
            <ul className="list">
                {transactions.map(transaction =>
                    ( <Transaction key={transaction.id} transaction={transaction} /> ))}
            </ul>
        </>
    )
}
