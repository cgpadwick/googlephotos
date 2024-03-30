import datetime
import uuid
import yaml

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


CUSTOMERTABLE = "customers"
IMAGESTABLE = "images"


class DatabaseHelper(object):
    """A class to represent a database."""

    def __init__(self, config_file):
        """Initialize the Database object."""
        self.config_file = config_file
        self.config = self.load_config()

        creds_path = self.config["accounts"]["service_account"]["path_to_credentials"]
        creds = credentials.Certificate(creds_path)
        _ = firebase_admin.initialize_app(creds)
        self.db = firestore.Client(database=self.config["firestore"]["database_name"])

    def check_unique_email(self, email):
        """Check if the email is unique in the database."""
        doc_ref = self.db.collection(CUSTOMERTABLE).where("email", "==", email).limit(1)
        docs = doc_ref.get()
        return len(docs) == 0

    def insert_customer(self, customer):
        """Insert a customer into the database."""
        doc_ref = self.db.collection(CUSTOMERTABLE).document(str(customer.uuid))
        doc_ref.set(customer.to_dict())

    def load_config(self):
        """Load the configuration file and return the loaded configuration."""
        with open(self.config_file, "r") as file:
            config = yaml.safe_load(file)
        return config


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
