import React, { useState, useEffect } from 'react';
import { InstantSearch, Hits, Configure, connectSearchBox, Highlight, Pagination } from 'react-instantsearch-dom';
import TypesenseInstantSearchAdapter from 'typesense-instantsearch-adapter';
import { fetchSignedUrls } from '../pages/image-gallery.js';

// Initialize Typesense adapter
const typesenseInstantsearchAdapter = new TypesenseInstantSearchAdapter({
  server: {
    apiKey: process.env.NEXT_PUBLIC_TYPESENSE_API_KEY,
    nodes: [{
      host: process.env.NEXT_PUBLIC_TYPESENSE_HOST,
      port: '443',
      protocol: 'https'
    }],
  },
  additionalSearchParameters: {
    queryBy: 'caption',
  },
});
const searchClient = typesenseInstantsearchAdapter.searchClient;

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
    // Assume bucket_name is available or predefined if not part of hit
    fetchSignedUrls(hit.bucket_name, [hit.blob_name])
      .then(signedUrls => {
        if (signedUrls.length > 0) {
          setImageUrl(signedUrls[0].url);  // Assuming signedUrls is an array with url property
        }
      })
      .catch(error => {
        console.error('Error fetching signed URL:', error);
        setImageUrl('/path/to/default/image.jpg'); // Fallback image
      });
  }, [hit.blob_name, hit.bucket_name]);

  return (
    <div className="hit">
      {imageUrl && <img src={imageUrl} alt={hit.blob_name} className="search-image" />}
      <div>
        <Highlight attribute="caption" hit={hit} tagName="mark"/>
      </div>
    </div>
  );
};

export default function SearchInterface() {
  return (
    <InstantSearch searchClient={searchClient} indexName="images">
      <CustomSearchBox />
      <Configure hitsPerPage={20} /> 
      <Hits hitComponent={Hit} />
    </InstantSearch>
  );
}
