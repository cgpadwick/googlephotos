// firebase/firebase.js
import { initializeApp } from 'firebase/app';
import { getAuth } from "firebase/auth";

async function fetchFirebaseConfig() {
  const response = await fetch('/api/firebaseConfig', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: '', // Optional body content
  });

  if (!response.ok) {
    throw new Error('Failed to fetch Firebase config');
  }

  return await response.json();
}

async function initializeFirebase() {
  const firebaseConfig = await fetchFirebaseConfig();
  const firebaseApp = initializeApp(firebaseConfig);
  return firebaseApp;
}

const firebaseApp = await initializeFirebase().catch(error => {
  console.error('Error initializing Firebase:', error);
});

const auth = firebaseApp ? getAuth(firebaseApp) : null;

export { firebaseApp, auth };
