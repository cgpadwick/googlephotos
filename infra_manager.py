import argparse
from pathlib import Path
import yaml
from google.cloud import pubsub_v1


def display_menu():
    print("\n\nInfra Manager Menu")
    print("\n")
    print("1. Build infra")
    print("2. Teardown infra")
    print("3. Exit")
    print("\n")


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
    for topic_name, subscribers in data.get("topics", {}).items():
        # Create or get topic
        topic_path = publisher.topic_path(project_id, topic_name)

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
        for subscriber_name in subscribers:
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


import yaml
from google.cloud import pubsub_v1


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
    for topic_name, subscribers in data.get("topics", {}).items():
        # Delete topic
        topic_path = publisher.topic_path(project_id, topic_name)
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
        for subscriber_name in subscribers:
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
        elif choice == "2":
            destroy_topics_and_subscribers_from_yaml(args.configfile)
        elif choice == "3":
            print("Exiting")
            break
        else:
            print("Invalid choice. Please try again.")
