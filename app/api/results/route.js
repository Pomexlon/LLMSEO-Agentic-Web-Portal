import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const dataPath = path.join(process.cwd(), 'results.json');
    const jsonData = fs.readFileSync(dataPath, 'utf-8');
    const results = JSON.parse(jsonData);
    
    return NextResponse.json(results);
  } catch (error) {
    console.error('Error reading JSON file:', error);
    return NextResponse.json({ error: 'Error reading JSON file' }, { status: 500 });
  }
}

