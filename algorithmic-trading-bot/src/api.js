// src/api.js
export async function fetchStockData(symbols, category) {
  let apiUrl = ''

  if (category === 'crypto') {
    apiUrl = `https://api.binance.com/api/v3/ticker/price?symbol=${symbols[0]}`
  } else if (category === 'us-stocks') {
    apiUrl = `https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=${symbols[0]}&apikey=YOUR_ALPHA_VANTAGE_API_KEY`
  } else if (category === 'taiwan-stocks') {
    apiUrl = `https://twseapi.example.com/stock/${symbols[0]}`
  }

  try {
    const response = await fetch(apiUrl)
    const data = await response.json()
    console.log('Fetched Data:', data)
    return data
  } catch (error) {
    console.error('Error fetching stock data:', error)
    return null
  }
}
