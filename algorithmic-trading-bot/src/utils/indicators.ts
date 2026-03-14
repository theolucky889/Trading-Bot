// ── Technical Indicator Library ────────────────────────────────────────────────

/** Exponential Moving Average */
export function ema(prices: number[], period: number): number[] {
  if (prices.length < period) return []
  const k = 2 / (period + 1)
  let val = prices.slice(0, period).reduce((a, b) => a + b) / period
  const result: number[] = [val]
  for (let i = period; i < prices.length; i++) {
    val = prices[i] * k + val * (1 - k)
    result.push(val)
  }
  return result
}

/** Simple Moving Average */
export function sma(prices: number[], period: number): number[] {
  const result: number[] = []
  for (let i = period - 1; i < prices.length; i++) {
    const slice = prices.slice(i - period + 1, i + 1)
    result.push(slice.reduce((a, b) => a + b) / period)
  }
  return result
}

/** Relative Strength Index (Wilder smoothing) */
export function rsi(prices: number[], period = 14): number[] {
  if (prices.length < period + 1) return []
  const result: number[] = []
  let gains = 0
  let losses = 0

  for (let i = 1; i <= period; i++) {
    const d = prices[i] - prices[i - 1]
    if (d > 0) gains += d
    else losses -= d
  }

  let avgGain = gains / period
  let avgLoss = losses / period

  for (let i = period; i < prices.length; i++) {
    if (i > period) {
      const d = prices[i] - prices[i - 1]
      avgGain = (avgGain * (period - 1) + (d > 0 ? d : 0)) / period
      avgLoss = (avgLoss * (period - 1) + (d < 0 ? -d : 0)) / period
    }
    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss
    result.push(100 - 100 / (1 + rs))
  }
  return result
}

/** MACD (line, signal, histogram) */
export function macd(
  prices: number[],
  fast = 12,
  slow = 26,
  signalPeriod = 9,
): { line: number[]; signal: number[]; histogram: number[] } {
  const emaFast = ema(prices, fast)
  const emaSlow = ema(prices, slow)
  const offset = slow - fast
  const line = emaSlow.map((v, i) => emaFast[i + offset] - v)
  const signal = ema(line, signalPeriod)
  const signalOffset = signalPeriod - 1
  const histogram = signal.map((v, i) => line[i + signalOffset] - v)
  return { line, signal, histogram }
}

/** Bollinger Bands (middle SMA ± k×stddev) */
export function bollingerBands(
  prices: number[],
  period = 20,
  k = 2,
): { upper: number[]; middle: number[]; lower: number[] } {
  const upper: number[] = []
  const middle: number[] = []
  const lower: number[] = []
  for (let i = period - 1; i < prices.length; i++) {
    const slice = prices.slice(i - period + 1, i + 1)
    const mean = slice.reduce((a, b) => a + b) / period
    const std = Math.sqrt(slice.reduce((s, p) => s + (p - mean) ** 2, 0) / period)
    middle.push(mean)
    upper.push(mean + k * std)
    lower.push(mean - k * std)
  }
  return { upper, middle, lower }
}

/** Average True Range (simplified — daily closes only, no high/low) */
export function atr(prices: number[], period = 14): number {
  const trs = prices.slice(1).map((p, i) => Math.abs(p - prices[i]))
  if (trs.length < period) return prices[prices.length - 1] * 0.02
  return trs.slice(-period).reduce((a, b) => a + b) / period
}

// ── Signal Generation ──────────────────────────────────────────────────────────

export type SignalAction = 'STRONG BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG SELL'

export interface TradingSignal {
  action: SignalAction
  confidence: number       // 0–100
  rsiValue: number
  emaAlignment: 'bullish' | 'bearish' | 'mixed'
  macdBullish: boolean
  bbZone: 'oversold' | 'neutral' | 'overbought'
  riskScore: number        // 1–10 (1 = lowest risk)
  entryPrice: number
  stopLoss: number
  takeProfit: number
  riskRewardRatio: number
  reasons: { text: string; bullish: boolean }[]
  rawScore: number         // -6..6
}

