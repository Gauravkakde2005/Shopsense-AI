import { useEffect, useState } from 'react'
import axios from 'axios'
import {
  ArrowRight,
  BarChart3,
  Heart,
  Mic,
  Search,
  ShieldCheck,
  ShoppingBag,
  Sparkles,
  Star,
  TrendingUp,
  Volume2,
} from 'lucide-react'
import { BarChart, Bar, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

const API_URL = 'http://localhost:8000'

const prompts = [
  'Best Titan watch under ₹5,000 with a black dial',
  'Compare smartwatches under ₹4,500 for daily college use',
  'Find a stylish watch with a metal strap and strong reviews',
]

const defaultWeights = {
  rating: 30,
  review: 25,
  value: 25,
  preference: 20,
}

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [selected, setSelected] = useState<string[]>([])
  const [comparison, setComparison] = useState<any[]>([])
  const [saved, setSaved] = useState<string[]>([])
  const [parsedRequirements, setParsedRequirements] = useState<Record<string, unknown>>({})
  const [weights, setWeights] = useState(defaultWeights)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [listening, setListening] = useState(false)
  const [sourceStatus, setSourceStatus] = useState('Checking live provider')

  async function handleSearch(value = query) {
    setLoading(true)
    setError('')
    try {
      const response = await axios.post(`${API_URL}/api/search`, { query: value })
      const data = response.data
      setResults(data.recommendations)
      setParsedRequirements(data.parsed_requirements || {})
      setSourceStatus(data.source_status || 'live_web')
      setSelected((prev) => {
        const nextIds = [...prev, ...(data.recommendations || []).slice(0, 2).map((item: any) => item.product_id)]
        return Array.from(new Set(nextIds))
      })
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Unable to load recommendations right now.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadSavedProducts()
    void loadProviderStatus()
  }, [])

  async function loadProviderStatus() {
    try {
      const response = await axios.get(`${API_URL}/api/providers`)
      const provider = response.data?.[0]
      setSourceStatus(provider?.status === 'configured' ? 'Live web retrieval ready' : 'Live provider needs configuration')
    } catch {
      setSourceStatus('Provider status unavailable')
    }
  }

  function handleVoiceInput() {
    const speechWindow = window as typeof window & {
      SpeechRecognition?: any
      webkitSpeechRecognition?: any
    }
    const Recognition = speechWindow.SpeechRecognition || speechWindow.webkitSpeechRecognition
    if (!Recognition) {
      setError('Voice input is not supported by this browser. Try Chrome or Edge.')
      return
    }
    const recognition = new Recognition()
    recognition.lang = 'en-IN'
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognition.onstart = () => setListening(true)
    recognition.onend = () => setListening(false)
    recognition.onerror = () => {
      setListening(false)
      setError('Voice input could not be captured. Please try again.')
    }
    recognition.onresult = (event: any) => {
      const transcript = event.results?.[0]?.[0]?.transcript?.trim()
      if (transcript) {
        setQuery(transcript)
        void handleSearch(transcript)
      }
    }
    recognition.start()
  }

  function speakRecommendation(item: any) {
    if (!('speechSynthesis' in window)) {
      setError('Read-aloud is not supported by this browser.')
      return
    }
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(new SpeechSynthesisUtterance(
      `${item.product_name}. Price ${item.price_inr ? `₹${item.price_inr}` : 'not available'}. Rating ${item.rating || 'not available'}. ${item.explanation}`,
    ))
  }

  async function loadSavedProducts() {
    try {
      const response = await axios.get(`${API_URL}/api/saved-products`)
      setSaved(Object.keys(response.data || {}))
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Saved products could not be loaded.')
    }
  }

  async function handleCompare() {
    if (selected.length === 0) {
      return
    }
    try {
      const response = await axios.post(`${API_URL}/api/compare`, { product_ids: selected.slice(0, 5) })
      setComparison(response.data.comparison)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Comparison failed.')
    }
  }

  async function handleSave(productId: string) {
    try {
      await axios.post(`${API_URL}/api/saved-products`, { product_id: productId })
      setSaved((prev) => (prev.includes(productId) ? prev : [...prev, productId]))
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Save failed.')
    }
  }

  async function handleDeleteSaved(productId: string) {
    try {
      await axios.delete(`${API_URL}/api/saved-products/${productId}`)
      setSaved((prev) => prev.filter((id) => id !== productId))
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Could not remove saved product.')
    }
  }

  async function handleRerank(nextWeights = weights) {
    const productIds = selected.length > 0 ? selected : results.map((item) => item.product_id)
    if (productIds.length === 0) {
      return
    }

    try {
      const response = await axios.post(`${API_URL}/api/recommendations/rerank`, {
        product_ids: productIds.slice(0, 5),
        max_budget: parsedRequirements.max_budget || 100000,
        weights: {
          rating: nextWeights.rating / 100,
          review: nextWeights.review / 100,
          value: nextWeights.value / 100,
          preference: nextWeights.preference / 100,
        },
      })
      setResults(response.data.ranked_products)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Reranking failed.')
    }
  }

  const chartData = results.map((item) => ({
    name: item.product_name?.split(' ')[0] || 'Product',
    score: item.score,
    price: item.price_inr || 0,
  }))

  const reviewData = results.map((item) => ({
    name: item.product_name?.split(' ')[0] || 'Product',
    rating: item.rating ? item.rating * 20 : 0,
  }))

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="mx-auto max-w-7xl px-6 py-6">
        <nav className="flex items-center justify-between rounded-full border border-slate-200 bg-white/80 px-5 py-3 shadow-sm backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-600 text-lg font-bold text-white">S</div>
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">ShopSense AI</p>
              <h1 className="text-lg font-semibold">Smart shopping assistant</h1>
            </div>
          </div>
          <div className="hidden items-center gap-8 md:flex">
            <a className="text-sm font-medium text-slate-600" href="#search">Search</a>
            <a className="text-sm font-medium text-slate-600" href="#insights">Insights</a>
            <a className="text-sm font-medium text-slate-600" href="#compare">Compare</a>
          </div>
          <div className="flex items-center gap-3">
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
              Saved {saved.length}
            </span>
            <button className="rounded-full bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500">
              Start now
            </button>
          </div>
        </nav>
      </header>

      <main className="mx-auto max-w-7xl space-y-10 px-6 pb-16">
        <section className="grid gap-6 rounded-[2rem] border border-slate-200 bg-white p-8 shadow-xl shadow-indigo-100/40 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-indigo-700">
              <Sparkles size={14} /> Intelligent product discovery
            </div>
            <div>
              <h2 className="text-4xl font-black tracking-tight text-slate-900 md:text-5xl">Find the best product for you</h2>
              <p className="mt-4 max-w-xl text-lg text-slate-600">Personalized, review-driven recommendations with transparent scores, better value checks, and source-backed shopping links.</p>
            </div>

            <div id="search" className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-3 md:flex-row">
              <div className="flex flex-1 items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3">
                <Search className="text-slate-400" size={18} />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask for a product, budget, brand, or feature"
                  className="w-full border-0 bg-transparent text-sm outline-none placeholder:text-slate-400"
                />
                <button
                  type="button"
                  onClick={handleVoiceInput}
                  title="Speak your shopping requirements"
                  aria-label="Speak your shopping requirements"
                  className={`rounded-lg p-2 ${listening ? 'bg-rose-100 text-rose-600' : 'text-slate-500 hover:bg-slate-100 hover:text-indigo-600'}`}
                >
                  <Mic size={18} />
                </button>
              </div>
              <button
                onClick={() => void handleSearch()}
                className="rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
              >
                Search
              </button>
            </div>

            <div className="flex flex-wrap gap-2">
              {prompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => setQuery(prompt)}
                  className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm text-slate-700 transition hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-[1.5rem] border border-slate-200 bg-slate-900 p-5 text-white">
            <div className="mb-4 flex items-center justify-between">
              <p className="text-sm uppercase tracking-[0.2em] text-slate-300">Data source</p>
              <ShieldCheck className="text-emerald-400" size={18} />
            </div>
            <div className="space-y-4">
              <div className="rounded-2xl border border-slate-700 bg-slate-800 p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Status</p>
                <p className="mt-2 text-2xl font-bold text-emerald-400">{sourceStatus}</p>
              </div>
              <div className="space-y-3 text-sm text-slate-300">
                <p>• Prices and links come from the authorized search provider</p>
                <p>• Ratings are shown only when returned by the source</p>
                <p>• No live provider data means no recommendations</p>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          {[
            { title: 'Budget fit', icon: ShoppingBag, value: '₹0–₹5,000' },
            { title: 'Review score', icon: TrendingUp, value: '4.0+ avg' },
            { title: 'Recommendation engine', icon: BarChart3, value: 'Transparent scoring' },
          ].map(({ title, icon: Icon, value }) => (
            <div key={title} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-700">
                <Icon size={18} />
              </div>
              <p className="text-sm text-slate-500">{title}</p>
              <p className="mt-2 text-xl font-bold">{value}</p>
            </div>
          ))}
        </section>

        {error ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-red-700">{error}</div>
        ) : null}

        {parsedRequirements && Object.keys(parsedRequirements).length > 0 ? (
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Extracted preferences</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {Object.entries(parsedRequirements).map(([key, value]) => (
                <span key={key} className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700">
                  {key}: {String(value)}
                </span>
              ))}
            </div>
          </section>
        ) : null}

        {loading ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-slate-600">Loading recommendations…</div>
        ) : (
          <section className="grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
            <div className="space-y-5">
              {results.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-slate-500">
                  No recommendation yet. Search for a product to begin.
                </div>
              ) : (
                results.map((item) => (
                  <article key={item.product_id} className="card-shadow rounded-[1.5rem] border border-slate-200 bg-white p-5">
                    <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                      <div className="flex gap-4">
                        <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-100 to-cyan-100 text-2xl font-black text-indigo-700">
                          {item.brand?.slice(0, 2).toUpperCase() || 'AI'}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{item.brand}</p>
                            <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-700">
                              {item.source_label}
                            </span>
                          </div>
                          <h3 className="mt-1 text-2xl font-bold">{item.product_name}</h3>
                          <div className="mt-2 flex items-center gap-3 text-sm text-slate-600">
                            <span className="flex items-center gap-1"><Star size={14} className="fill-amber-400 text-amber-400" /> {item.rating || 'N/A'}</span>
                            <span>{item.review_count || 0} reviews</span>
                            <span>{item.data_freshness}</span>
                          </div>
                        </div>
                      </div>

                      <div className="text-left md:text-right">
                        <p className="text-sm text-slate-500">Offer price</p>
                        <p className="text-3xl font-black text-slate-900">₹{item.price_inr?.toLocaleString() || 'N/A'}</p>
                        <p className="text-sm text-slate-500">{item.retailer_name}</p>
                      </div>
                    </div>

                    <div className="mt-5 flex flex-wrap gap-3">
                      <button
                        onClick={() => setSelected((prev) => prev.includes(item.product_id) ? prev : [...prev, item.product_id])}
                        className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:border-indigo-200 hover:text-indigo-700"
                      >
                        Select for compare
                      </button>
                      <button
                        onClick={() => void handleSave(item.product_id)}
                        className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:border-rose-200 hover:text-rose-600"
                      >
                        <span className="inline-flex items-center gap-2"><Heart size={14} /> Save</span>
                      </button>
                      <button
                        onClick={() => speakRecommendation(item)}
                        title="Read recommendation aloud"
                        aria-label={`Read ${item.product_name} recommendation aloud`}
                        className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:border-cyan-200 hover:text-cyan-700"
                      >
                        <span className="inline-flex items-center gap-2"><Volume2 size={14} /> Listen</span>
                      </button>
                      {item.retailer_url ? (
                        <a href={item.retailer_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-3 py-2 text-sm font-medium text-white">
                          Open retailer <ArrowRight size={14} />
                        </a>
                      ) : null}
                    </div>

                    <div className="mt-5 grid gap-4 md:grid-cols-3">
                      <div className="rounded-2xl bg-slate-50 p-3">
                        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Recommendation score</p>
                        <p className="mt-2 text-2xl font-bold text-indigo-700">{item.score}</p>
                      </div>
                      <div className="rounded-2xl bg-slate-50 p-3">
                        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Preference match</p>
                        <p className="mt-2 text-2xl font-bold text-emerald-600">{item.preference_match}%</p>
                      </div>
                      <div className="rounded-2xl bg-slate-50 p-3">
                        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Confidence</p>
                        <p className="mt-2 text-2xl font-bold text-cyan-600">{item.confidence}%</p>
                      </div>
                    </div>

                    <p className="mt-5 text-slate-700">{item.explanation}</p>
                  </article>
                ))
              )}
            </div>

            <aside id="insights" className="space-y-5">
              <div className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm">
                <p className="text-sm font-semibold text-slate-500">Recommendations trend</p>
                <div className="h-52 pt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Bar dataKey="score" radius={[6, 6, 0, 0]} fill="#4f46e5" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-slate-500">Ratings & review coverage</p>
                  <span className="text-xs text-slate-400">rating / 5</span>
                </div>
                <div className="h-52 pt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={reviewData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Bar dataKey="rating" radius={[6, 6, 0, 0]} fill="#059669" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-2 space-y-2">
                  {results.slice(0, 3).map((item) => (
                    <div key={item.product_id} className="flex items-center justify-between text-xs text-slate-600">
                      <span>{item.product_name}</span>
                      <span>{item.review_count || 0} customer reviews</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm">
                <p className="text-sm font-semibold text-slate-500">Selected products</p>
                <div className="mt-3 space-y-2">
                  {selected.length === 0 ? (
                    <p className="text-sm text-slate-500">Nothing selected yet.</p>
                  ) : (
                    selected.map((id) => (
                      <button
                        key={id}
                        className="flex w-full items-center justify-between rounded-xl border border-slate-200 px-3 py-2 text-left text-sm text-slate-700 hover:border-indigo-200 hover:text-indigo-700"
                        onClick={() => setSelected((prev) => prev.filter((item) => item !== id))}
                      >
                        Product #{id}
                        <span>Remove</span>
                      </button>
                    ))
                  )}
                </div>
                <button
                  onClick={() => void handleCompare()}
                  className="mt-4 w-full rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500"
                >
                  Compare selected
                </button>
              </div>

              <div className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm">
                <p className="text-sm font-semibold text-slate-500">Adjust ranking priorities</p>
                <div className="mt-4 space-y-4">
                  {Object.entries(weights).map(([key, value]) => (
                    <div key={key}>
                      <div className="mb-2 flex items-center justify-between text-xs uppercase tracking-[0.2em] text-slate-500">
                        <span>{key}</span>
                        <span>{value}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={value}
                        onChange={(event) => {
                          const nextWeights = { ...weights, [key]: Number(event.target.value) }
                          setWeights(nextWeights)
                          void handleRerank(nextWeights)
                        }}
                        className="w-full accent-indigo-600"
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm">
                <p className="text-sm font-semibold text-slate-500">Saved products</p>
                <div className="mt-3 space-y-2">
                  {saved.length === 0 ? (
                    <p className="text-sm text-slate-500">No products saved yet.</p>
                  ) : (
                    saved.map((id) => (
                      <div key={id} className="flex items-center justify-between rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-700">
                        <span>#{id}</span>
                        <button
                          onClick={() => void handleDeleteSaved(id)}
                          className="text-xs font-medium text-rose-600 hover:text-rose-500"
                        >
                          Remove
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </aside>
          </section>
        )}

        {comparison.length > 0 ? (
          <section id="compare" className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-2xl font-bold">Product comparison</h3>
              <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-indigo-700">side by side</span>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500">
                    <th className="py-3 pr-4">Product</th>
                    <th className="py-3 pr-4">Brand</th>
                    <th className="py-3 pr-4">Price</th>
                    <th className="py-3 pr-4">Rating</th>
                    <th className="py-3 pr-4">Score</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.map((item) => (
                    <tr key={item.product_id} className="border-b border-slate-100 align-top">
                      <td className="py-3 pr-4 font-semibold">{item.product_name}</td>
                      <td className="py-3 pr-4">{item.brand}</td>
                      <td className="py-3 pr-4">₹{item.price_inr?.toLocaleString() || 'N/A'}</td>
                      <td className="py-3 pr-4">{item.rating || 'N/A'}</td>
                      <td className="py-3 pr-4">{item.score}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}
      </main>
    </div>
  )
}

export default App
