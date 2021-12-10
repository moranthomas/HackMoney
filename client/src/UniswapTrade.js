const { ChainId, Fetcher, WETH, Route, Trade, TokenAmount, TradeType, Token } = require ('@uniswap/sdk');

const DAI = new Token(
  ChainId.MAINNET,
  "0x6B175474E89094C44Da98b954EedeAC495271d0F",
  18
);

// note that you may want/need to handle this async code differently,
// for example if top-level await is not an option

const pair = async () => {
    Fetcher.fetchPairData(DAI, WETH[DAI.chainId]);
}
const route = new Route([pair], WETH[DAI.chainId]);

const amountIn = "1000000000000000000"; // 1 WETH

const trade = new Trade(
  route,
  new TokenAmount(WETH[DAI.chainId], amountIn),
  TradeType.EXACT_INPUT
);