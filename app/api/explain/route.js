import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const basePath = '/Users/richardblackhurst/Library/Mobile Documents/com~apple~CloudDocs/HOPE 5/LLMSEO-Agentic-Web-Portal/data';

export async function POST(req){
  try{
    const { projectId='default', keyword } = await req.json();
    const dataPath = path.join(basePath, 'projects', projectId, 'results.json');
    const json = JSON.parse(fs.readFileSync(dataPath, 'utf-8'));
    const items = json[keyword] || [];
    const competitors = items.slice(0,3).map(i=>`${i.title} — ${i.link}`).join('\n');

    const key = process.env.OPENAI_API_KEY;
    if(!key) throw new Error('Missing OPENAI_API_KEY');

    const prompt = `Keyword: ${keyword}
Top results:
${competitors}

Give 3–5 short bullets explaining likely reasons these rank above our site and the most leverage actions to outrank them. Be specific (content gaps, schema, page intent, internal links).`;

    const res = await fetch('https://api.openai.com/v1/chat/completions',{
      method:'POST',
      headers:{'Authorization':`Bearer ${key}`,'Content-Type':'application/json'},
      body: JSON.stringify({model:'gpt-4o-mini', messages:[{role:'user', content: prompt}], temperature:0.2})
    });
    const data = await res.json();
    const text = data?.choices?.[0]?.message?.content ?? 'No advice.';
    return NextResponse.json({ advice: text });
  }catch(e){
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

