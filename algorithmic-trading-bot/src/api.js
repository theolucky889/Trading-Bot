/* ──────────────────────────────────────────
   1.  Price helpers per market
   ────────────────────────────────────────── */
   const AV_KEY = import.meta.env.VITE_ALPHA_KEY

   // ▸ US‑listed equities via Alpha Vantage
   async function getUSPrice(symbol) {
     const url = `/av/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=${symbol}&apikey=${AV_KEY}&outputsize=compact`
     const json = await fetch(url).then(r => r.json())
     const series = json['Time Series (Daily)'] ?? {}
     const labels = Object.keys(series).slice(0, 30).reverse()      // newest → oldest
     const prices = labels.map(d => +series[d]['5. adjusted close'])
     return { labels, prices }
   }
   
   // ▸ TWSE equities (average close of latest day)
   async function getTWPrice(stockNo) {
     const url = `/twse/STOCK_DAY_AVG_ALL`
     const list = await fetch(url).then(r => r.json())
     const row  = list.find(x => x.Code === stockNo)
     if (!row) throw new Error(`TWSE: symbol ${stockNo} not found`)
     return { labels: [row.Date], prices: [+row.Close] }
   }
   
   // ▸ Crypto (latest lastPrice)
   async function getCryptoPrice(symbol = 'BTCUSDT') {
     const url = `https://api.binance.com/api/v3/ticker/24hr`
     const list = await fetch(url).then(r => r.json())
     const row  = list.find(x => x.symbol === symbol)
     if (!row) throw new Error(`Binance: symbol ${symbol} not found`)
     return { labels: [row.symbol], prices: [+row.lastPrice] }
   }
   
   /* ──────────────────────────────────────────
      2.  Unified entry point for chartManager
      ────────────────────────────────────────── */
   export async function fetchStockData(symbol, category) {
     switch (category) {
       case 'us-stocks':
         return getUSPrice(symbol)
       case 'taiwan-stocks':
         return getTWPrice(symbol)
       default:              // 'crypto'
         return getCryptoPrice(symbol)
     }
   }
   
   /* ──────────────────────────────────────────
      3.  Volume and Return/Loss mocks
      ────────────────────────────────────────── */
   // TODO: replace these with real endpoints when available
   export async function fetchTradeVolume(symbol, category) {
     return {
       labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5'],
       values: [1200, 1500, 1800, 1400, 2000]
     }
   }
   
   export async function fetchReturnLoss(symbol, category) {
     return {
       labels:       ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
       returnValues: [ 10,   15,     8,    12,    18 ],
       lossValues:   [ -5,   -2,    -7,    -3,    -1 ]
     }
   }
   