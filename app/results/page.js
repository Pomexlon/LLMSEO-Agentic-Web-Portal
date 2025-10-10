'use client';
import { useEffect, useState } from 'react';

export default function ResultsPage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    const ls = localStorage.getItem('llmseo_last_results');
    if (ls) setData(JSON.parse(ls));
    else setData({});
  }, []);

  if (data === null) return <div style={{padding:24}}>Loading…</div>;

  const queries = Object.keys(data || {});
  return (
    <div style={{fontFamily:'Inter, system-ui, Arial', padding: 24, maxWidth: 980, margin: '0 auto'}}>
      <header style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom: 24}}>
        <h1 style={{fontSize: 28, fontWeight: 700}}>LLMSEO • SERP Dashboard</h1>
        <a href="/" style={{textDecoration:'none', fontSize:14}}>Home</a>
      </header>

      {!queries.length && <div>No results yet. Go back and run a crawl.</div>}

      {queries.map((q) => (
        <section key={q} style={{background:'#fff', border:'1px solid #eee', borderRadius:14, padding:18, marginBottom:20, boxShadow:'0 1px 2px rgba(0,0,0,0.04)'}}>
          <h2 style={{fontSize:20, marginBottom:10}}>{q}</h2>
          <ol style={{paddingLeft:20, lineHeight:1.6}}>
            {(data[q] || []).map((r) => (
              <li key={`${r.rank}-${r.link}`}>
                <a href={r.link} target="_blank" rel="noreferrer" style={{color:'#2563eb', textDecoration:'none'}}>
                  {r.title || r.link}
                </a>
                <span style={{color:'#666'}}>  • rank #{r.rank}</span>
              </li>
            ))}
          </ol>
        </section>
      ))}
    </div>
  );
}
