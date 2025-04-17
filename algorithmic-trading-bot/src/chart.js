import Chart from 'chart.js/auto'
import { getUSDaily, getTWSEDaily, getKlines } from '@/api/quotes.js'

const chartInstances = {}

export async function renderCharts(
  stockPriceChartId,
  volumeChartId,
  chartType = 'line',
  symbol,
  category
) {
  const priceCtx  = document.getElementById(stockPriceChartId)?.getContext('2d')
  const volumeCtx = document.getElementById(volumeChartId)?.getContext('2d')
  if (!priceCtx || !volumeCtx) return console.error('canvas not found')

  // 1️⃣ Destroy any existing charts
  [stockPriceChartId, volumeChartId].forEach(id => {
    if (chartInstances[id]) chartInstances[id].destroy()
  })

  // 2️⃣ Fetch the correct price series
  let series
  switch (category) {
    case 'us-stocks':     series = await getUSDaily(symbol);   break
    case 'taiwan-stocks': series = await getTWSEDaily(symbol); break
    default:              series = await getKlines(symbol);    break
  }

  // 3️⃣ Price chart (line or bar, per toggle)
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

  // 4️⃣ Volume placeholder – you can call a real volume endpoint here
  chartInstances[volumeChartId] = new Chart(volumeCtx, {
    type: 'bar',
    data: {
      labels: series.labels,
      datasets: [
        { label: 'Volume', data: Array(series.labels.length).fill(0) }
      ]
    }
  })
}
