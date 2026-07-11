import { renderCharts, destroyAllCharts } from './chart.js'

/**
 * Redraw charts whenever the user changes stocks, category, or graph type.
 * Data comes from the project's own /api/history endpoint (see chart.js).
 *
 * @param {string[]} selectedStocks    array of symbols (e.g. ['AAPL', 'TSLA'])
 * @param {string}   selectedCategory  'us-stocks' | 'taiwan-stocks' | 'crypto'
 * @param {string}   selectedGraph     'line' | 'bar'
 * @returns {Promise<{warning: string|null, error: string|null}>}
 *   Aggregated warning/error across all rendered symbols, for the UI banner.
 */
export async function updateCharts(selectedStocks, selectedCategory, selectedGraph) {
  const warnings = []
  const errors = []

  for (const stock of selectedStocks) {
    // IDs that match the <canvas> elements in DashboardView.vue
    const priceId = `${stock}${selectedGraph}StockPriceChart`
    const volumeId = `${stock}TradeVolumeChart`

    const { warning, error } = await renderCharts(
      priceId,
      volumeId,
      selectedGraph,
      stock,
      selectedCategory
    )

    if (warning) warnings.push(`${stock}: ${warning}`)
    if (error) errors.push(`${stock}: ${error}`)
  }

  return {
    warning: warnings.length ? warnings.join(' · ') : null,
    error: errors.length ? errors.join(' · ') : null
  }
}

export { destroyAllCharts }
