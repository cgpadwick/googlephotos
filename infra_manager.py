import argparse
from dotenv import load_dotenv
import os
from pathlib import Path
import yaml
from google.cloud import pubsub_v1
from google.cloud import functions_v1


def display_menu():
    print("\n\nInfra Manager Menu")
    print("\n")
    print("1. Build infra")
    print("2. Teardown infra")
    print("3. Exit")
    print("\n")


def get_function_name(function_name, project_id, location):
    name = f"projects/{project_id}/locations/{location}/functions/{function_name}"
    return name


def func_exists(name):
    client = functions_v1.CloudFunctionsServiceClient()
    try:
        client.get_function(name=name)
        return True
    except Exception:
        return False


def delete_cloud_functions_from_yaml(config_file):
    """
    Load the Cloud Function configuration from the YAML file
    Initialize the Cloud Functions client
    Delete the Cloud Function
    Print a success message after deleting the Cloud Function
    """
    # Load the Cloud Function configuration from the YAML file
    with open(config_file, "r") as file:
        data = yaml.safe_load(file)

    # Initialize the Cloud Functions client
    client = functions_v1.CloudFunctionsServiceClient()

    for function_name, attr in data.get("functions", {}).items():

        name = get_function_name(function_name, data["project_id"], attr["location"])
        if not func_exists(name):
            print("no function exists with name: " + function_name)
            continue

        # Delete the Cloud Function
        client.delete_function(name=name)
        print(f"Cloud Function '{function_name}' deleted successfully.")


def create_cloud_functions_from_yaml(config_file):
    """
    Load the Cloud Function configuration from the YAML file
    """

    load_dotenv()

    # Load the Cloud Function configuration from the YAML file
    with open(config_file, "r") as file:
        data = yaml.safe_load(file)

    # Initialize the Cloud Functions client
    client = functions_v1.CloudFunctionsServiceClient()

    for function_name, attr in data.get("functions", {}).items():

        name = get_function_name(function_name, data["project_id"], attr["location"])

        if func_exists(name):
            print("function already exists: " + function_name)
            continue

        trigger_topic = f"projects/{data['project_id']}/topics/{attr['trigger_topic']}"
        function = functions_v1.CloudFunction()
        function.entry_point = attr["entry_point"]
        function.runtime = attr["runtime"]
        function.name = name
        function.max_instances = attr["max_instances"]
        function.event_trigger = functions_v1.EventTrigger()
        function.event_trigger.event_type = "google.pubsub.topic.publish"
        function.event_trigger.resource = trigger_topic
        function.source_repository = functions_v1.SourceRepository()
        function.source_repository.url = attr["source_url"]

        envvars = {}
        for var in attr["env_vars"]:
            envvars[var] = os.getenv(var)
        function.environment_variables = envvars

        request = functions_v1.CreateFunctionRequest(
            location=f"projects/{data['project_id']}/locations/{attr['location']}",
            function=function,
        )

        operation = client.create_function(request=request)
        result = operation.result()

        print(f"Cloud Function '{function_name}' created successfully.")


def create_topics_and_subscribers_from_yaml(yaml_file):
    """
    Create topics and subscribers from a YAML file.

    Args:
        yaml_file (str): The path to the YAML file containing the topic and subscriber information.

    Returns:
        None
    """
    # Load YAML file
    with open(yaml_file, "r") as file:
        data = yaml.safe_load(file)

    project_id = data.get("project_id")

    # Initialize Pub/Sub clients
    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()

    # Loop through topics
    for topic, attr in data.get("topics", {}).items():
        # Create or get topic
        topic_path = publisher.topic_path(project_id, attr["name"])

        try:
            topic = publisher.get_topic(request={"topic": topic_path})
        except Exception as e:
            topic = None

        if not topic:
            topic = publisher.create_topic(request={"name": topic_path})
            print(f"Topic created: {topic.name}")
        else:
            print(f"Topic already exists: {topic.name}")

        # Loop through subscribers
        for subscriber_name in attr["subscribers"]:
            # Create or get subscription
            subscription_path = subscriber.subscription_path(
                project_id, subscriber_name
            )
            try:
                subscription = subscriber.get_subscription(
                    request={"subscription": subscription_path}
                )
            except Exception as e:
                subscription = None

            if not subscription:
                subscription = subscriber.create_subscription(
                    request={"name": subscription_path, "topic": topic_path}
                )
                print(f"Subscription created: {subscription.name}")
            else:
                print(f"Subscription already exists: {subscription.name}")


def destroy_topics_and_subscribers_from_yaml(yaml_file):
    """
    Destroy topics and subscribers from a YAML file.

    Parameters:
        yaml_file (str): The path to the YAML file containing topic and subscriber information.

    Returns:
        None
    """

    # Load YAML file
    with open(yaml_file, "r") as file:
        data = yaml.safe_load(file)

    project_id = data.get("project_id")

    # Initialize Pub/Sub clients
    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()

    # Loop through topics
    for topic, attr in data.get("topics", {}).items():
        # Delete topic
        topic_path = publisher.topic_path(project_id, attr["name"])
        try:
            topic = publisher.get_topic(request={"topic": topic_path})
        except Exception as e:
            topic = None

        if topic:
            publisher.delete_topic(request={"topic": topic_path})
            print(f"Topic deleted: {topic_path}")
        else:
            print(f"Topic does not exist: {topic_path}")

        # Loop through subscribers
        for subscriber_name in attr["subscribers"]:
            # Delete subscription
            subscription_path = subscriber.subscription_path(
                project_id, subscriber_name
            )
            try:
                subscription = subscriber.get_subscription(
                    request={"subscription": subscription_path}
                )
            except Exception as e:
                subscription = None

            if subscription:
                subscriber.delete_subscription(
                    request={"subscription": subscription_path}
                )
                print(f"Subscription deleted: {subscription_path}")
            else:
                print(f"Subscription does not exist: {subscription_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--configfile",
        required=True,
        type=Path,
        help="path to the yaml config file",
    )
    args = parser.parse_args()

    if not args.configfile.exists():
        raise ValueError(f"Invalid path specified: {args.configfile}")

    while True:
        display_menu()
        choice = input("Enter your choice: ")
        if choice == "1":
            create_topics_and_subscribers_from_yaml(args.configfile)
            create_cloud_functions_from_yaml(args.configfile)
        elif choice == "2":
            delete_cloud_functions_from_yaml(args.configfile)
            destroy_topics_and_subscribers_from_yaml(args.configfile)
        elif choice == "3":
            print("Exiting")
            break
        else:
            print("Invalid choice. Please try again.")
