'use client';
import { useState } from 'react';

export default function Home() {
  const [url, setUrl] = useState('');
  const [keywords, setKeywords] = useState('');

  const runCloud = async () => {
    const kws = keywords.split(',').map(s => s.trim()).filter(Boolean);
    if (kws.length === 0) { alert('Please enter at least one keyword'); return; }
    try {
      const res = await fetch('/api/crawl', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ keywords: kws, maxPerQuery: 10 })
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || 'Crawl failed');
      // stash results for display page
      localStorage.setItem('llmseo_last_results', JSON.stringify(data.results));
      window.location.href = '/results';
    } catch (e) {
      alert('Error: ' + e.message);
    }
  };

  return (
    <div style={{fontFamily:'Inter, system-ui, Arial', padding: 24, maxWidth: 720, margin: '0 auto'}}>
      <h1 style={{fontSize: 28, fontWeight: 700, marginBottom: 12}}>LLMSEO Advisor</h1>
      <p style={{color:'#444', marginBottom: 18}}>Enter your website and target keywords.</p>

      <label>Website URL</label>
      <input value={url} onChange={e=>setUrl(e.target.value)} placeholder="https://www.example.com"
        style={{width:'100%', padding:12, border:'1px solid #ddd', borderRadius:10, margin:'6px 0 14px'}} />

      <label>Keywords (comma-separated)</label>
      <textarea value={keywords} onChange={e=>setKeywords(e.target.value)} rows={3}
        placeholder="oxygen concentrators uk, portable oxygen concentrator"
        style={{width:'100%', padding:12, border:'1px solid #ddd', borderRadius:10, margin:'6px 0 16px'}} />

      <div style={{display:'flex', gap:12}}>
        <button onClick={runCloud}
          style={{background:'#111827', color:'#fff', padding:'10px 16px', borderRadius:10, border:'none', cursor:'pointer'}}>
          Run Crawl (Cloud)
        </button>
        <a href="/results" style={{alignSelf:'center'}}>View Results</a>
      </div>
    </div>
  );
}
