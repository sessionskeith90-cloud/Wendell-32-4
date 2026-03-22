#!/usr/bin/env python3
"""
LedgerIngestor – Reads anchor JSON files from ~/forensic_data/ and publishes
each as a graph node message to RabbitMQ queue 'graph_input'.
"""

import json
import logging
import sys
from pathlib import Path

import pika
from pika.exceptions import AMQPConnectionError

ANCHOR_DIR = Path.home() / "forensic_data"
RABBITMQ_HOST = "localhost"
RABBITMQ_PORT = 5672
RABBITMQ_USER = "guest"
RABBITMQ_PASS = "guest"
QUEUE_NAME = "graph_input"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(Path.home() / "wendell" / "logs" / "ledger_ingestor.log", mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("LedgerIngestor")

def load_anchor(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def build_graph_node(anchor):
    return {
        "type": "Evidence",
        "properties": {
            "filename": anchor.get("filename", "unknown"),
            "sha256": anchor.get("hashes", {}).get("sha256", ""),
            "case": anchor.get("case", ""),
            "examiner": anchor.get("examiner", ""),
            "timestamp": anchor.get("timestamp", ""),
            "master_hash": anchor.get("master_hash", ""),
            "source": "LedgerSleuth",
            "notes": anchor.get("notes", "")
        }
    }

def publish_message(node):
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST, port=RABBITMQ_PORT,
        credentials=credentials, heartbeat=600
    )
    try:
        conn = pika.BlockingConnection(params)
        chan = conn.channel()
        chan.queue_declare(queue=QUEUE_NAME, durable=True)
        chan.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps(node),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        conn.close()
    except AMQPConnectionError as e:
        logger.error(f"RabbitMQ connection failed: {e}")
        raise

def main():
    logger.info("="*60)
    logger.info("LedgerIngestor started")
    if not ANCHOR_DIR.exists():
        logger.error(f"Directory not found: {ANCHOR_DIR}")
        sys.exit(1)

    anchors = list(ANCHOR_DIR.glob("anchor_*.json"))
    logger.info(f"Found {len(anchors)} anchor files.")

    success = 0
    for af in anchors:
        try:
            anchor = load_anchor(af)
            node = build_graph_node(anchor)
            publish_message(node)
            logger.info(f"Published: {af.name}")
            success += 1
        except Exception as e:
            logger.error(f"Failed {af.name}: {e}")

    logger.info(f"Done. Published {success}/{len(anchors)}.")
    logger.info("="*60)

if __name__ == "__main__":
    main()
