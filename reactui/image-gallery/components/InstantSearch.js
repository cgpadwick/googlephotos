import React, { useState, useEffect } from 'react';
import { InstantSearch, Hits, Configure, connectSearchBox, Highlight, Pagination } from 'react-instantsearch-dom';
import TypesenseInstantSearchAdapter from 'typesense-instantsearch-adapter';
import { fetchSignedUrls } from '../pages/image-gallery.js';

async function fetchTypesenseConfig() {
  const response = await fetch('/api/typesenseConfig', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
     },
     body: '',
   });

   if (!response.ok) {
      throw new Error('Failed to fetch Typesense config');
   }

   return await response.json();
}

async function initializeTypesenseAdapter() {
 const config = await fetchTypesenseConfig();

 const adapter = new TypesenseInstantSearchAdapter({
   server: {
     apiKey: config.apiKey,
     nodes: [{
       host: config.host,
       port: '443',
       protocol: 'https',
     }],
   },
   additionalSearchParameters: {
     queryBy: 'caption',
   },
 });

 return adapter.searchClient;
}

// Custom search box component
const SearchBox = ({ refine }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (event) => {
    event.preventDefault();
    refine(query);
  };

  return (
    <form onSubmit={handleSubmit} className="search-form">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search for images..."
      />
      <button type="submit" className="search-button">Search</button>
    </form>
  );
};

const CustomSearchBox = connectSearchBox(SearchBox);

// Component displaying search hits
const Hit = ({ hit }) => {
  const [imageUrl, setImageUrl] = useState('');

  useEffect(() => {
    console.log(hit);
    // Assume bucket_name is available or predefined if not part of hit
    fetchSignedUrls(hit.bucket_name, [hit.rr_img])
      .then(signedUrls => {
        if (signedUrls.length > 0) {
          setImageUrl(signedUrls[0].url);  // Assuming signedUrls is an array with url property
        }
      })
      .catch(error => {
        console.error('Error fetching signed URL:', error);
        setImageUrl('/path/to/default/image.jpg'); // Fallback image
      });
  }, [hit.rr_img, hit.bucket_name]);

  return (
    <div>
      {imageUrl && <img src={imageUrl} alt={hit.rr_img} />}
      <div>
        <Highlight attribute="caption" hit={hit} tagName="mark" />
      </div>
    </div>
  );
};

export default function SearchInterface() {

  const [searchClient, setSearchClient] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    initializeTypesenseAdapter()
      .then(setSearchClient)
      .catch(setError);
  }, []);

  if (error) {
    return <div>Error initializing Typesense: {error.message}</div>;
  }

  if (!searchClient) {
    return <div>Loading Typesense...</div>;
  }

  return (
    <InstantSearch searchClient={searchClient} indexName='images'>
      <CustomSearchBox />
      <Configure hitsPerPage={50} /> 
      <div>
        <Hits hitComponent={Hit} />
      </div>
    </InstantSearch>
  );
}
