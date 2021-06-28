import React, { useContext, useState } from 'react'

import { GlobalContext } from '../context/GlobalState'

export const AddTransaction = () => {

    const [text, setText] = useState('');
    const [amount, setAmount] = useState(0);

    const {addTransaction} = useContext(GlobalContext);

    const onSubmit = e => {
        e.preventDefault();
        const newTransaction = {
            id: Math.floor(Math.random() * 100000000),
            text: text,
            amount: +amount
        }
        addTransaction(newTransaction);
    }

    return (
        <>
            <form onSubmit={onSubmit}>
                <div className="form-control">
                    <label htmlFor="text">Add Description </label>
                    <input type="text" value={text} onChange={
                        (e) => setText(e.target.value)}
                        placeholder="Enter text...">
                    </input>
                </div>
                <div className="form-control">
                    <label htmlFor="amount">Add Amount <br/>
                    (negative for  expense, positive for income)
                    </label>
                    <input type="number" value={amount} onChange={
                        (e) => setAmount(e.target.value)} placeholder="Enter amount..."  />
                </div>
                <button className="btn">Add transaction</button>
            </form>
        </>
    )
}
