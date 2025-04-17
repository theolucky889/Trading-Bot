const AV_KEY = import.meta.env.VITE_ALPHA_KEY     // put your key in .env

async function getUSPrice(symbol) {
  const url = `https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=${symbol}&apikey=${AV_KEY}&outputsize=compact`
  const r   = await fetch(url).then(r => r.json())
  const series = r['Time Series (Daily)']
  const labels = Object.keys(series).slice(0, 30).reverse()        // last 30 days
  const prices = labels.map(d => +series[d]['5. adjusted close'])
  return { labels, prices }
}

async function getTWPrice(symbol) {
  const url = 'https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_AVG_ALL'
  const list = await fetch(url).then(r => r.json())
  const row  = list.find(x => x.Code === symbol)
  return { labels: [row.Date], prices: [+row.Close] }              // simplified
}

async function getCryptoPrice(symbol) {
  const url = 'https://api.binance.com/api/v3/ticker/24hr'
  const list = await fetch(url).then(r => r.json())
  const row  = list.find(x => x.symbol === symbol)
  return { labels: [row.symbol], prices: [+row.lastPrice] }
}

/* entry‑point used by chartManager */
export async function fetchStockData(symbol, category) {
  switch (category) {
    case 'us-stocks':     return getUSPrice(symbol)
    case 'taiwan-stocks': return getTWPrice(symbol)
    default:              return getCryptoPrice(symbol)
  }
}

/* mocks left as‑is for volume / return‑loss */
export { fetchTradeVolume, fetchReturnLoss }     // unchanged
