import { useEffect, useState } from "react";

//const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8100";
const API =
  (typeof window !== 'undefined' && (process.env.NEXT_PUBLIC_API_URL || `${window.location.protocol}//${window.location.hostname}:8100`))
  || process.env.NEXT_PUBLIC_API_URL
  || "http://localhost:8100";

export default function Home() {
  const [status, setStatus] = useState("checking…");
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [symbol, setSymbol] = useState("MSFT");
  const [watchlist, setWatchlist] = useState([]);
  const [quote, setQuote] = useState(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch(API + "/health").then(r => r.json()).then(d => setStatus(d.status)).catch(()=>setStatus("error"));
    const t = localStorage.getItem("ig_token");
    if (t) { setToken(t); loadWatchlist(t); }
  }, []);

  const register = async () => {
    setMessage("");
    try {
      const res = await fetch(API+"/auth/register", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({username, password})
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || "Registration failed");
      }
      await login(); // proceed to login
    } catch (e) {
      setMessage(String(e.message || e));
    }
  };

  const login = async () => {
    setMessage("");
    try {
      const r = await fetch(API+"/auth/login", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({username, password})
      });
      if (!r.ok) {
        const txt = await r.text();
        throw new Error(txt || "Invalid credentials");
      }
      const data = await r.json();
      localStorage.setItem("ig_token", data.access_token);
      setToken(data.access_token);
      loadWatchlist(data.access_token);
    } catch (e) {
      setMessage(String(e.message || e));
    }
  };

  const authHeader = (t) => ({"Authorization":"Bearer "+t});

  const loadWatchlist = async (t = token) => {
    if (!t) return;
    const r = await fetch(API+"/watchlist", { headers: authHeader(t) });
    if (r.ok) setWatchlist(await r.json());
  };

  const addSymbol = async () => {
    if (!token) return alert("Login first");
    const r = await fetch(API+"/watchlist", {
      method:"POST",
      headers:{"Content-Type":"application/json", ...authHeader(token)},
      body: JSON.stringify({symbol})
    });
    if (r.ok) loadWatchlist();
  };

  const getQuote = async () => {
    const r = await fetch(API+"/quotes/"+symbol);
    if (r.ok) setQuote(await r.json());
  };

  // Background jobs demo
  const enqueueJob = async () => {
    const r = await fetch(API+"/jobs/quote", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify({symbol})
    });
    const data = await r.json();
    setMessage("Job queued: " + data.job_id);
  };

  return (
    <main className="wrap">
      <h1>Invest-guru</h1>
      <p>API health: <b>{status}</b></p>
      {message && <p style={{color:'crimson'}}>{message}</p>}

      {!token && (
        <section className="card">
          <h2>Login or Create Account</h2>
          <input placeholder="username" value={username} onChange={e=>setUsername(e.target.value)} />
          <input type="password" placeholder="password" value={password} onChange={e=>setPassword(e.target.value)} />
          <div className="row">
            <button onClick={login}>Login</button>
            <button onClick={register}>Create Account</button>
          </div>
        </section>
      )}

      {token && (
        <section className="card">
          <h2>Watchlist & Quotes</h2>
          <div className="row">
            <input value={symbol} onChange={e=>setSymbol(e.target.value.toUpperCase())} />
            <button onClick={addSymbol}>Add to Watchlist</button>
            <button onClick={getQuote}>Get Quote</button>
            <button onClick={enqueueJob}>Queue BG Job</button>
          </div>

          <h3>Watchlist</h3>
          <ul>{watchlist.map((i)=> <li key={i.id}>{i.symbol}</li>)}</ul>

          {quote && (
            <div className="quote">
              <div><b>{quote.symbol}</b> — {quote.name}</div>
              <div>Date/Time: {quote.date} {quote.time}</div>
              <div>O: {quote.open} H: {quote.high} L: {quote.low} C: {quote.close} Vol: {quote.volume}</div>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
