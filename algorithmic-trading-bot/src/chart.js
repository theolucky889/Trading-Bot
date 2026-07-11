import Chart from 'chart.js/auto'
import { fetchHistory } from '@/api/history'

const chartInstances = {}

/**
 * Render the price + volume charts for one symbol using the project's own
 * /api/history endpoint (which routes by symbol shape: digits→TWSE,
 * USDT-suffix→Binance, else US, with graceful fallback + warning field).
 *
 * @returns {Promise<{warning: string|null, error: string|null}>}
 *   `warning` surfaces degraded/synthetic data; `error` is a fetch failure.
 */
export async function renderCharts(
  stockPriceChartId,
  volumeChartId,
  chartType = 'line',
  symbol,
  category, // kept for signature compatibility; backend routes by symbol shape
  days = 90
) {
  const priceCtx = document.getElementById(stockPriceChartId)?.getContext('2d')
  const volumeCtx = document.getElementById(volumeChartId)?.getContext('2d')
  if (!priceCtx || !volumeCtx) {
    console.error('canvas not found')
    return { warning: null, error: 'Chart canvas not found.' }
  }

  // 1️⃣ Destroy any existing charts (plain loop — no ASI trap).
  for (const id of [stockPriceChartId, volumeChartId]) {
    if (chartInstances[id]) {
      chartInstances[id].destroy()
      delete chartInstances[id]
    }
  }

  // 2️⃣ Fetch the price series from the internal history endpoint.
  let history
  try {
    history = await fetchHistory(symbol, days)
  } catch (err) {
    return { warning: null, error: err instanceof Error ? err.message : String(err) }
  }

  const candles = history.candles ?? []
  const labels = candles.map((c) => c.date)
  const prices = candles.map((c) => c.close)
  const volumes = candles.map((c) => c.volume)

  // 3️⃣ Price chart (line or bar, per toggle)
  chartInstances[stockPriceChartId] = new Chart(priceCtx, {
    type: chartType,
    data: {
      labels,
      datasets: [
        {
          label: `${symbol} price`,
          data: prices,
          borderColor: 'rgba(129, 140, 248, 1)',
          backgroundColor: 'rgba(129, 140, 248, .25)',
          borderWidth: 1,
          pointRadius: 0,
          fill: chartType !== 'line'
        }
      ]
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: '#d1d5db' } } },
      scales: {
        x: { ticks: { color: '#9ca3af', maxTicksLimit: 8 }, grid: { color: 'rgba(75,85,99,.2)' } },
        y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(75,85,99,.2)' } }
      }
    }
  })

  // 4️⃣ Volume chart (real volume from the same series).
  chartInstances[volumeChartId] = new Chart(volumeCtx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Volume',
          data: volumes,
          backgroundColor: 'rgba(75, 192, 192, .4)'
        }
      ]
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: '#d1d5db' } } },
      scales: {
        x: { ticks: { color: '#9ca3af', maxTicksLimit: 8 }, grid: { color: 'rgba(75,85,99,.2)' } },
        y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(75,85,99,.2)' } }
      }
    }
  })

  return { warning: history.warning ?? null, error: null }
}

/** Destroy every tracked chart instance (call on unmount). */
export function destroyAllCharts() {
  for (const id of Object.keys(chartInstances)) {
    chartInstances[id].destroy()
    delete chartInstances[id]
  }
}
