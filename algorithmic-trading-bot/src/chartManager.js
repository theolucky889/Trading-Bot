import { renderCharts, renderBarCharts, renderCombinedCharts } from './chart.js'
import { fetchStockData, fetchTradeVolume, fetchReturnLoss } from './api.js'

export async function updateCharts(selectedStocks, selectedCategory, selectedGraph) {
  try {
    await fetchStockData(selectedStocks, selectedCategory)
    for (const stock of selectedStocks) {
      const tradeVolumeData = await fetchTradeVolume(stock, selectedCategory)
      const returnLossData = await fetchReturnLoss(stock, selectedCategory)

      renderCharts(`${stock}${selectedGraph}StockPriceChart`)
      renderBarCharts(`${stock}TradeVolumeChart`, tradeVolumeData)
      renderCombinedCharts(`${stock}ReturnLossChart`, returnLossData)
    }
  } catch (error) {
    console.error('Error updating charts:', error)
  }
}
