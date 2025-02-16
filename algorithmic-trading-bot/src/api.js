export async function fetchTradeVolume(stock, category) {
  // Replace with your actual API call
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5'],
        values: [1200, 1500, 1800, 1400, 2000], // Example data
      })
    }, 500) // Simulate API call delay
  })
}

export async function fetchReturnLoss(stock, category) {
  // Replace with your actual API call.  Example data:
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
        returnValues: [10, 15, 8, 12, 18], // Example return data
        lossValues: [-5, -2, -7, -3, -1], // Example loss data
      })
    }, 500) // Simulate API delay
  })
}
