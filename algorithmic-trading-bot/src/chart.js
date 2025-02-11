import axios from 'axios'
import Chart from 'chart.js/auto'

export async function renderCharts(stockPriceChartId, volumeChartId) {
  const stockPriceChart = document.getElementById(stockPriceChartId).getContext('2d')
  const volumeChart = document.getElementById(volumeChartId).getContext('2d')

  // Fetch data from Binance API
  const response = await axios.get('https://api.binance.com/api/v3/ticker/24hr')
  const data = response.data

  // Process data for charts
  const prices = data.map((item) => parseFloat(item.lastPrice))
  const volumes = data.map((item) => parseFloat(item.volume))

  // Create Stock Price Chart
  new Chart(stockPriceChart, {
    type: 'line',
    data: {
      labels: data.map((item) => item.symbol),
      datasets: [
        {
          label: 'Stock Price',
          data: prices,
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1,
          fill: false,
        },
      ],
    },
  })

  // Create Volume Chart
  new Chart(volumeChart, {
    type: 'bar',
    data: {
      labels: data.map((item) => item.symbol),
      datasets: [
        {
          label: 'Volume',
          data: volumes,
          backgroundColor: 'rgba(153, 102, 255, 0.2)',
          borderColor: 'rgba(153, 102, 255, 1)',
          borderWidth: 1,
        },
      ],
    },
  })
}
