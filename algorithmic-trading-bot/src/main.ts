import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
// import VTooltip from './v-tooltip'

const app = createApp(App)

app.use(router)
// app.use(VTooltip)

app.mount('#app')
