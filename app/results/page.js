'use client';
import { useEffect, useState } from 'react';

export default function ResultsPage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch('/api/results')
      .then(response => response.json())
      .then(data => setData(data))
      .catch(error => console.error('Error fetching data:', error));
  }, []);

  if (!data) {
    return <div className="p-8">Loading...</div>;
  }

  return (
    <div className="p-8 font-sans">
      <h1 className="text-2xl font-bold mb-4">🔍 LLMSEO SERP Results</h1>
      {Object.keys(data).map(query => (
        <div key={query} className="mt-6">
          <h2 className="text-xl font-semibold capitalize mb-3">{query}</h2>
          <ol className="mt-2 list-decimal pl-6 space-y-2">
            {data[query].map(result => (
              <li key={result.rank}>
                <a className="text-blue-600 hover:underline" href={result.link} target="_blank" rel="noopener noreferrer">
                  {result.title}
                </a>
              </li>
            ))}
          </ol>
        </div>
      ))}
    </div>
  );
}

