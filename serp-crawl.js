const { CrawlingAPI } = require('proxycrawl');
const cheerio = require('cheerio');
const fs = require('fs');

const api = new CrawlingAPI({ token: 'A9IPVVqYJdA2-tIO3Hrt5Q' });

const queries = [
  'oxygen concentrators UK',
  'best portable oxygen concentrators UK',
  'NHS approved oxygen concentrators UK'
];

async function crawlQueries() {
  let allResults = {};

  for (let query of queries) {
    const url = `https://www.google.com/search?q=${encodeURIComponent(query)}`;

    try {
      const response = await api.get(url);
      if (response.statusCode === 200) {
        console.log(`\n✅ Results for "${query}":\n`);

        const $ = cheerio.load(response.body);
        let results = [];

        $('div.ezO2md').each((index, element) => {
          const title = $(element).find('span.CVA68e').text();
          let link = $(element).find('a').attr('href');
          if (link && link.startsWith('/url?q=')) {
            link = decodeURIComponent(link.split('/url?q=')[1].split('&sa=')[0]);
          }
          results.push({ rank: index + 1, title, link });
          console.log(`${index + 1}. ${title}\nDirect Link: ${link}\n`);
        });

        allResults[query] = results;

      } else {
        console.error(`🚨 Error (${query}):`, response.statusCode);
      }
    } catch (error) {
      console.error(`Request failed (${query}):`, error);
    }
  }

  // Clearly save results to JSON file
  fs.writeFileSync('results.json', JSON.stringify(allResults, null, 2));
  console.log('\n📁 Results successfully saved in results.json\n');
}

crawlQueries();

