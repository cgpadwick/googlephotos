// pages/image-gallery.js

import React, { useEffect, useState } from 'react';
import {
  getFirestore, collection, query, limit, orderBy, getDocs, startAfter,
} from 'firebase/firestore';

import firebaseApp from '../firebase/firebase';

import SearchInterface from '../components/InstantSearch';

import '../styles/styles.css';

async function fetchSignedUrls(bucketName, fileNames) {
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

const fetchFromDb = async (lastVisible = null) => {
  const db = getFirestore(firebaseApp, 'photos');
  console.log(db);

  const collectionRef = collection(db, 'customers', 'b8e49401-86fb-48ab-ad3d-33a29c301fa1', 'images');
  let thequery = null;

  if (lastVisible) {
    thequery = query(collectionRef, orderBy('acquisition_time'), startAfter(lastVisible), limit(12));
  } else {
    thequery = query(collectionRef, orderBy('acquisition_time'), limit(12));
  }

  const snapshot = await getDocs(thequery);
  let lastVisibleDocument = null;

  const fileNames = snapshot.docs.map((doc) => doc.data().blob_name);

  if (!snapshot.empty) {
    lastVisibleDocument = snapshot.docs[snapshot.docs.length - 1];
  }

  return { fileNames, lastVisibleDocument };
};

function ImageGallery() {
  const [images, setImages] = useState([]);
  const [lastVisible, setLastVisible] = useState(null);

  const handleForwardClick = async () => {
    const { fileNames, lastVisibleDocument } = await fetchFromDb(lastVisible);
    setLastVisible(lastVisibleDocument);

    const bucketName = 'cgp-photos-export';
    fetchSignedUrls(bucketName, fileNames)
      .then((signedUrls) => {
        signedUrls.forEach((item) => console.log(item));
        setImages(signedUrls);
        // Use signed URLs to display images or download files
        // console.log(signedUrls);
      })
      .catch((error) => console.error(error));
  };

  useEffect(() => {
    handleForwardClick();
  }, []);

  return (
    <div>
      <h1>Image Gallery</h1>
      <SearchInterface />
      <button onClick={handleForwardClick}>Forward</button>
      <div className="gallery">
        {images.map((img) => (
          <div key={img.fileName} className="img">
            <img src={img.url} alt={img.fileName} />
            <div className="image-text">{img.fileName}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ImageGallery;
