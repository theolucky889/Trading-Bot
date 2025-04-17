import axios from 'axios'

const AV_KEY = import.meta.env.VITE_ALPHA_KEY     // free Alpha‑Vantage key

export async function getUSDaily(symbol) {
  const { data } = await axios.get(
    `/av/query`, {
      params: {
        function: 'TIME_SERIES_DAILY_ADJUSTED',
        symbol,
        apikey: AV_KEY,
        outputsize: 'compact'
      }
    }
  )
  const series = data['Time Series (Daily)']
  const labels = Object.keys(series).slice(0, 30).reverse()
  const prices = labels.map(d => +series[d]['5. adjusted close'])
  return { labels, prices }
}

/* TWSE – via proxy to https://www.twse.com.tw/exchangeReport */
export async function getTWSEDaily(stockNo) {
  const { data } = await axios.get(
    `/twse/STOCK_DAY`, { params: { response: 'json', date: '', stockNo } }
  )
  // latest close is at data.data[data.data.length‑1][6]
  return {
    labels: data.data.map(r => r[0]),
    prices: data.data.map(r => +r[6])
  }
}

/* Crypto via Binance */
export async function getKlines(symbol = 'BTCUSDT', limit = 30) {
  const { data } = await axios.get(
    `https://api.binance.com/api/v3/klines`,
    { params: { symbol, interval: '1d', limit } }
  )
  return {
    labels: data.map(k => new Date(k[0]).toLocaleDateString()),
    prices: data.map(k => +k[4])
  }
}
