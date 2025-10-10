import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const filePath = path.join(process.cwd(), 'results.json');
    const raw = fs.existsSync(filePath) ? fs.readFileSync(filePath, 'utf-8') : '{}';
    const data = JSON.parse(raw || '{}');
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: 'Failed to read results' }, { status: 500 });
  }
}
