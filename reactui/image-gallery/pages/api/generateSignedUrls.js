import { Storage } from '@google-cloud/storage';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).send({ message: 'Only POST requests allowed' });
  }

  try {
    const storage = new Storage({
      projectId: 'cgp-project',
    });

    const { bucketName, fileNames } = req.body; // Expect bucketName and an array of fileNames in the request body

    const promises = fileNames.map(async (fileName) => {
      const options = {
        version: 'v4',
        action: 'read',
        expires: Date.now() + 15 * 60 * 1000, // 15 minutes
      };

      // Attempt to generate a signed URL for the fileName
      try {
        const [url] = await storage.bucket(bucketName).file(fileName).getSignedUrl(options);
        // Return both fileName and signed URL
        return { fileName, url, success: true };
      } catch (error) {
        // In case of an error, log it and return the fileName and an error indicator
        console.error(`Error generating signed URL for ${fileName}:`, error);
        return {
          fileName, url: null, success: false, error: error.message,
        };
      }
    });

    // Wait for all promises to resolve
    const results = await Promise.all(promises);

    // Send back the array of results, each including the fileName and the signed URL (or null if an error occurred)
    res.status(200).json(results);
  } catch (error) {
    console.error('Error generating signed URLs:', error);
    res.status(500).json({ error: 'Error generating signed URLs' });
  }
}
