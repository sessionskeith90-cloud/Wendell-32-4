#!/usr/bin/env python3
"""
Simple consumer for graph_input queue – logs messages to a file.
"""
import json
import logging
from pathlib import Path

import pika

LOG_FILE = Path.home() / "wendell" / "graph_output.log"
QUEUE = "graph_input"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        logging.info(f"Received: {json.dumps(data, indent=2)}")
    except Exception as e:
        logging.error(f"Error processing message: {e}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.basic_consume(queue=QUEUE, on_message_callback=callback)
    print("Waiting for messages. Press Ctrl+C to exit.")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()

if __name__ == "__main__":
    main()
