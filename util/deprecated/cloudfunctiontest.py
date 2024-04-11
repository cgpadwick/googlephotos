import os
from google.cloud import functions_v1
from google.oauth2 import service_account
from google.auth import impersonated_credentials
from dotenv import load_dotenv


def deploy_cloud_function(project_id, location, function_name, entry_point, topic_name):

    load_dotenv()

    target_scopes=["https://www.googleapis.com/auth/cloud-platform"]
    source_credentials = (
        service_account.Credentials.from_service_account_file(
            '_secrets_/cgp-project-c6daf9dd8063.json',
            scopes=target_scopes))

    """Deploy a Cloud Function triggered by Pub/Sub event."""
    client = functions_v1.CloudFunctionsServiceClient(credentials=source_credentials)

    # Construct the fully qualified topic name
    topic = f"projects/{project_id}/topics/{topic_name}"

    function = functions_v1.CloudFunction()
    function.entry_point = entry_point
    function.runtime = "python39"
    function.name = (
        f"projects/{project_id}/locations/{location}/functions/{function_name}"
    )
    function.max_instances = 1
    function.event_trigger = functions_v1.EventTrigger()
    function.event_trigger.event_type = "google.pubsub.topic.publish"
    function.event_trigger.resource = topic
    function.source_repository = functions_v1.SourceRepository()
    function.source_repository.url = "https://source.developers.google.com/projects/cgp-project/repos/github_cgpadwick_googlephotos/moveable-aliases/main/paths/cloud_functions/pubsub_trigger/"
    function.environment_variables = {"OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")}

    # https://source.developers.google.com/projects/$PROJECT_ID/repos/hello-world/moveable-aliases/master/paths/gcf_hello_world

    request = functions_v1.CreateFunctionRequest(
        location=f"projects/{project_id}/locations/{location}",
        function=function,
    )

    # Create or update the Cloud Function
    operation = client.create_function(request=request)
    result = operation.result()

    print(f"Cloud Function deployed successfully: {result.name}")


# Example Cloud Function code
def pubsub_trigger(event, context):
    """Triggered by a Pub/Sub message."""
    import base64

    print(
        f"Received Pub/Sub message: {base64.b64decode(event['data']).decode('utf-8')}"
    )


# Example usage
if __name__ == "__main__":
    project_id = "cgp-project"
    location = "us-central1"
    function_name = "pubsub_function"
    entry_point = "hello_pubsub"
    topic_name = "cgp-target-topic"

    deploy_cloud_function(project_id, location, function_name, entry_point, topic_name)
