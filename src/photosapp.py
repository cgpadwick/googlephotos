import datetime
import json
import uuid
import yaml

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from google.cloud import firestore_v1
from google.cloud import pubsub_v1
from google.oauth2 import service_account
from google.cloud import storage


CUSTOMERTABLE = "customers"
IMAGESTABLE = "images"


class PubSubHelper(object):
    """A class to represent a PubSub object."""

    def __init__(self, config_file):
        """Initialize the PubSub object."""
        self.config_file = config_file
        self.config = self.load_config()

        # Create the topic path
        self.publisher = pubsub_v1.PublisherClient()

    def load_config(self):
        """Load the configuration file and return the loaded configuration."""
        with open(self.config_file, "r") as file:
            config = yaml.safe_load(file)
        return config

    def publish_message(self, topic_name, message):
        """Publish a message to a topic."""
        message_data = json.dumps(message).encode("utf-8")
        topic_path = self.publisher.topic_path(self.config["project_id"], topic_name)
        future = self.publisher.publish(topic_path, message_data)
        message_id = future.result()
        return message_id


class GCStoragehelper(object):
    """A class to represent a Google Cloud Storage object."""

    def __init__(self, config_file):
        """Initialize the GCStorage object."""
        self.config_file = config_file
        self.config = self.load_config()

        # Get the contents of the bucket.
        creds_path = self.config["accounts"]["service_account"]["path_to_credentials"]
        source_credentials = service_account.Credentials.from_service_account_file(
            creds_path
        )
        self.storage_client = storage.Client(credentials=source_credentials)

    def load_config(self):
        """Load the configuration file and return the loaded configuration."""
        with open(self.config_file, "r") as file:
            config = yaml.safe_load(file)
        return config

    def get_bucket(self, bucket_name):
        """Get the contents of a bucket."""
        bucket = self.storage_client.get_bucket(bucket_name)
        return bucket

    def get_blobs(self, bucket_name):
        """Get the contents of a bucket."""
        bucket = self.storage_client.get_bucket(bucket_name)
        blobs = bucket.list_blobs()
        return blobs


class DatabaseHelper(object):
    """A class to represent a database."""

    def __init__(self, config_file, test_mode=False):
        """Initialize the Database object."""
        self.config_file = config_file
        self.config = self.load_config()

        creds_path = self.config["accounts"]["service_account"]["path_to_credentials"]
        creds = credentials.Certificate(creds_path)
        if not firebase_admin._apps:
            _ = firebase_admin.initialize_app(creds)

        if test_mode:
            self.db = firestore.Client(database=self.config["firestore"]["testdb_name"])
        else:
            self.db = firestore.Client(database=self.config["firestore"]["database_name"])

    def load_config(self):
        """Load the configuration file and return the loaded configuration."""
        with open(self.config_file, "r") as file:
            config = yaml.safe_load(file)
        return config

    def check_unique_email(self, email):
        """Check if the email is unique in the database."""
        field_filter = firestore_v1.base_query.FieldFilter("email", "==", email)
        doc_ref = self.db.collection(CUSTOMERTABLE).where(filter=field_filter).limit(1)
        docs = doc_ref.get()
        return len(docs) == 0

    def get_customer(self, email):
        """Retrieve a customer in the database."""
        field_filter = firestore_v1.base_query.FieldFilter("email", "==", email)
        doc_ref = self.db.collection(CUSTOMERTABLE).where(filter=field_filter).limit(1)
        docs = doc_ref.get()
        assert len(docs) == 1
        customer = docs[0].to_dict()
        return customer

    def insert_customer(self, customer):
        """Insert a customer into the database."""
        doc_ref = self.db.collection(CUSTOMERTABLE).document(str(customer.uuid))
        doc_ref.set(customer.to_dict())

    def get_db(self):
        """Return the database object."""
        return self.db

    def get_collection(self, collection_name):
        """Return a collection from the Firestore database."""
        collections = self.db.collections()
        for collection in collections:
            if collection.id == collection_name:
                return collection
        return None

    def clear_firestore_collections(self):
        """
        Method to clear all collections in Firestore.
        """
        for collection in self.db.collections():
            print(
                f'deleting {collection.id} from {self.config["firestore"]["database_name"]}'
            )
            self.db.recursive_delete(collection)

    def get_collections(self):
        """
        Method to list all collections in Firestore.
        """
        return self.db.collections()

    def delete_collection(self, collection_name):
        """Delete a collection from the Firestore database."""
        collection_ref = self.get_collection(collection_name)
        if not collection_ref:
            print(f"Collection '{collection_name}' does not exist.")
            return

        # Delete the collection
        self.db.recursive_delete(collection_ref)

        print(f"Collection '{collection_name}' deleted successfully.")


class Customer(object):
    """A class to represent a customer."""

    def __init__(self, name, email, phone, bucket_name):
        """Initialize the Customer object."""
        self.name = name
        self.email = email
        self.phone = phone
        self.bucket_name = bucket_name
        self.uuid = uuid.uuid4()
        self.created_at = datetime.datetime.now()

    def to_dict(self):
        """Export customer attributes as a dictionary."""
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "bucket_name": self.bucket_name,
            "uuid": str(self.uuid),
            "created_at": str(self.created_at),
        }

    def __repr__(self):
        """Return a string representation of the customer."""
        return f"Customer({self.name}, {self.email}, {self.phone}, {self.bucket_name}, {self.uuid}, {self.created_at})"
