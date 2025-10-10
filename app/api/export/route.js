import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const basePath = '/Users/richardblackhurst/Library/Mobile Documents/com~apple~CloudDocs/HOPE 5/LLMSEO-Agentic-Web-Portal/data';

function toCSV(obj){
  const rows = [['keyword','rank','title','link']];
  for (const [kw, items] of Object.entries(obj)) {
    for (const it of items) rows.push([kw, it.rank, it.title, it.link]);
  }
  return rows.map(r => r.map(x => `"${String(x??'').replace(/"/g,'""')}"`).join(',')).join('\n');
}

export async function GET(req) {
  const { searchParams } = new URL(req.url);
  const projectId = searchParams.get('projectId') || 'default';
  const dataPath = path.join(basePath, 'projects', projectId, 'results.json');
  try {
    const json = JSON.parse(fs.readFileSync(dataPath, 'utf-8'));
    const csv = toCSV(json);
    return new NextResponse(csv, {
      headers: {
        'Content-Type': 'text/csv',
        'Content-Disposition': `attachment; filename="results_${projectId}.csv"`
      }
    });
  } catch (e) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

