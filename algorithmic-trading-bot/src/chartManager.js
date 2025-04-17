import { renderCharts, renderBarCharts, renderCombinedCharts } from './chart.js'
import { fetchTradeVolume, fetchReturnLoss } from './api.js'

export async function updateCharts(selectedStocks, selectedCategory, selectedGraph) {
  try {
    for (const stock of selectedStocks) {
      // build the three canvas IDs that your template uses
      const priceId     = `${stock}${selectedGraph}StockPriceChart`;
      const volumeId    = `${stock}TradeVolumeChart`;
      const returnLossId= `${stock}ReturnLossChart`;

      const tradeVol    = await fetchTradeVolume(stock, selectedCategory);
      const retLoss     = await fetchReturnLoss(stock, selectedCategory);
      const priceSeries     = await fetchStockData(stock, selectedCategory)
      
      /* 1️⃣ price line + (temporary) volume bars — needs TWO IDs */
      renderCharts(priceId, volumeId, selectedGraph)

      renderCharts(priceId, volumeId, selectedGraph, priceSeries)   // supply data
      /* 2️⃣ overwrite the volume canvas with the nicer bar chart */
      renderBarCharts(priceId, tradeVol, selectedGraph);

      /* 3️⃣ draw the return‑vs‑loss line chart */
      renderCombinedCharts(returnLossId, retLoss, selectedGraph);
    }
  } catch (err) {
    console.error('Error updating charts:', err);
  }
}
