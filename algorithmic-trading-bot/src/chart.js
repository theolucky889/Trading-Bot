import axios from 'axios'
import Chart from 'chart.js/auto'

// Store chart instances to manage them
const chartInstances = {}

export async function renderCharts(stockPriceChartId, volumeChartId, chartType='line') {
  const stockPriceChartElement = document.getElementById(stockPriceChartId)
  const volumeChartElement = document.getElementById(volumeChartId)

  console.log('Stock Price Chart Element:', stockPriceChartElement)
  console.log('Volume Chart Element:', volumeChartElement)

  if (!stockPriceChartElement || !volumeChartElement) {
    console.error('Canvas elements not found')
    return
  }

  const stockPriceChart = stockPriceChartElement.getContext('2d')
  const volumeChart = volumeChartElement.getContext('2d')

  // Destroy existing charts if they exist
  if (chartInstances[stockPriceChartId]) {
    chartInstances[stockPriceChartId].destroy()
  }
  if (chartInstances[volumeChartId]) {
    chartInstances[volumeChartId].destroy()
  }

  // Fetch data from Binance API
  const response = await axios.get('https://api.binance.com/api/v3/ticker/24hr')
  const data = response.data

  // Process data for charts
  const prices = data.map((item) => parseFloat(item.lastPrice))
  const volumes = data.map((item) => parseFloat(item.volume))

  // Create Stock Price Chart
  chartInstances[stockPriceChartId] = new Chart(stockPriceChart, {
    type: chartType,
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
  chartInstances[volumeChartId] = new Chart(volumeChart, {
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
  const canvasElement = document.getElementById(chartId)
  console.log('Canvas Element for Bar Chart:', canvasElement)

  if (!canvasElement) {
    console.error('Canvas element not found for ID:', chartId)
    return
  }

  if (chartInstances[chartId]) {
    chartInstances[chartId].destroy()
  }

  const context = canvasElement.getContext('2d')
  if (!context) {
    console.error('Failed to acquire context for canvas ID:', chartId)
    return
  }

  chartInstances[chartId] = new Chart(context, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [
        {
          label: 'Trade Volume',
          data: data.values,
          backgroundColor: 'rgba(54, 162, 235, 0.8)',
        },
      ],
    },
  })
}

export function renderCombinedCharts(chartId, data) {
  const canvasElement = document.getElementById(chartId)
  console.log('Canvas Element for Combined Chart:', canvasElement)

  if (!canvasElement) {
    console.error('Canvas element not found for ID:', chartId)
    return
  }

  if (chartInstances[chartId]) {
    chartInstances[chartId].destroy()
  }

  const context = canvasElement.getContext('2d')
  if (!context) {
    console.error('Failed to acquire context for canvas ID:', chartId)
    return
  }

  chartInstances[chartId] = new Chart(context, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [
        {
          label: 'Return',
          data: data.returnValues,
          borderColor: 'green',
          fill: false,
        },
        {
          label: 'Loss',
          data: data.lossValues,
          borderColor: 'red',
          fill: false,
        },
      ],
    },
  })
}
