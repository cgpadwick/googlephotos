// Imports the Secret Manager library
const {SecretManagerServiceClient} = require('@google-cloud/secret-manager');

// Instantiates a client
const client = new SecretManagerServiceClient();

async function getSecret() {
  const [version] = await client.accessSecretVersion({
    name: 'projects/cgp-project/secrets/svcacct/versions/latest',
  });
  const payload = version.payload.data.toString('utf8');
  const credentials = JSON.parse(payload);
  return credentials;
}

module.exports = { getSecret };