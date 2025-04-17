import { renderCharts } from './chart.js'
import { fetchStockData } from '@/api.js'

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
      const priceId = `${stock}${selectedGraph}StockPriceChart`
      const volumeId = `${stock}TradeVolumeChart`

      // Fetch price & volume data based on category
      // Market logic lives inside renderCharts via fetchStockData
      await renderCharts(
        priceId,
        volumeId,
        selectedGraph,
        stock,
        selectedCategory
      )
    }
  } catch (err) {
    console.error('updateCharts error:', err)
  }
}