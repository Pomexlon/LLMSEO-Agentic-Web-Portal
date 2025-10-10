import { NextResponse } from 'next/server';
import cheerio from 'cheerio';

const TOKEN = process.env.CRAWLBASE_TOKEN;

// helper: fetch a Google SERP via Crawlbase/ProxyCrawl
async function fetchSerp(query) {
  const searchUrl = 'https://www.google.com/search?q=' + encodeURIComponent(query) + '&hl=en-GB';
  const apiUrl = `https://api.proxycrawl.com/?token=${TOKEN}&url=${encodeURIComponent(searchUrl)}`;

  const resp = await fetch(apiUrl, { cache: 'no-store' });
  if (!resp.ok) throw new Error(`Crawlbase HTTP ${resp.status}`);
  const html = await resp.text();

  const $ = cheerio.load(html);
  const results = [];

  // primary selector block
  $('div.ezO2md').each((i, el) => {
    const title = $(el).find('span.CVA68e').text().trim();
    let link = $(el).find('a').attr('href');
    if (link && link.startsWith('/url?q=')) {
      link = decodeURIComponent(link.split('/url?q=')[1].split('&sa=')[0]);
    }
    if (title && link) results.push({ rank: i + 1, title, link });
  });

  // fallback selector (h3 inside anchors)
  if (results.length === 0) {
    $('a h3').each((i, el) => {
      const h3 = $(el);
      const a = h3.closest('a');
      const title = h3.text().trim();
      let link = a.attr('href');
      if (link && link.startsWith('/url?q=')) {
        link = decodeURIComponent(link.split('/url?q=')[1].split('&sa=')[0]);
      }
      if (title && link) results.push({ rank: i + 1, title, link });
    });
  }

  return results;
}

export async function POST(req) {
  try {
    if (!TOKEN) return NextResponse.json({ error: 'Missing CRAWLBASE_TOKEN' }, { status: 500 });

    const body = await req.json().catch(() => ({}));
    const { keywords = [], maxPerQuery = 10 } = body;

    const queries = (Array.isArray(keywords) ? keywords : [])
      .map(s => String(s || '').trim())
      .filter(Boolean);

    if (queries.length === 0) {
      return NextResponse.json({ error: 'No keywords provided' }, { status: 400 });
    }

    const all = {};
    for (const q of queries) {
      const list = await fetchSerp(q);
      all[q] = list.slice(0, maxPerQuery);
    }

    return NextResponse.json({ ok: true, results: all });
  } catch (err) {
    return NextResponse.json({ error: String(err?.message || err) }, { status: 500 });
  }
}
