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

export function renderBarCharts(chartId, data) {
  new Chart(document.getElementById(chartId), {
    type: 'bar',
    data: {
      labels: data.labels, // Example: ['Day 1', 'Day 2', ...]
      datasets: [
        {
          label: 'Trade Volume',
          data: data.values, // Example: [1200, 1500, ...]
          backgroundColor: 'rgba(54, 162, 235, 0.8)', // Example color
        },
      ],
    },
    // ... other chart options
  })
}

export function renderCombinedCharts(chartId, data) {
  new Chart(document.getElementById(chartId), {
    type: 'line', // Use 'line' for Return/Loss
    data: {
      labels: data.labels, // Your x-axis labels (e.g., dates)
      datasets: [
        {
          label: 'Return',
          data: data.returnValues, // Your return data points
          borderColor: 'green',
          fill: false,
        },
        {
          label: 'Loss',
          data: data.lossValues, // Your loss data points
          borderColor: 'red',
          fill: false,
        },
      ],
    },
    // ... other options for the chart
  }).render()
}
