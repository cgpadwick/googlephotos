// pages/image-gallery.js

import React, { useEffect, useState } from 'react';
import SearchInterface from '../components/InstantSearch';
import {firebaseApp, auth} from '../firebase/firebase';
import { onAuthStateChanged } from 'firebase/auth';
import { useRouter } from 'next/router';
import '../styles/styles.css';

export async function fetchSignedUrls(bucketName, fileNames) {
  const response = await fetch('/api/generateSignedUrls', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ bucketName, fileNames }),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch signed URLs');
  }

  const data = await response.json();
  return data;
}

function ImageGallery() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleError = () => {
    router.push('/');
  }

  useEffect(() => {
    // Check if user is logged in
    const unsubscribe = onAuthStateChanged(auth, authenticatedUser => {
      if (authenticatedUser) {
        // User is signed in.
        setUser(authenticatedUser);
      } else {
        // No user is signed in. Redirect to login page.
        setError('You must be logged in to access this page.');
      }
      setLoading(false);
    });

    // Clean up the subscription
    return () => unsubscribe();
  }, [router]);

  if (loading) {
    return (
      <div className="loading-container">
        Checking authentication status... <span className="spinner"></span>
      </div>
    );
  }

  if (!user) {
    return (
      <div>
        {error && <div className="error-message">{error}</div>}
        <button onClick={handleError}>Go To Login</button>
      </div>
    );
  }

  return (
    <div>
      <h1>Searchable Image Gallery</h1>
      <SearchInterface />
    </div>
  );
}

export default ImageGallery;
