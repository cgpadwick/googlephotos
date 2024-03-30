import datetime
import uuid


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
