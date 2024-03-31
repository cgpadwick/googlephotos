import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, "../src")
import yaml

from dotenv import load_dotenv

from google.oauth2 import service_account
from google.cloud import pubsub_v1
from google.cloud import functions_v1

import photosapp


class DatabaseManager(object):
    def __init__(self, config_file):
        """
        Initialize the class with the provided configuration file.

        Parameters:
            config_file (str): The path to the configuration file.

        Returns:
            None
        """
        self.config_file = config_file
        self.config = self.load_config()
        self.db_helper = photosapp.DatabaseHelper(config_file)

    def load_config(self):
        """
        Load the configuration file and return the loaded configuration.

        Parameters:
            self (object): The instance of the class.

        Returns:
            dict: The loaded configuration.
        """
        with open(self.config_file, "r") as file:
            config = yaml.safe_load(file)
        return config

    def display_menu(self):
        """
        Display the infrastructure manager menu options to the user.
        """
        print("\n\nDatabase Manager Menu")
        print("\n")
        print("1. List Collections")
        print("2. Delete a specific collection")
        print("3. Delete all collections from database")
        print("4. Exit")
        print("\n")

    def clear_firestore_collections(self):
        """
        Method to clear all collections in Firestore.
        """
        self.db_helper.clear_firestore_collections()

    def list_collections(self):
        """
        Method to list all collections in Firestore.
        """
        print("\n\nCollections:")
        for collection in self.db_helper.get_collections():
            print(f"{collection.id}")
        print("\n\n")

    def delete_collection(self):
        """
        Delete a collection by name after user input.
        If the collection exists, deletes it and prints a success message.
        """
        print("\n\nDelete collection:\n\n")
        collection_name = input("Enter the name of the collection to delete: ")
        self.db_helper.delete_collection(collection_name)

    def run(self):
        """
        Run the main loop for the program, displaying a menu and handling user input
        to perform various actions.
        """

        while True:
            self.display_menu()
            choice = input("Enter your choice: ")
            if choice == "1":
                self.list_collections()
            elif choice == "2":
                self.delete_collection()
            elif choice == "3":
                self.clear_firestore_collections()
            elif choice == "4":
                print("Exiting")
                break
            else:
                print("Invalid choice. Please try again.")


class InfraManager(object):
    def __init__(self, config_file):
        """
        Initialize the class with the provided configuration file.

        Parameters:
            config_file (str): The path to the configuration file.

        Returns:
            None
        """
        self.config_file = config_file
        self.config = self.load_config()
        self.database_manager = DatabaseManager(self.config_file)

    def load_config(self):
        """
        Load the configuration file and return the loaded configuration.

        Parameters:
            self (object): The instance of the class.

        Returns:
            dict: The loaded configuration.
        """
        with open(self.config_file, "r") as file:
            config = yaml.safe_load(file)
        return config

    def display_menu(self):
        """
        Display the infrastructure manager menu options to the user.
        """
        print("\n\nInfra Manager Menu")
        print("\n")
        print("1. Build infra")
        print("2. Teardown infra")
        print("3. Manage database")
        print("4. Exit")
        print("\n")

    def _get_function_name(self, function_name, project_id, location):
        """
        Retrieves the full function name based on the provided function_name, project_id, and location.

        Args:
            function_name (str): The name of the function.
            project_id (str): The ID of the project.
            location (str): The location of the function.

        Returns:
            str: The full function name.
        """
        name = f"projects/{project_id}/locations/{location}/functions/{function_name}"
        return name

    def _func_exists(self, name):
        """
        A function that checks if a function exists in the Cloud Functions service.

        Parameters:
        name (str): The name of the function to check.

        Returns:
        bool: True if the function exists, False otherwise.
        """
        client = functions_v1.CloudFunctionsServiceClient()
        try:
            client.get_function(name=name)
            return True
        except Exception:
            return False

    def delete_cloud_functions(self):
        """
        Delete cloud functions based on the configuration provided.
        """

        # Initialize the Cloud Functions client
        client = functions_v1.CloudFunctionsServiceClient()

        for function_name, attr in self.config.get("functions", {}).items():

            name = self._get_function_name(
                function_name, self.config["project_id"], attr["location"]
            )
            if not self._func_exists(name):
                print("no function exists with name: " + function_name)
                continue

            # Delete the Cloud Function
            client.delete_function(name=name)
            print(f"Cloud Function '{function_name}' deleted successfully.")

    def create_cloud_functions(self):
        """
        Load the Cloud Function configuration from the YAML file
        """

        load_dotenv()

        target_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        creds_path = self.config["accounts"]["service_account"]["path_to_credentials"]
        source_credentials = service_account.Credentials.from_service_account_file(
            creds_path, scopes=target_scopes
        )

        # Initialize the Cloud Functions client
        client = functions_v1.CloudFunctionsServiceClient(
            credentials=source_credentials
        )

        for function_name, attr in self.config.get("functions", {}).items():

            print(f"Creating function: {function_name}")

            name = self._get_function_name(
                function_name, self.config["project_id"], attr["location"]
            )

            if self._func_exists(name):
                print("function already exists: " + function_name)
                continue

            trigger_topic = (
                f"projects/{self.config['project_id']}/topics/{attr['trigger_topic']}"
            )
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
                location=f"projects/{self.config['project_id']}/locations/{attr['location']}",
                function=function,
            )

            operation = client.create_function(request=request)
            result = operation.result()

            print(f"Cloud Function '{function_name}' created successfully.")

    def create_topics_and_subscribers(self):
        """
        Generate topics and subscribers based on the configuration provided.
        """

        project_id = self.config.get("project_id")

        # Initialize Pub/Sub clients
        publisher = pubsub_v1.PublisherClient()
        subscriber = pubsub_v1.SubscriberClient()

        # Loop through topics
        for topic, attr in self.config.get("topics", {}).items():
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

    def destroy_topics_and_subscribers(self):
        """
        Deletes all topics and subscribers in the Pub/Sub system.

        This function iterates through all the topics and subscribers defined in the configuration
        and deletes them one by one. It first retrieves the project ID from the configuration. Then,
        it initializes the Pub/Sub clients for publishing and subscribing. Next, it loops through
        each topic in the configuration and checks if it exists. If it does, it deletes the topic and
        prints a message indicating that the topic has been deleted. If it does not exist, it prints
        a message indicating that the topic does not exist. After that, it loops through each
        subscriber of the topic and checks if the corresponding subscription exists. If it does,
        it deletes the subscription and prints a message indicating that the subscription has been
        deleted. If it does not exist, it prints a message indicating that the subscription does
        not exist.

        Parameters:
            self (object): The instance of the current class.

        Returns:
            None
        """

        project_id = self.config.get("project_id")

        # Initialize Pub/Sub clients
        publisher = pubsub_v1.PublisherClient()
        subscriber = pubsub_v1.SubscriberClient()

        # Loop through topics
        for topic, attr in self.config.get("topics", {}).items():
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

    def run(self):
        """
        Run the main loop for the program, displaying a menu and handling user input to perform various actions.
        """

        while True:
            self.display_menu()
            choice = input("Enter your choice: ")
            if choice == "1":
                self.create_topics_and_subscribers()
                self.create_cloud_functions()
            elif choice == "2":
                self.delete_cloud_functions()
                self.destroy_topics_and_subscribers()
            elif choice == "3":
                self.database_manager.run()
            elif choice == "4":
                print("Exiting")
                break
            else:
                print("Invalid choice. Please try again.")


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

    manager = InfraManager(args.configfile)
    manager.run()
