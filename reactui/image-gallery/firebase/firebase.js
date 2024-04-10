// firebase/firebase.js

import { initializeApp } from 'firebase/app';

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: 'AIzaSyC8tche8xOFkdwHop1p0qHmMLzEnNDEWWk',
  authDomain: 'cgp-project.firebaseapp.com',
  projectId: 'cgp-project',
  storageBucket: 'cgp-project.appspot.com',
  messagingSenderId: '913530702391',
  appId: '1:913530702391:web:43b0c6352abd58977d0db2',
};

const firebaseApp = initializeApp(firebaseConfig);

export default firebaseApp;
