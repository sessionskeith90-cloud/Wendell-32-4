#!/usr/bin/env python3
"""
WENDELL Core 33 - RabbitMQ Client
Thin wrapper around pika for inter-agent messaging.
"""

import json
import logging
import time
from typing import Any, Callable, Dict, Optional

import pika

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """Manages a single RabbitMQ connection and channel."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------
    def connect(self, retries: int = 5, delay: float = 2.0):
        """Connect with exponential back-off."""
        host = self.config.get("rabbitmq_host", "localhost")
        port = int(self.config.get("rabbitmq_port", 5672))
        user = self.config.get("rabbitmq_user", "guest")
        password = self.config.get("rabbitmq_password", "guest")
        vhost = self.config.get("rabbitmq_vhost", "/")

        credentials = pika.PlainCredentials(user, password)
        params = pika.ConnectionParameters(
            host=host,
            port=port,
            virtual_host=vhost,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300,
        )

        for attempt in range(1, retries + 1):
            try:
                self.connection = pika.BlockingConnection(params)
                self.channel = self.connection.channel()
                logger.info(f"Connected to RabbitMQ at {host}:{port} (attempt {attempt})")
                return
            except pika.exceptions.AMQPConnectionError as exc:
                logger.warning(f"RabbitMQ connect attempt {attempt}/{retries} failed: {exc}")
                if attempt < retries:
                    time.sleep(delay * attempt)
        raise ConnectionError(f"Could not connect to RabbitMQ at {host}:{port} after {retries} attempts")

    # ------------------------------------------------------------------
    # Publish / Consume
    # ------------------------------------------------------------------
    def publish(
        self,
        queue: str,
        message: Dict[str, Any],
        properties: Optional[Dict[str, str]] = None,
    ):
        """Publish a JSON message to *queue* (auto-declared, durable)."""
        self.channel.queue_declare(queue=queue, durable=True)
        props = pika.BasicProperties(
            delivery_mode=2,  # persistent
            content_type="application/json",
            **(properties or {}),
        )
        self.channel.basic_publish(
            exchange="",
            routing_key=queue,
            body=json.dumps(message),
            properties=props,
        )
        logger.debug(f"Published to {queue}")

    def consume(self, queue: str, callback: Callable):
        """Blocking consume from *queue*."""
        self.channel.queue_declare(queue=queue, durable=True)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=queue, on_message_callback=callback)
        logger.info(f"Consuming from {queue}")
        self.channel.start_consuming()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def close(self):
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as exc:
            logger.error(f"Error closing RabbitMQ connection: {exc}")
