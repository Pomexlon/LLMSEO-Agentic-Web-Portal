// src/amplifyConfig.ts
import { Amplify } from 'aws-amplify';

export function initAmplify() {
  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId: 'eu-west-2_NtCCcE0jo',                 // your pool id
        userPoolClientId: '6l7qjgjbtnc4hgi6jihrih08fu',    // NEW public (no-secret) client id
        loginWith: {
          oauth: {
            domain: 'llmseo-portal.auth.eu-west-2.amazoncognito.com', // no https://
            scopes: ['email', 'openid', 'profile'],
            redirectSignIn: ['http://localhost:3000/'],
            redirectSignOut: ['http://localhost:3000/'],
            responseType: 'code'
          }
        }
      }
    }
  });
}

