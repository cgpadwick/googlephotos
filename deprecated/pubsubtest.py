from google.cloud import pubsub_v1

# Set up your Google Cloud project ID
project_id = "cgp-project"

# Initialize a Publisher client
publisher = pubsub_v1.PublisherClient()

# Set the topic name
topic_name = f"projects/{project_id}/topics/cgp-test-topic"

# Publish messages
def publish_messages(topic, messages):
    for message in messages:
        # Data must be a bytestring
        data = message.encode("utf-8")
        # Publishes the message
        future = publisher.publish(topic, data=data)
        # Wait for the message to be published
        future.result()

# Example messages to publish
messages_to_publish = ["Message 1", "Message 2", "Message 3"]

# Call the function to publish messages
print("publishing messages...")
publish_messages(topic_name, messages_to_publish)
print("done")


# Initialize a Subscriber client
subscriber = pubsub_v1.SubscriberClient()

# Set the subscription name
subscription_name = f"projects/{project_id}/subscriptions/cgp-test-subscription"

# Define a callback function to process messages
def callback(message):
    print("Received message:", message)
    # Acknowledge the message to remove it from the subscription's backlog
    message.ack()

# Subscribe to the topic and start listening for messages
def subscribe_to_topic(subscription_name):
    subscriber.subscribe(subscription_name, callback=callback)
    print("Listening for messages on subscription {}...".format(subscription_name))
    # Keep the main thread alive
    while True:
        pass

# Call the function to subscribe to the topic and start listening for messages
subscribe_to_topic(subscription_name)

