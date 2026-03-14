import Chart from 'chart.js/auto'
import { getUSDaily, getTWSEDaily, getKlines } from '@/api/quotes.js'
import { fetchReturnLoss } from '@/api.js'

const chartInstances = {}

export async function renderCharts(
  stockPriceChartId,
  volumeChartId,
  returnLossChartId,
  chartType = 'line',
  symbol,
  category
) {
  const priceCtx      = document.getElementById(stockPriceChartId)?.getContext('2d')
  const volumeCtx     = document.getElementById(volumeChartId)?.getContext('2d')
  const returnLossCtx = document.getElementById(returnLossChartId)?.getContext('2d')
  if (!priceCtx || !volumeCtx) return console.error('canvas not found')

  // Destroy any existing charts
  [stockPriceChartId, volumeChartId, returnLossChartId].forEach(id => {
    if (chartInstances[id]) chartInstances[id].destroy()
  })

  // Fetch the correct price series
  let series
  switch (category) {
    case 'us-stocks':     series = await getUSDaily(symbol);   break
    case 'taiwan-stocks': series = await getTWSEDaily(symbol); break
    default:              series = await getKlines(symbol);    break
  }

  // Price chart (line or bar, per toggle)
  chartInstances[stockPriceChartId] = new Chart(priceCtx, {
    type: chartType,
    data: {
      labels: series.labels,
      datasets: [
        {
          label: `${symbol} price`,
          data: series.prices,
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, .25)',
          borderWidth: 1,
          fill: chartType !== 'line'
        }
      ]
    }
  })

  // Volume placeholder
  chartInstances[volumeChartId] = new Chart(volumeCtx, {
    type: 'bar',
    data: {
      labels: series.labels,
      datasets: [
        { label: 'Volume', data: Array(series.labels.length).fill(0) }
      ]
    }
  })

  // Return/Loss chart
  if (returnLossCtx) {
    const rl = await fetchReturnLoss(symbol, category)
    chartInstances[returnLossChartId] = new Chart(returnLossCtx, {
      type: 'bar',
      data: {
        labels: rl.labels,
        datasets: [
          {
            label: 'Return',
            data: rl.returnValues,
            backgroundColor: 'rgba(74, 222, 128, 0.6)'
          },
          {
            label: 'Loss',
            data: rl.lossValues,
            backgroundColor: 'rgba(248, 113, 113, 0.6)'
          }
        ]
      }
    })
  }
}