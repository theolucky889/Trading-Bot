<template>
  <div class="w-full">
    <div class="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div class="flex flex-col gap-2 w-full">
        <label class="text-sm font-medium text-gray-700">Query (multi supported)</label>
        <textarea
          v-model="queryText"
          rows="2"
          placeholder="BTC, TSLA, gold price... (comma or new line separated)"
          class="w-full rounded-lg border border-gray-300 px-3 py-2 outline-none focus:ring"
        />
        <div class="text-xs text-gray-500">
          Detected: <span class="font-medium text-gray-700">{{ parsedQueries.length }}</span>
          query{{ parsedQueries.length === 1 ? '' : 'ies' }}
        </div>

        <div v-if="parsedQueries.length > 0" class="flex flex-wrap gap-2">
          <span
            v-for="(q, i) in parsedQueries"
            :key="q + i"
            class="rounded-full border border-gray-200 bg-white px-2 py-1 text-xs text-gray-700"
          >
            {{ q }}
          </span>
        </div>
      </div>

      <div class="flex flex-row flex-wrap gap-3">
        <div class="flex flex-col gap-2">
          <label class="text-sm font-medium text-gray-700">Articles</label>
          <select
            v-model.number="numArticles"
            class="rounded-lg border border-gray-300 px-3 py-2 outline-none focus:ring"
          >
            <option :value="5">5</option>
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="30">30</option>
          </select>
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-sm font-medium text-gray-700">Model</label>
          <select v-model="model" class="rounded-lg border border-gray-300 px-3 py-2 outline-none focus:ring">
            <option value="vader">VADER</option>
            <option value="finbert">FinBERT (optional)</option>
          </select>
        </div>

        <button
          @click="runAll()"
          class="h-10 rounded-lg bg-black px-4 py-2 text-white hover:opacity-90 disabled:opacity-50"
          :disabled="loading || parsedQueries.length === 0"
          title="Analyze all detected queries"
        >
          <span v-if="loading">Analyzing...</span>
          <span v-else>Analyze</span>
        </button>
      </div>
    </div>

    <p v-if="error" class="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
      {{ error }}
    </p>
    <p v-else-if="warning" class="mt-3 rounded-lg bg-yellow-50 px-3 py-2 text-sm text-yellow-800">
      {{ warning }}
    </p>

    <!-- ✅ History -->
    <div class="mt-4 rounded-xl border border-gray-200 bg-white">
      <div class="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <div class="flex flex-col">
          <div class="font-semibold">My Recent Searches</div>
          <div class="text-xs text-gray-500">Click an item to re-run</div>
        </div>

        <button
          @click="loadHistory()"
          class="rounded-lg border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50 disabled:opacity-50"
          :disabled="historyLoading"
        >
          <span v-if="historyLoading">Refreshing...</span>
          <span v-else>Refresh</span>
        </button>
      </div>

      <div v-if="historyError" class="px-4 py-3 text-sm text-gray-600">
        {{ historyError }}
      </div>

      <div v-else-if="historyLoading" class="px-4 py-3 text-sm text-gray-600">
        Loading...
      </div>

      <div v-else-if="history.length === 0" class="px-4 py-3 text-sm text-gray-500">
        No history yet.
      </div>

      <ul v-else class="divide-y divide-gray-100">
        <li
          v-for="item in history.slice(0, 10)"
          :key="item._id"
          class="cursor-pointer px-4 py-3 hover:bg-gray-50"
          @click="rerunFromHistory(item)"
          title="Click to re-run this search"
        >
          <div class="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
            <div class="font-medium">{{ item.query }}</div>
            <div class="text-xs text-gray-500">
              {{ item.model }} • {{ formatTime(pickHistoryTime(item)) }}
            </div>
          </div>

          <div class="mt-1 text-xs text-gray-500">
            Avg: {{ item.summary?.avg_compound ?? '-' }}
            • +{{ item.summary?.positive ?? 0 }}
            / ={{ item.summary?.neutral ?? 0 }}
            / -{{ item.summary?.negative ?? 0 }}
          </div>
        </li>
      </ul>
    </div>

    <!-- ✅ Multi-result list -->
    <div v-if="results.length > 0" class="mt-4 rounded-xl border border-gray-200 bg-white">
      <div class="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <div class="font-semibold">Results</div>
        <div class="text-xs text-gray-500">
          {{ results.length }} quer{{ results.length === 1 ? 'y' : 'ies' }}
          • selected: {{ selectedResult?.query }}
        </div>
      </div>

      <ul class="divide-y divide-gray-100">
        <li
          v-for="(r, idx) in results"
          :key="r.query + idx"
          class="cursor-pointer px-4 py-3 hover:bg-gray-50"
          :class="idx === selectedIndex ? 'bg-gray-50' : ''"
          @click="selectedIndex = idx"
        >
          <div class="flex items-center justify-between">
            <div class="font-medium">{{ r.query }}</div>
            <div class="text-xs text-gray-500">
              Avg: {{ r.summary.avg_compound }} • +{{ r.summary.positive }}/={{ r.summary.neutral }}/-{{ r.summary.negative }}
            </div>
          </div>
          <div class="mt-1 text-xs text-gray-500">
            {{ r.articles.length }} articles • {{ r.model }} • {{ formatTime(r.generated_at) }}
          </div>
        </li>
      </ul>
    </div>

    <!-- ✅ Summary cards for selected result -->
    <div v-if="selectedResult" class="mt-4 grid grid-cols-1 gap-3 md:grid-cols-4">
      <div class="rounded-xl border border-gray-200 bg-white p-4">
        <div class="text-xs text-gray-500">Avg compound</div>
        <div class="mt-1 text-2xl font-semibold">{{ selectedResult.summary.avg_compound }}</div>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-4">
        <div class="text-xs text-gray-500">Positive</div>
        <div class="mt-1 text-2xl font-semibold">{{ selectedResult.summary.positive }}</div>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-4">
        <div class="text-xs text-gray-500">Neutral</div>
        <div class="mt-1 text-2xl font-semibold">{{ selectedResult.summary.neutral }}</div>
      </div>
      <div class="rounded-xl border border-gray-200 bg-white p-4">
        <div class="text-xs text-gray-500">Negative</div>
        <div class="mt-1 text-2xl font-semibold">{{ selectedResult.summary.negative }}</div>
      </div>
    </div>

    <!-- ✅ Articles for selected result -->
    <div v-if="selectedResult" class="mt-4 rounded-xl border border-gray-200 bg-white">
      <div class="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <div class="font-semibold">Articles</div>
        <div class="text-xs text-gray-500">
          {{ selectedResult.articles.length }} results • {{ selectedResult.model }} •
          {{ formatTime(selectedResult.generated_at) }}
        </div>
      </div>

      <div v-if="selectedResult.articles.length === 0" class="px-4 py-6 text-gray-500">
        No articles found.
      </div>

      <ul v-else class="divide-y divide-gray-100">
        <li v-for="(a, idx) in selectedResult.articles" :key="idx" class="px-4 py-3">
          <div class="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
            <a :href="a.link" target="_blank" rel="noreferrer" class="font-medium hover:underline">
              {{ a.title }}
            </a>

            <div class="flex items-center gap-2">
              <span class="rounded-full px-2 py-0.5 text-xs font-medium" :class="badgeClass(a.label)">
                {{ a.label }}
              </span>
              <span class="text-xs text-gray-500">{{ a.compound }}</span>
            </div>
          </div>

          <div class="mt-1 text-xs text-gray-500">
            <span v-if="a.source">{{ a.source }}</span>
            <span v-if="a.published"> • {{ formatTime(a.published) }}</span>
          </div>

          <p v-if="a.excerpt" class="mt-2 text-sm text-gray-700 line-clamp-3">
            {{ a.excerpt }}
          </p>
        </li>
      </ul>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, ref } from 'vue'
