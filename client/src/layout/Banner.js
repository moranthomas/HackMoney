import React from 'react';

export default function Banner() {
    return (
        <div style={headerStyle}>
            <div style={centerFlex}></div>
        </div>
    )
}

const centerFlex = {
    position: 'fixed',
    top: '7%',
    left: '8%',
    transform: 'translate( -50%)',
    width: '120px'
}
const headerStyle = {
    background: 'f8ecf4',
    textAlign: 'center',
    padding: '40px',
    marginTop: '10px',
    display: 'flex',
    justifyContent: 'space-between'
}
