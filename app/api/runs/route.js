import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const basePath = '/Users/richardblackhurst/Library/Mobile Documents/com~apple~CloudDocs/HOPE 5/LLMSEO-Agentic-Web-Portal/data';

export async function GET(req) {
  const { searchParams } = new URL(req.url);
  const projectId = searchParams.get('projectId') || 'default';
  const dir = path.join(basePath, 'projects', projectId, 'runs');
  try {
    const files = fs.readdirSync(dir).filter(f => f.endsWith('.json')).sort().reverse().slice(0, 10);
    return NextResponse.json(files);
  } catch {
    return NextResponse.json([], { status: 200 });
  }
}

