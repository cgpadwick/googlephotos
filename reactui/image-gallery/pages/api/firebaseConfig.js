// Assuming you've stored the entire Firebase config as a single JSON object in a secret
const {SecretManagerServiceClient} = require('@google-cloud/secret-manager');
const client = new SecretManagerServiceClient();


export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).send({ message: 'Only POST requests allowed' });
  }

  try {
    const [version] = await client.accessSecretVersion({
      name: 'projects/cgp-project/secrets/photosapp/versions/latest'
    });
    const configJson = version.payload.data.toString('utf8');
    const appConfig = JSON.parse(configJson);

    res.status(200).json(appConfig);
  } catch (error) {
    console.error('Error fetching Firebase config:', error);
    res.status(500).json({ error: 'Error fetching Firebase config' });
  }
}
