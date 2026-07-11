import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { fetchHistory } from '../history'

describe('fetchHistory', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('builds the /api/history URL with encoded symbol and days', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ symbol: 'AAPL', source: 'yahoo', candles: [], warning: null }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await fetchHistory('AAPL', 90)

    const url = fetchMock.mock.calls[0][0] as string
    expect(url).toContain('/api/history?')
    expect(url).toContain('symbol=AAPL')
    expect(url).toContain('days=90')
  })

  it('defaults days to 365 when omitted', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ symbol: 'TSLA', source: 'stooq', candles: [], warning: null }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await fetchHistory('TSLA')

    expect(fetchMock.mock.calls[0][0]).toContain('days=365')
  })

  it('percent-encodes symbols that need it', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ symbol: 'BTC/USD', source: 'binance', candles: [], warning: null }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await fetchHistory('BTC/USD')

    expect(fetchMock.mock.calls[0][0]).toContain('symbol=BTC%2FUSD')
  })

  it('throws with the backend detail message on a non-ok response', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      json: async () => ({ detail: 'symbol is required' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(fetchHistory('')).rejects.toThrow('symbol is required')
  })
})
