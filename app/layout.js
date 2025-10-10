'use client';
import { useEffect } from 'react';
import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import { initAmplify } from '../src/amplifyConfig';

export default function RootLayout({ children }) {
  useEffect(() => { initAmplify(); }, []);
  return (
    <html lang="en">
      <body>
        <Authenticator loginMechanisms={['email']}>
  {children}
        </Authenticator>
      </body>
    </html>
  );
}

