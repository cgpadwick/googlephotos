// pages/api/typesenseConfig.js
const { SecretManagerServiceClient } = require('@google-cloud/secret-manager');
const client = new SecretManagerServiceClient();

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Only POST requests allowed' });
  }

  try {
    const [version] = await client.accessSecretVersion({
      name: 'projects/cgp-project/secrets/typesense/versions/latest',
    });

       const configJson = version.payload.data.toString('utf8');
       const typesenseConfig = JSON.parse(configJson);

       res.status(200).json(typesenseConfig);
  } catch (error) {
    console.error('Error fetching Typesense config:', error);
    res.status(500).json({ error: 'Error fetching Typesense config' });
  }
}
