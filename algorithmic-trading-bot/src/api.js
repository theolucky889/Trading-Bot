export async function fetchStockData(selectedStocks, selectedCategory) {
  console.log(`Fetching stock data for ${selectedStocks} in category ${selectedCategory}`)
  // Replace with your actual API call logic
  return new Promise((resolve) => {
    setTimeout(() => {
      const data = selectedStocks.map(stock => ({
        symbol: stock,
        price: Math.random() * 1000, // Example random price
      }))
      console.log('Stock Data:', data)
      resolve(data)
    }, 500) // Simulate API call delay
  })
}

export async function fetchTradeVolume(stock, category) {
  console.log(`Fetching trade volume for ${stock} in category ${category}`)
  return new Promise((resolve) => {
    setTimeout(() => {
      const data = {
        labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5'],
        values: [1200, 1500, 1800, 1400, 2000], // Example data
      }
      console.log('Trade Volume Data:', data)
      resolve(data)
    }, 500) // Simulate API call delay
  })
}

export async function fetchReturnLoss(stock, category) {
  console.log(`Fetching return/loss for ${stock} in category ${category}`)
  return new Promise((resolve) => {
    setTimeout(() => {
      const data = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
        returnValues: [10, 15, 8, 12, 18], // Example return data
        lossValues: [-5, -2, -7, -3, -1], // Example loss data
      }
      console.log('Return/Loss Data:', data)
      resolve(data)
    }, 500) // Simulate API delay
  })
}
