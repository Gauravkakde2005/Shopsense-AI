import { useEffect, useRef, useState, type ReactNode } from 'react'
import axios from 'axios'
import { Bot, LoaderCircle, Minus, Send, Sparkles, Trash2, X } from 'lucide-react'

const API_URL = 'http://localhost:8000'

type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

type ProductAssistantProps = {
  searchedProduct: string
  products: any[]
  parsedRequirements: Record<string, unknown>
  comparison: any[]
}

function renderInlineMarkdown(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={`${part}-${index}`}>{part.slice(2, -2)}</strong>
    }
    return <span key={`${part}-${index}`}>{part}</span>
  })
}

function renderAssistantMessage(content: string): ReactNode[] {
  const blocks: ReactNode[] = []
  let listItems: string[] = []

  const flushList = () => {
    if (listItems.length > 0) {
      blocks.push(
        <ul key={`list-${blocks.length}`} className="my-2 list-disc space-y-1 pl-5">
          {listItems.map((item, index) => <li key={`${item}-${index}`}>{renderInlineMarkdown(item)}</li>)}
        </ul>,
      )
      listItems = []
    }
  }

  content.split(/\r?\n/).forEach((line, index) => {
    const trimmed = line.trim()
    const bullet = trimmed.match(/^(?:[*-])\s+(.*)$/)
    const heading = trimmed.match(/^#{1,3}\s+(.*)$/)
    if (bullet) {
      listItems.push(bullet[1])
    } else if (heading) {
      flushList()
      blocks.push(<p key={`heading-${index}`} className="mt-2 font-semibold text-slate-900">{renderInlineMarkdown(heading[1])}</p>)
    } else if (trimmed) {
      flushList()
      blocks.push(<p key={`paragraph-${index}`} className="my-1">{renderInlineMarkdown(trimmed)}</p>)
    } else {
      flushList()
    }
  })
  flushList()
  return blocks
}

export default function ProductAssistant({
  searchedProduct,
  products,
  parsedRequirements,
  comparison,
}: ProductAssistantProps) {
  const [open, setOpen] = useState(false)
  const [minimized, setMinimized] = useState(false)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: 'I can explain, compare, and evaluate the products currently displayed. What would you like to know?',
    },
  ])
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, open, minimized])

  async function sendMessage() {
    const content = input.trim()
    if (!content || sending) {
      return
    }
    const nextMessages: ChatMessage[] = [...messages, { role: 'user', content }]
    setMessages(nextMessages)
    setInput('')
    setError('')
    setSending(true)
    try {
      const response = await axios.post(`${API_URL}/api/assistant/chat`, {
        searched_product: searchedProduct,
        products,
        parsed_requirements: parsedRequirements,
        comparison,
        messages: nextMessages,
      })
      setMessages((current) => [...current, { role: 'assistant', content: response.data.answer }])
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail || 'The assistant could not answer right now.')
    } finally {
      setSending(false)
    }
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      void sendMessage()
    }
  }

  function clearChat() {
    setMessages([])
    setError('')
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      {open && !minimized ? (
        <section className="flex h-[min(620px,calc(100vh-7rem))] w-[min(390px,calc(100vw-2rem))] flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl shadow-slate-900/20">
          <header className="flex items-center justify-between bg-slate-900 px-4 py-3 text-white">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-500"><Bot size={18} /></div>
              <div>
                <p className="font-semibold">AI Product Assistant</p>
                <p className="text-xs text-slate-300">{products.length ? `${products.length} products in context` : 'Search for products to begin'}</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={clearChat} title="Clear chat" aria-label="Clear chat" className="rounded-lg p-2 text-slate-300 hover:bg-slate-800 hover:text-white"><Trash2 size={16} /></button>
              <button onClick={() => setMinimized(true)} title="Minimize assistant" aria-label="Minimize assistant" className="rounded-lg p-2 text-slate-300 hover:bg-slate-800 hover:text-white"><Minus size={17} /></button>
              <button onClick={() => setOpen(false)} title="Close assistant" aria-label="Close assistant" className="rounded-lg p-2 text-slate-300 hover:bg-slate-800 hover:text-white"><X size={17} /></button>
            </div>
          </header>

          <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto bg-slate-50 p-4">
            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[88%] whitespace-pre-wrap rounded-2xl px-3 py-2.5 text-sm leading-6 ${message.role === 'user' ? 'rounded-br-md bg-indigo-600 text-white' : 'rounded-bl-md border border-slate-200 bg-white text-slate-700'}`}>
                  {message.role === 'assistant' ? renderAssistantMessage(message.content) : message.content}
                </div>
              </div>
            ))}
            {sending ? (
              <div className="flex items-center gap-2 text-xs text-slate-500"><LoaderCircle size={15} className="animate-spin" /> Thinking from the current product data...</div>
            ) : null}
            {error ? <p className="rounded-xl bg-red-50 px-3 py-2 text-xs text-red-700">{error}</p> : null}
          </div>

          <div className="border-t border-slate-200 bg-white p-3">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about these products..."
              rows={2}
              className="w-full resize-none rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            />
            <div className="mt-2 flex items-center justify-between">
              <span className="text-[11px] text-slate-400">Answers use the current search results</span>
              <button onClick={() => void sendMessage()} disabled={!input.trim() || sending} className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"><Send size={14} /> Send</button>
            </div>
          </div>
        </section>
      ) : null}

      {open && minimized ? (
        <button onClick={() => setMinimized(false)} className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-xl hover:border-indigo-300 hover:text-indigo-700">Open assistant</button>
      ) : null}

      <button
        onClick={() => { setOpen((current) => !current); setMinimized(false) }}
        title="Open AI Product Assistant"
        aria-label="Open AI Product Assistant"
        className="flex h-14 w-14 items-center justify-center rounded-full bg-indigo-600 text-white shadow-xl shadow-indigo-600/30 transition hover:scale-105 hover:bg-indigo-500"
      >
        {open ? <X size={22} /> : <Sparkles size={22} />}
      </button>
    </div>
  )
}