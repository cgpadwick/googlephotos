import React, { useEffect, useState } from 'react';
import { InstantSearch, SearchBox, Hits, Stats, Highlight } from "react-instantsearch-dom"
import TypesenseInstantSearchAdapter from "typesense-instantsearch-adapter"

import { fetchSignedUrls } from '../pages/image-gallery.js'

import '../styles/styles.css';


const typesenseInstantsearchAdapter = new TypesenseInstantSearchAdapter({
  server: {
    apiKey: process.env.NEXT_PUBLIC_TYPESENSE_API_KEY,
    nodes: [
      {
        host: process.env.NEXT_PUBLIC_TYPESENSE_HOST,
        port: '443',
        protocol: 'https'
      },
    ],
  },
  // The following parameters are directly passed to Typesense's search API endpoint.
  //  So you can pass any parameters supported by the search endpoint below.
  //  queryBy is required.
  additionalSearchParameters: {
    queryBy: "caption",
  },
})
const searchClient = typesenseInstantsearchAdapter.searchClient
export default function SearchInterface() {

    const Hit = ({ hit }) => {
        const [imageUrl, setImageUrl] = useState(null);
    
        useEffect(() => {
          fetchSignedUrls(hit.bucket_name, [hit.blob_name])
            .then(signedUrls => {
              if (signedUrls.length > 0) {
                setImageUrl(signedUrls[0].url); // Assuming signedUrls is an array of objects with url property
              }
            })
            .catch(error => {
              console.error('Error fetching signed URL:', error);
            });
        }, [hit.blob_name]);
    
        return (
          <div style={{ marginBottom: 10 }}>
            {imageUrl && <img src={imageUrl} alt={hit.blob_name} className="search-image" />}
            <div>
              <Highlight attribute="caption" hit={hit} />
            </div>
          </div>
        );
      };

return (
      <InstantSearch searchClient={searchClient} indexName="images">
        <SearchBox />
        <Stats />
        <Hits hitComponent={Hit} />
      </InstantSearch>
  )
}
