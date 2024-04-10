import React from 'react';
import { getAuth, signInWithPopup, GoogleAuthProvider } from 'firebase/auth';
import firebaseApp from '../firebase/firebase';

function GoogleSignIn() {
  const handleSignInWithGoogle = async () => {
    const auth = getAuth(firebaseApp);
    const provider = new GoogleAuthProvider();
    try {
      await signInWithPopup(auth, provider);
      console.log('Successfully signed in with Google!');
    } catch (error) {
      console.error('Error signing in with Google:', error.message);
    }
  };

  return (
    <div>
      <h2>Sign In with Google</h2>
      <button onClick={handleSignInWithGoogle}>Sign in with Google</button>
    </div>
  );
}

export default GoogleSignIn;
