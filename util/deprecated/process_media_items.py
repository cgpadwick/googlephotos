import argparse
import json
import yaml

import pandas as pd
from pathlib import Path

from google.cloud import pubsub_v1

from tqdm import tqdm


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--filename",
        required=True,
        type=Path,
        help="pathname to the saved media items file",
    )
    parser.add_argument(
        "--maxmessages",
        required=False,
        type=int,
        default=10,
        help="maximum number of messages to send",
    )
    parser.add_argument(
        "--configfile",
        required=True,
        type=Path,
        help="path to the yaml config file",
    )

    args = parser.parse_args()
    photos_df = pd.read_pickle(args.filename)

    with open(args.configfile, "r") as file:
        config = yaml.safe_load(file)

    # Create the topic path
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(
        config["project_id"], config["topics"]["target_topic"]["name"]
    )

    num_msgs_sent = 0
    for _, row in photos_df.iterrows():

        print("HARDCODED BASE URL FOR TESTING!!!!")
        if "image" in row.mimeType:
            msg = {
                #"baseurl": row.baseUrl,
                "baseurl": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                "id": row.id,
                "project_id": config["project_id"],
                "processed_topic": config["topics"]["processed_topic"]["name"],
                "error_topic": config["topics"]["error_topic"]["name"],
            }
            message_data = json.dumps(msg).encode("utf-8")

            print(row.baseUrl)

            # Publish the message
            future = publisher.publish(topic_path, data=message_data)
            message_id = future.result()
            num_msgs_sent += 1
            print(f"processed id {row.id}")

        if num_msgs_sent >= args.maxmessages:
            break
