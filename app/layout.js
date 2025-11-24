'use client';
import { useEffect } from 'react';
import { initAmplify } from '../src/amplifyConfig';

export default function RootLayout({ children }) {
  useEffect(() => { initAmplify(); }, []);

  return (
    <html lang="en">
      <body>
        <div>
          {children}
        </div>
      </body>
    </html>
  );
}

