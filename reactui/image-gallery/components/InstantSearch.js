import { InstantSearch, SearchBox, Hits, Stats } from "react-instantsearch-dom"
import TypesenseInstantSearchAdapter from "typesense-instantsearch-adapter"
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
  const Hit = ({ hit }) => (
    <p>
      {hit.blob_name} - {hit.bucket_name}
    </p>
  )
return (
      <InstantSearch searchClient={searchClient} indexName="images">
        <SearchBox />
        <Stats />
        <Hits hitComponent={Hit} />
      </InstantSearch>
  )
}
