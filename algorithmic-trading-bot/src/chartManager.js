import { renderCharts } from './chart.js'

/**
 * Redraw charts whenever the user changes stocks, category, or graph type
 *
 * @param {string[]} selectedStocks    array of symbols (e.g. ['AAPL', 'TSLA'])
 * @param {string}   selectedCategory  'us-stocks' | 'taiwan-stocks' | 'crypto'
 * @param {string}   selectedGraph     'line' | 'bar'
 */
export async function updateCharts(selectedStocks, selectedCategory, selectedGraph) {
  try {
    for (const stock of selectedStocks) {
      // IDs that match the <canvas> elements in Dashboard.vue
      const priceId      = `${stock}${selectedGraph}StockPriceChart`
      const volumeId     = `${stock}TradeVolumeChart`
      const returnLossId = `${stock}ReturnLossChart`

      await renderCharts(
        priceId,
        volumeId,
        returnLossId,
        selectedGraph,
        stock,
        selectedCategory
      )
    }
  } catch (err) {
    console.error('updateCharts error:', err)
  }
}