import { useState } from "react";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function App() {
  const [query, setQuery] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runSearch = async (q) => {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, top_k: 5 }),
      });
      const json = await res.json();
      if (!res.ok) {
        setError(typeof json.detail === "string" ? json.detail : JSON.stringify(json.detail));
        setData(null);
      } else {
        setData(json);
      }
    } catch (err) {
      setError(`Could not reach the backend: ${err.message}`);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    runSearch(query);
  };

  const fmtTime = (ts) => (ts ? new Date(ts).toLocaleString() : "");

  return (
    <div className="app">
      <header className="header">
        <h1>Search a Group Chat Properly</h1>
        <p className="subtitle">
          Semantic search over group chat — understands meaning, not just keywords.
        </p>
      </header>

      <main className="main">
        <form className="search-form" onSubmit={handleSearch}>
          <input
            type="text"
            className="search-input"
            placeholder='e.g. "What did Priya say about the budget in May 2024?"'
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
          />
          <button type="submit" className="search-button" disabled={loading || !query.trim()}>
            {loading ? "Searching…" : "Search"}
          </button>
        </form>

        <div className="examples">
          Try:
          {[
            "when did we finalize the Manali trip?",
            "what did Priya say about the budget?",
            "what did we discuss last month?",
          ].map((ex) => (
            <button key={ex} type="button" className="example-chip" onClick={() => { setQuery(ex); runSearch(ex); }}>
              {ex}
            </button>
          ))}
        </div>

        {loading && <div className="loading">Searching 4,210 messages…</div>}

        {error && <div className="error">⚠ {error}</div>}

        

        {data && !loading && (
          <div className="results-area">
            <div className="filters-bar">
              {data.filters?.sender && <span className="filter-chip">👤 Sender: {data.filters.sender}</span>}
              {data.filters?.date_range && (
                <span className="filter-chip">
                  📅 {new Date(data.filters.date_range[0]).toLocaleDateString()} –{" "}
                  {new Date(data.filters.date_range[1]).toLocaleDateString()}
                </span>
              )}
              {!data.filters?.sender && !data.filters?.date_range && (
                <span className="filter-chip muted">semantic (no filters)</span>
              )}
              <span className="result-count">{data.total_results} result(s)</span>
            </div>

            {data.results?.length === 0 && <p className="no-results">No results found.</p>}

            {data.results?.map((item, i) => (
              <div key={item.message_id} className="result-card">
                <div className="result-header">
                  <span className="match-badge">Match {i + 1}</span>
                  <span className="score">score {item.score.toFixed(4)}</span>
                  <span className="thread">thread: {item.thread_id}</span>
                </div>
                <div className="context-block">
                  {item.context.map((m) => (
                    <div key={m.message_id} className={`context-msg ${m.is_matched ? "matched" : ""}`}>
                      <span className="msg-sender">{m.sender}</span>
                      <span className="msg-text">{m.text}</span>
                      <span className="msg-time">{fmtTime(m.timestamp)}</span>
                      {m.is_matched && <span className="match-tag">◀ match</span>}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {!data && !loading && !error && (
          <div className="placeholder-text">
            <p>Ask a question about the group chat to get started.</p>
            <ul>
              <li>Semantic — "when did we decide on the trip"</li>
              <li>Attributed — "what did Priya say about the budget"</li>
              <li>Temporal — "what did we discuss last month"</li>
            </ul>
          </div>
        )}
      </main>

      <footer className="footer">
        <p>Synthetic dataset · 8 participants · Jan–Jun 2024 · MongoDB Vector Search + multilingual-e5-small</p>
      </footer>
    </div>
  );
}

export default App;
