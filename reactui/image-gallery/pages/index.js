// pages/index.js

import React from 'react';
import Link from 'next/link';

import GoogleSignIn from '../components/GoogleSignIn';

function HomePage() {
  return (
    <div>
      <h1>Welcome to My Image Gallery</h1>
      <p>This is a simple image gallery web app built with React, Next.js, and Firebase.</p>
      <GoogleSignIn />
      <p>Click the button below to view the image gallery:</p>
      <Link href="/image-gallery">
        Go to Image Gallery
      </Link>
    </div>
  );
}

export default HomePage;
