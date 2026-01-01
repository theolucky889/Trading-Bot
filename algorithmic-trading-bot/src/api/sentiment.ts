export type SentimentLabel = 'positive' | 'neutral' | 'negative'

export type SentimentSummary = {
  positive: number
  neutral: number
  negative: number
  avg_compound: number
}

export type SentimentArticle = {
  title: string
  link: string
  source?: string
  published?: string
  excerpt?: string
  compound: number
  label: SentimentLabel
}

export type SentimentResult = {
  query: string
  model: string
  generated_at: string
  summary: SentimentSummary
  articles: SentimentArticle[]
  warning?: string
}

// Supports your current call style:
// fetchMarketSentiment(query, numArticles, model)
export async function fetchMarketSentiment(
  query: string,
  numArticles = 10,
  model = 'vader'
): Promise<SentimentResult> {
  const url =
    `/api/sentiment?query=${encodeURIComponent(query)}` +
    `&num_articles=${encodeURIComponent(numArticles)}` +
    `&model=${encodeURIComponent(model)}`

  try {
    const res = await fetch(url, { headers: { Accept: 'application/json' } })
    if (!res.ok) throw new Error(`Sentiment API failed: ${res.status} ${res.statusText}`)
    return await res.json()
  } catch (e) {
    // fallback mock for UI
    const now = new Date().toISOString()
    const articles: SentimentArticle[] = [
      { title: 'Mock: ETF inflows rebound', link: 'https://example.com/1', source: 'Mock', published: now, compound: 0.42, label: 'positive' },
      { title: 'Mock: Market waits for macro data', link: 'https://example.com/2', source: 'Mock', published: now, compound: 0.02, label: 'neutral' },
      { title: 'Mock: Risk-off into event risk', link: 'https://example.com/3', source: 'Mock', published: now, compound: -0.31, label: 'negative' },
    ]
    const positive = articles.filter(a => a.label === 'positive').length
    const neutral  = articles.filter(a => a.label === 'neutral').length
    const negative = articles.filter(a => a.label === 'negative').length
    const avg_compound = Number((articles.reduce((s,a)=>s+a.compound,0)/articles.length).toFixed(4))

    return {
      query,
      model,
      generated_at: now,
      summary: { positive, neutral, negative, avg_compound },
      articles,
      warning: 'Backend not reachable — showing mock data.'
    }
  }
}
