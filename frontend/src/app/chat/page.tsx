"use client";

import { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
  recipes?: MatchedRecipe[];
}

interface MatchedRecipe {
  id: string;
  title: string;
  match_count: number;
  matched_ingredients: string;
  total_time: string;
  image_url: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Merhaba! 🐾 Ben CoPaw, yapay zeka yemek asistanınım. Elindeki malzemeleri yaz, sana ne pişirebileceğini söyleyeyim!\n\nÖrneğin: \"Tavuk, pirinç, soğan ve domates var\"",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();

      const assistantMsg: Message = {
        role: "assistant",
        content: data.reply || "Bir hata oluştu.",
        recipes: data.matched_recipes,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Bağlantı hatası. Lütfen tekrar deneyin.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex h-[calc(100vh-57px)] max-w-4xl flex-col px-4">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-6">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`chat-bubble mb-4 flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-[var(--accent)] text-white"
                  : "border border-[var(--border)] bg-[var(--bg-secondary)]"
              }`}
            >
              {msg.role === "assistant" && (
                <span className="mb-1 block text-xs font-medium text-[var(--accent)]">
                  🐾 CoPaw
                </span>
              )}
              <div className="whitespace-pre-wrap text-sm">{msg.content}</div>

              {/* Matched recipes cards */}
              {msg.recipes && msg.recipes.length > 0 && (
                <div className="mt-3 space-y-2">
                  <p className="text-xs font-medium text-[var(--text-secondary)]">
                    Eşleşen Tarifler:
                  </p>
                  {msg.recipes.slice(0, 5).map((r) => (
                    <a
                      key={r.id}
                      href={`/recipes/${r.id}`}
                      className="flex items-center gap-3 rounded-lg bg-[var(--bg-primary)] p-2 hover:bg-[var(--border)] transition-colors"
                    >
                      {r.image_url ? (
                        <img
                          src={r.image_url}
                          alt={r.title}
                          className="h-12 w-12 rounded-lg object-cover"
                        />
                      ) : (
                        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-[var(--bg-secondary)] text-lg">
                          🍽️
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="truncate text-sm font-medium">
                          {r.title}
                        </p>
                        <p className="text-xs text-[var(--text-secondary)]">
                          {r.match_count} malzeme eşleşti
                          {r.total_time && ` · ${r.total_time}`}
                        </p>
                      </div>
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="chat-bubble mb-4 flex justify-start">
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] px-4 py-3">
              <span className="text-xs font-medium text-[var(--accent)]">
                🐾 CoPaw
              </span>
              <div className="mt-1 flex gap-1">
                <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--text-secondary)]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--text-secondary)] [animation-delay:0.1s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--text-secondary)] [animation-delay:0.2s]" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-[var(--border)] py-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Elindeki malzemeleri yaz... (ör: tavuk, pirinç, soğan)"
            className="flex-1 rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] px-4 py-3 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:border-[var(--accent)] focus:outline-none"
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="rounded-xl bg-[var(--accent)] px-6 py-3 font-medium text-white hover:bg-[var(--accent-hover)] disabled:opacity-50 transition-colors"
          >
            Gönder
          </button>
        </div>
        <p className="mt-2 text-center text-xs text-[var(--text-secondary)]">
          Gemini AI tarafından desteklenmektedir • Tarifler Cookidoo&apos;dan alınmıştır
        </p>
      </div>
    </div>
  );
}