export function generateSignal(prices: number[]): TradingSignal {
  const n = prices.length
  const current = prices[n - 1]

  // ── Indicators ────────────────────────────────────────────────────────────
  const rsiArr = rsi(prices, 14)
  const rsiVal = rsiArr.length > 0 ? rsiArr[rsiArr.length - 1] : 50

  const ema9 = ema(prices, 9)
  const ema21 = ema(prices, Math.min(21, n - 1))
  const ema50 = ema(prices, Math.min(50, n - 1))
  const lastE9 = ema9[ema9.length - 1] ?? current
  const lastE21 = ema21[ema21.length - 1] ?? current
  const lastE50 = ema50[ema50.length - 1] ?? current

  const { histogram } = macd(prices)
  const lastHist = histogram[histogram.length - 1] ?? 0
  const prevHist = histogram[histogram.length - 2] ?? 0

  const bb = bollingerBands(prices, Math.min(20, n))
  const bbUpper = bb.upper[bb.upper.length - 1] ?? current * 1.04
  const bbLower = bb.lower[bb.lower.length - 1] ?? current * 0.96
  const bbMid = bb.middle[bb.middle.length - 1] ?? current

  const atrVal = atr(prices, 14)

  // ── Scoring ───────────────────────────────────────────────────────────────
  let score = 0
  const reasons: TradingSignal['reasons'] = []

  // RSI
  if (rsiVal < 30) {
    score += 2
    reasons.push({ text: `RSI ${rsiVal.toFixed(1)} — oversold, high probability bounce`, bullish: true })
  } else if (rsiVal < 45) {
    score += 1
    reasons.push({ text: `RSI ${rsiVal.toFixed(1)} — mildly oversold`, bullish: true })
  } else if (rsiVal > 70) {
    score -= 2
    reasons.push({ text: `RSI ${rsiVal.toFixed(1)} — overbought, pullback risk`, bullish: false })
  } else if (rsiVal > 60) {
    score -= 1
    reasons.push({ text: `RSI ${rsiVal.toFixed(1)} — approaching overbought`, bullish: false })
  } else {
    score += 0.5
    reasons.push({ text: `RSI ${rsiVal.toFixed(1)} — healthy mid-range zone`, bullish: true })
  }

  // EMA alignment
  const emaAlignment: TradingSignal['emaAlignment'] =
    lastE9 > lastE21 && lastE21 > lastE50 ? 'bullish' :
    lastE9 < lastE21 && lastE21 < lastE50 ? 'bearish' : 'mixed'

  if (emaAlignment === 'bullish') {
    score += 2
    reasons.push({ text: 'EMA 9 > EMA 21 > EMA 50 — strong uptrend confirmed', bullish: true })
  } else if (emaAlignment === 'bearish') {
    score -= 2
    reasons.push({ text: 'EMA 9 < EMA 21 < EMA 50 — downtrend confirmed', bullish: false })
  } else {
    reasons.push({ text: 'EMAs mixed — no clear trend, wait for alignment', bullish: false })
  }

  // EMA crossover (short-term momentum)
  if (lastE9 > lastE21) {
    score += 0.5
    reasons.push({ text: 'EMA 9 crossed above EMA 21 — short-term momentum up', bullish: true })
  }

  // MACD
  const macdBullish = lastHist > 0 || (lastHist > prevHist && lastHist > -0.5)
  if (lastHist > 0 && lastHist > prevHist) {
    score += 1.5
    reasons.push({ text: 'MACD histogram positive and rising — strong bullish momentum', bullish: true })
  } else if (lastHist > 0) {
    score += 0.5
    reasons.push({ text: 'MACD histogram positive — bullish momentum', bullish: true })
  } else if (lastHist < 0 && lastHist < prevHist) {
    score -= 1.5
    reasons.push({ text: 'MACD histogram negative and falling — strong bearish momentum', bullish: false })
  } else {
    score -= 0.5
    reasons.push({ text: 'MACD histogram negative — bearish momentum', bullish: false })
  }

  // Bollinger Bands
  const bbWidth = (bbUpper - bbLower) / bbMid
  let bbZone: TradingSignal['bbZone'] = 'neutral'
  if (current <= bbLower * 1.005) {
    bbZone = 'oversold'
    score += 1.5
    reasons.push({ text: 'Price at lower Bollinger Band — statistical bounce zone', bullish: true })
  } else if (current >= bbUpper * 0.995) {
    bbZone = 'overbought'
    score -= 1.5
    reasons.push({ text: 'Price at upper Bollinger Band — mean-reversion risk', bullish: false })
  } else if (current > bbMid) {
    score += 0.3
    reasons.push({ text: 'Price above Bollinger midline — mild bullish bias', bullish: true })
  }

  // ── Signal classification ─────────────────────────────────────────────────
  let action: SignalAction
  if (score >= 4.5) action = 'STRONG BUY'
  else if (score >= 2) action = 'BUY'
  else if (score <= -4.5) action = 'STRONG SELL'
  else if (score <= -2) action = 'SELL'
  else action = 'HOLD'

  // Map score -7..7 → 0-100 confidence
  const confidence = Math.round(Math.min(100, Math.max(0, ((score + 7) / 14) * 100)))

  // Risk management (ATR-based)
  const stopLoss = Math.round((current - 2 * atrVal) * 100) / 100
  const takeProfit = Math.round((current + 3 * atrVal) * 100) / 100
  const riskRewardRatio = Math.round(((takeProfit - current) / (current - stopLoss)) * 100) / 100

  // Risk score: combination of BB width (volatility) and trend clarity
  const volatilityScore = Math.min(10, Math.round(bbWidth * 50))
  const trendClarity = emaAlignment === 'mixed' ? 3 : 0
  const riskScore = Math.max(1, Math.min(10, volatilityScore + trendClarity))

  return {
    action,
    confidence,
    rsiValue: Math.round(rsiVal * 10) / 10,
    emaAlignment,
    macdBullish,
    bbZone,
    riskScore,
    entryPrice: current,
    stopLoss,
    takeProfit,
    riskRewardRatio,
    reasons,
    rawScore: Math.round(score * 10) / 10,
  }
}

/** Combine technical signal + sentiment score into a prediction */
export function combinedPrediction(
  signal: TradingSignal,
  sentimentCompound: number, // -1..1
): { direction: 'UP' | 'DOWN' | 'NEUTRAL'; confidence: number; techWeight: number; sentWeight: number } {
  // Technical score mapped to -1..1
  const techScore = (signal.confidence - 50) / 50 // -1..1
  // Sentiment already -1..1
  const sentScore = Math.max(-1, Math.min(1, sentimentCompound))

  // Weighted combination: 65% technical, 35% sentiment
  const combined = techScore * 0.65 + sentScore * 0.35

  const direction = combined > 0.05 ? 'UP' : combined < -0.05 ? 'DOWN' : 'NEUTRAL'
  const confidence = Math.round(Math.min(95, Math.max(5, Math.abs(combined) * 100 + 50)))

  return {
    direction,
    confidence,
    techWeight: Math.round(techScore * 100),
    sentWeight: Math.round(sentScore * 100),
  }
}