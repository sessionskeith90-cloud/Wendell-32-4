#!/usr/bin/env python3
"""
WENDELL Core 33 - WSGI Entry Point
Used by gunicorn / Azure App Service to start the application.
"""

import os
import logging

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from agent_wendell import WendellAgent

# Create and initialise the agent
agent = WendellAgent()

try:
    agent.initialize()
except Exception as exc:
    logging.getLogger(__name__).warning(
        f"Initialisation warning (RabbitMQ may not be available): {exc}"
    )

# Expose the Flask app for gunicorn
app = agent.app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    app.run(host="0.0.0.0", port=port)
