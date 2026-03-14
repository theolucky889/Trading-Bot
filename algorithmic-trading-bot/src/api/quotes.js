import axios from 'axios'

function authHeaders() {
  const token = localStorage.getItem('auth_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/** US stock daily prices — proxied through backend using user's stored AV key */
export async function getUSDaily(symbol) {
  const { data } = await axios.get(`/api/market/stock/${encodeURIComponent(symbol)}`, {
    headers: authHeaders(),
  })
  return { labels: data.labels, prices: data.prices }
}

/** Forex daily prices — proxied through backend using user's stored AV key */
export async function getForexDaily(fromSymbol, toSymbol = 'USD') {
  const { data } = await axios.get(
    `/api/market/forex/${encodeURIComponent(fromSymbol)}/${encodeURIComponent(toSymbol)}`,
    { headers: authHeaders() },
  )
  return { labels: data.labels, prices: data.prices }
}

/** Crypto daily prices — proxied through backend, uses Binance public API (no key needed) */
export async function getKlines(symbol = 'BTCUSDT', limit = 60) {
  const { data } = await axios.get(`/api/market/crypto/${encodeURIComponent(symbol)}`, {
    params: { limit },
  })
  return {
    labels: data.labels.map(ts => new Date(Number(ts)).toLocaleDateString()),
    prices: data.prices,
  }
}

/** Taiwan stock daily prices — still proxied via Vite → TWSE (no key needed) */
export async function getTWSEDaily(stockNo) {
  const { data } = await axios.get('/twse/STOCK_DAY', {
    params: { response: 'json', date: '', stockNo },
  })
  return {
    labels: data.data.map(r => r[0]),
    prices: data.data.map(r => +r[6]),
  }
}