require('dotenv').config();
const { CrawlingAPI } = require('proxycrawl');
const cheerio = require('cheerio');
const fs = require('fs');

const token = process.env.CRAWLBASE_TOKEN;
if (!token) { console.error('Missing CRAWLBASE_TOKEN in .env'); process.exit(1); }
const api = new CrawlingAPI({ token });

const input = (process.env.KEYWORDS || '').trim();
const queries = input
  ? input.split(',').map(s => s.trim()).filter(Boolean)
  : [
      'oxygen concentrators UK',
      'best portable oxygen concentrators UK',
      'NHS approved oxygen concentrators UK'
    ];

async function crawlQueries() {
  const allResults = {};
  for (const query of queries) {
    const url = `https://www.google.com/search?q=${encodeURIComponent(query)}&hl=en-GB`;
    try {
      const response = await api.get(url);
      if (response.statusCode !== 200) {
        console.error(`Error for "${query}": HTTP ${response.statusCode}`);
        continue;
      }
      const $ = cheerio.load(response.body);
      const results = [];

      $('div.ezO2md').each((i, el) => {
        const title = $(el).find('span.CVA68e').text().trim();
        let link = $(el).find('a').attr('href');
        if (link && link.startsWith('/url?q=')) {
          link = decodeURIComponent(link.split('/url?q=')[1].split('&sa=')[0]);
        }
        if (title && link) results.push({ rank: i + 1, title, link });
      });

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

      allResults[query] = results;
      console.log(`✅ ${query}: ${results.length} results`);
    } catch (err) {
      console.error(`Request failed (${query}):`, err?.message || err);
    }
  }

  fs.writeFileSync('results.json', JSON.stringify(allResults, null, 2));
  console.log('💾 Saved results.json');
}

crawlQueries();
