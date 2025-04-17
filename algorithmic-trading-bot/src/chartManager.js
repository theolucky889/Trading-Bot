import { renderCharts, renderBarCharts, renderCombinedCharts } from './chart.js'
import { fetchTradeVolume } from './api.js'

export async function updateCharts(selectedStocks, selectedCategory, selectedGraph) {
  try {
    for (const stock of selectedStocks) {
      const priceId  = `${stock}${selectedGraph}StockPriceChart`
      const volumeId = `${stock}TradeVolumeChart`

      const tradeVol    = await fetchTradeVolume(stock, selectedCategory);

      /* 1️⃣ price line + (temporary) volume bars — needs TWO IDs */
      renderCharts(priceId, volumeId, selectedGraph, stock, selectedCategory)

      /* 2️⃣ overwrite the volume canvas with the nicer bar chart */
      renderBarCharts(priceId, tradeVol, selectedGraph);

    }
  } catch (err) {
    console.error('Error updating charts:', err);
  }
}
