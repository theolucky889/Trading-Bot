document.addEventListener("DOMContentLoaded", function () {
    const app = Vue.createApp({
      data() {
        return {
          binanceData: null,
          botStatus: "Bot is running..."
        };
      },
      mounted() {
        this.fetchBinanceData();
      },
      methods: {
        fetchBinanceData() {
          axios.get('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT')
            .then(response => {
              this.binanceData = response.data;
              document.getElementById('binance-data').innerHTML = `BTC Price: $${this.binanceData.lastPrice}`;
            })
            .catch(error => {
              console.error("Error fetching Binance data:", error);
            });
        },
        toggleBotStatus() {
          if (this.botStatus === "Bot is running...") {
            this.botStatus = "Bot is stopped.";
          } else {
            this.botStatus = "Bot is running...";
          }
          document.getElementById('bot-status').innerText = this.botStatus;
        }
      }
    });
    
    const vm = app.mount("#app");
  
    // Event listeners
    document.getElementById('start-btn').addEventListener('click', () => {
      vm.toggleBotStatus();
    });
  
    document.getElementById('stop-btn').addEventListener('click', () => {
      vm.toggleBotStatus();
    });
  
    document.getElementById('refresh-btn').addEventListener('click', () => {
      vm.fetchBinanceData();
    });
  
    document.getElementById('save-settings').addEventListener('click', () => {
      const apiKey = document.getElementById('api-key').value;
      const apiSecret = document.getElementById('api-secret').value;
      alert(`Settings saved for API Key: ${apiKey} and API Secret: ${apiSecret}`);
    });
  });
  