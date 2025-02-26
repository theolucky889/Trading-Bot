import { renderCharts, renderBarCharts, renderCombinedCharts } from './chart.js'
import { fetchTradeVolume, fetchReturnLoss } from './api.js'

export async function updateCharts(selectedStocks, selectedCategory, selectedGraph) {
  try {
    console.log('Updating charts for:', selectedStocks, selectedCategory, selectedGraph)
    for (const stock of selectedStocks) {
      console.log(`Fetching data for stock: ${stock}`)
      const tradeVolumeData = await fetchTradeVolume(stock, selectedCategory)
      console.log('Trade Volume Data:', tradeVolumeData)
      const returnLossData = await fetchReturnLoss(stock, selectedCategory)
      console.log('Return/Loss Data:', returnLossData)

      renderCharts(`${stock}${selectedGraph}StockPriceChart`)
      renderBarCharts(`${stock}TradeVolumeChart`, tradeVolumeData)
      renderCombinedCharts(`${stock}ReturnLossChart`, returnLossData)
    }
  } catch (error) {
    console.error('Error updating charts:', error)
  }
}
