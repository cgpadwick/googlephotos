// pages/image-gallery.js

import React, { useEffect, useState } from 'react';
import SearchInterface from '../components/InstantSearch';
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

  return (
    <div>
      <h1>Searchable Image Gallery</h1>
      <SearchInterface />
    </div>
  );
}

export default ImageGallery;