import { fetchMarketSentiment } from '@/api/sentiment'

type SentimentSummary = {
  positive: number
  neutral: number
  negative: number
  avg_compound: number
}

type SentimentArticle = {
  title: string
  link: string
  source?: string
  published?: string
  excerpt?: string
  compound: number
  label: 'positive' | 'neutral' | 'negative'
}

type SentimentResult = {
  query: string
  model: string
  generated_at: string
  summary: SentimentSummary
  articles: SentimentArticle[]
  warning?: string
}

type SentimentRunHistoryItem = {
  _id: string
  query: string
  model: string
  numArticles?: number
  generatedAt?: string
  createdAt?: string
  summary?: SentimentSummary
}

export default defineComponent({
  name: 'SentimentEngine',
  setup() {
    // ✅ Multi-query input
    const queryText = ref('BTC')
    const numArticles = ref(10)
    const model = ref('vader')

    const loading = ref(false)
    const error = ref('')
    const warning = ref('')

    // ✅ Multi results + selection
    const results = ref<SentimentResult[]>([])
    const selectedIndex = ref(0)

    const selectedResult = computed(() => results.value[selectedIndex.value] || null)

    const parsedQueries = computed(() => {
      const raw = queryText.value || ''
      // split by newline or comma
      const parts = raw
        .split(/[\n,]+/g)
        .map((s) => s.trim())
        .filter(Boolean)

      // dedupe while preserving order
      const seen = new Set<string>()
      const out: string[] = []
      for (const p of parts) {
        const key = p.toLowerCase()
        if (!seen.has(key)) {
          seen.add(key)
          out.push(p)
        }
      }
      return out.slice(0, 10) // safety limit
    })

    // History
    const history = ref<SentimentRunHistoryItem[]>([])
    const historyLoading = ref(false)
    const historyError = ref('')

    const loadHistory = async () => {
      historyError.value = ''
      historyLoading.value = true
      try {
        const token = localStorage.getItem('auth_token')
        if (!token) {
          history.value = []
          historyError.value = 'Login to see your history.'
          return
        }

        const res = await fetch('/api/sentiment/history', {
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: 'application/json',
          },
        })

        if (!res.ok) {
          const text = await res.text().catch(() => '')
          throw new Error(`History API failed: ${res.status} ${res.statusText} ${text}`.trim())
        }

        history.value = await res.json()
      } catch (e: any) {
        historyError.value = e?.message || 'Failed to load history'
      } finally {
        historyLoading.value = false
      }
    }

    const runAll = async () => {
      error.value = ''
      warning.value = ''
      loading.value = true

      const qs = parsedQueries.value
      if (qs.length === 0) {
        error.value = 'Please enter at least one query.'
        loading.value = false
        return
      }

      try {
        // Run sequentially (more stable) — change to Promise.all if you want parallel
        const out: SentimentResult[] = []
        for (const q of qs) {
          const data = await fetchMarketSentiment(q, numArticles.value, model.value)
          out.push(data)
          if (data?.warning) warning.value = data.warning
        }

        results.value = out
        selectedIndex.value = 0

        // refresh history after runs (if logged in)
        await loadHistory()
      } catch (e: any) {
        error.value = e?.message || 'Failed to fetch sentiment'
      } finally {
        loading.value = false
      }
    }

    // UX: click history item to re-run (as single query)
    const rerunFromHistory = async (item: SentimentRunHistoryItem) => {
      queryText.value = item.query
      model.value = item.model || 'vader'
      if (typeof item.numArticles === 'number' && item.numArticles > 0) {
        numArticles.value = item.numArticles
      }
      await runAll()
    }

    const badgeClass = (label: string) => {
      if (label === 'positive') return 'bg-green-50 text-green-700 border border-green-200'
      if (label === 'negative') return 'bg-red-50 text-red-700 border border-red-200'
      return 'bg-gray-50 text-gray-700 border border-gray-200'
    }

    const formatTime = (iso: string) => {
      try {
        return new Date(iso).toLocaleString()
      } catch {
        return iso
      }
    }

    const pickHistoryTime = (item: SentimentRunHistoryItem) => {
      return item.generatedAt || item.createdAt || ''
    }

    // initial loads
    runAll()
    loadHistory()

    return {
      queryText,
      parsedQueries,
      numArticles,
      model,

      loading,
      error,
      warning,

      results,
      selectedIndex,
      selectedResult,

      runAll,

      badgeClass,
      formatTime,

      history,
      historyLoading,
      historyError,
      loadHistory,
      pickHistoryTime,
      rerunFromHistory,
    }
  },
})
</script>
