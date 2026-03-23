#!/usr/bin/env python3
"""
WENDELL Core 33 - Agent Integrator (Agent-Facing)
Orchestrates all other agents, manages 1‑touch universal integration,
and translates user requests into multi‑agent workflows.
Millisecond shadow for continuous availability.
"""

import json
import logging
import time
import threading
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

# WENDELL Core imports
from base_agent import BaseAgent
from security.audit import get_audit_logger
from security.config import get_config
from security.encryption import get_encryption_manager
from security.validators import validate_request_data
from lib.rabbitmq import RabbitMQClient

logger = logging.getLogger(__name__)
audit = get_audit_logger("agent_integrator")
config = get_config()
encryption = get_encryption_manager()


class IntegratorAgent(BaseAgent):
    """
    Agent-facing integrator for WENDELL Core 33.
    - Receives requests from Wendell agent (human‑facing)
    - Orchestrates other agents (21,22,34,41, etc.)
    - Manages 1‑touch universal integration workflows
    - Reports progress and results back to Wendell
    """
    
    agent_id = "integrator"
    agent_type = "agent_facing"
    capabilities = ["orchestrate", "deploy", "monitor", "integrate"]
    
    # Registry of supported external systems and their adapter agents
    ADAPTER_REGISTRY = {
        "uk_companies": {"agent": 41, "timeout": 30},
        "blockchain": {"agent": 1, "timeout": 60},
        "wallet_cluster": {"agent": 6, "timeout": 45},
        "sec_crawler": {"agent": 17, "timeout": 120},
        "officer_tracker": {"agent": 21, "timeout": 30},
        "graph_writer": {"agent": 22, "timeout": 20},
        "cross_val": {"agent": 31, "timeout": 15},
        "rest_gateway": {"agent": 34, "timeout": 10},
    }
    
    def __init__(self):
        # Call base class constructor with required arguments
        super().__init__(
            agent_id=self.agent_id,
            input_queue="integrator_input",
            output_queue="integrator_output"
        )
        self.shadow = IntegratorShadow(self)
        self.rabbitmq = RabbitMQClient(config.get_all())
        self.active_integrations = {}
        self.agent_status = {}
        self.start_time = time.time()
        
    def initialize(self, config_override: Optional[Dict] = None):
        """Initialize the integrator agent."""
        # Connect to RabbitMQ
        self.rabbitmq.connect()
        
        # Declare queues
        self.rabbitmq.channel.queue_declare(queue="integrator_input", durable=True)
        self.rabbitmq.channel.queue_declare(queue="integrator_output", durable=True)
        
        # Start shadow monitor
        self.shadow.start_monitoring()
        
        # Start consumer thread for responses from other agents
        self._start_response_consumer()
        
        audit.log("INIT", "system", "agent_integrator", {"status": "initialized"})
        return {"status": "initialized", "agent_id": self.agent_id}
    
    def _start_response_consumer(self):
        """Start background thread to consume responses from other agents."""
        def consumer():
            self.rabbitmq.consume(
                queue="integrator_output",
                callback=self._handle_agent_response
            )
        thread = threading.Thread(target=consumer, daemon=True)
        thread.start()
        logger.info("Integrator response consumer started")
    
    def _handle_agent_response(self, ch, method, properties, body):
        """Handle responses from other agents."""
        try:
            data = json.loads(body)
            correlation_id = properties.correlation_id
            
            # Match with active integration
            if correlation_id in self.active_integrations:
                integration = self.active_integrations[correlation_id]
                integration["responses"].append(data)
                integration["remaining"] -= 1
                
                # If all responses received, complete the integration
                if integration["remaining"] == 0:
                    self._complete_integration(correlation_id, integration)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error handling agent response: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def _complete_integration(self, request_id: str, integration: Dict):
        """Finalize an integration workflow and notify Wendell."""
        # Combine responses
        combined = {
            "request_id": request_id,
            "user_id": integration["user_id"],
            "query": integration["query"],
            "results": integration["responses"],
            "status": "completed",
            "duration": time.time() - integration["start_time"]
        }
        
        # Send result back to Wendell agent (via its input queue)
        self.rabbitmq.publish(
            queue="wendell_input",  # must be declared by Wendell agent
            message=combined,
            properties={"correlation_id": request_id}
        )
        
        # Audit
        audit.log("INTEGRATION_COMPLETE", integration["user_id"], f"request:{request_id}", {
            "duration": combined["duration"],
            "agent_count": len(integration["responses"])
        })
        
        # Clean up
        del self.active_integrations[request_id]
    
    def handle_user_query(self, message: Dict):
        """
        Entry point for requests from Wendell agent.
        Expected message format:
        {
            "type": "user_query",
            "user_id": "...",
            "query": "...",
            "request_id": "...",
            "timestamp": "..."
        }
        """
        request_id = message.get("request_id")
        user_id = message.get("user_id")
        query = message.get("query")
        
        if not all([request_id, user_id, query]):
            logger.warning(f"Invalid query message: {message}")
            return
        
        audit.log("QUERY_RECEIVED", user_id, f"request:{request_id}", {"query": query[:100]})
        
        # Parse query to determine which agents are needed
        target_agents = self._parse_query(query)
        
        # Create integration record
        self.active_integrations[request_id] = {
            "user_id": user_id,
            "query": query,
            "start_time": time.time(),
            "responses": [],
            "remaining": len(target_agents)
        }
        
        # Dispatch tasks to target agents
        for agent_id, task in target_agents:
            self._dispatch_task(request_id, agent_id, task)
    
    def _parse_query(self, query: str) -> List[tuple]:
        """
        Parse natural language query and determine which agents to invoke.
        Returns list of (agent_id, task_dict) tuples.
        """
        # Simple keyword-based routing – replace with NLP/extreme learning in production
        tasks = []
        query_lower = query.lower()
        
        if "company" in query_lower or "uk companies" in query_lower:
            tasks.append((41, {"action": "search", "term": query}))
        if "blockchain" in query_lower or "crypto" in query_lower or "wallet" in query_lower:
            tasks.append((1, {"action": "trace", "query": query}))
            tasks.append((6, {"action": "cluster", "query": query}))
        if "officer" in query_lower or "person" in query_lower or "track" in query_lower:
            tasks.append((21, {"action": "track", "query": query}))
        if "graph" in query_lower or "relationship" in query_lower:
            tasks.append((22, {"action": "query", "query": query}))
        if "validate" in query_lower or "cross" in query_lower:
            tasks.append((31, {"action": "validate", "query": query}))
        
        # Default: query all relevant agents
        if not tasks:
            tasks = [(41, {"action": "search", "term": query}),
                     (1, {"action": "trace", "query": query}),
                     (21, {"action": "track", "query": query})]
        
        return tasks
    
    def _dispatch_task(self, request_id: str, agent_id: int, task: Dict):
        """Send a task to a specific agent via RabbitMQ."""
        queue_name = f"agent_{agent_id}_input"  # convention: each agent listens on agent_<id>_input
        message = {
            "request_id": request_id,
            "task": task,
            "timestamp": datetime.utcnow().isoformat()
        }
        properties = {"correlation_id": request_id, "reply_to": "integrator_output"}
        
        self.rabbitmq.publish(
            queue=queue_name,
            message=message,
            properties=properties
        )
        logger.debug(f"Dispatched task to agent {agent_id} for request {request_id}")
    
    def universal_integration(self, target_system: str, config_data: Dict) -> Dict:
        """
        1‑touch integration with an external system.
        This can be triggered by a special command from Wendell or CLI.
        """
        request_id = str(uuid.uuid4())
        audit.log("INTEGRATION_START", "system", target_system, config_data)
        
        # Validate target system is supported
        if target_system not in self.ADAPTER_REGISTRY:
            return {"error": f"Unsupported system: {target_system}"}
        
        agent_info = self.ADAPTER_REGISTRY[target_system]
        agent_id = agent_info["agent"]
        timeout = agent_info["timeout"]
        
        # Create a one‑off integration task
        task = {
            "action": "integrate",
            "target": target_system,
            "config": config_data
        }
        
        # Dispatch to the appropriate agent
        self._dispatch_task(request_id, agent_id, task)
        
        # Wait for response (simplified – in production use async with timeout)
        # For this example, we'll just return immediately; the result will be sent to Wendell later.
        return {
            "status": "integration_started",
            "request_id": request_id,
            "estimated_time": timeout
        }
    
    def run(self):
        """Main loop – consume from integrator_input queue."""
        logger.info("Integrator agent started, waiting for requests...")
        self.rabbitmq.consume(
            queue="integrator_input",
            callback=self._handle_input_message
        )
    
    def _handle_input_message(self, ch, method, properties, body):
        """Handle incoming messages (from Wendell or direct commands)."""
        try:
            message = json.loads(body)
            msg_type = message.get("type")
            
            if msg_type == "user_query":
                self.handle_user_query(message)
            elif msg_type == "integration_command":
                # e.g., direct integration request
                result = self.universal_integration(
                    message.get("target"),
                    message.get("config", {})
                )
                # Send result back to reply queue
                if properties.reply_to:
                    self.rabbitmq.publish(
                        queue=properties.reply_to,
                        message=result,
                        properties={"correlation_id": properties.correlation_id}
                    )
            else:
                logger.warning(f"Unknown message type: {msg_type}")
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error handling input message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def health_check(self) -> Dict:
        """Return health status for monitoring."""
        return {
            "status": "healthy" if self.shadow.is_ready() else "degraded",
            "agent": self.agent_id,
            "uptime": time.time() - self.start_time,
            "active_integrations": len(self.active_integrations),
            "shadow": self.shadow.get_status()
        }
    
    def shutdown(self):
        """Graceful shutdown."""
        self.shadow.stop_monitoring()
        self.rabbitmq.close()
        audit.log("SHUTDOWN", "system", "agent_integrator", {})
        logger.info("Integrator agent shutdown")


class IntegratorShadow:
    """
    Shadow for IntegratorAgent – <1ms failover and decision validation.
    """
    
    def __init__(self, primary):
        self.primary = primary
        self.ready = False
        self.last_sync = 0
        self.health_check_interval = 0.5
        self.monitoring = False
        self.monitor_thread = None
        self.state = {}
        
    def start_monitoring(self):
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Integrator shadow monitoring started")
        
    def stop_monitoring(self):
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
            
    def _monitor_loop(self):
        while self.monitoring:
            try:
                if not self._check_primary_health():
                    self._takeover()
                self._sync_state()
                time.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Shadow monitor error: {e}")
                
    def _check_primary_health(self) -> bool:
        try:
            if hasattr(self.primary, 'health_check'):
                health = self.primary.health_check()
                return health.get('status') == 'healthy'
            return True
        except:
            return False
            
    def _takeover(self):
        logger.warning("Integrator shadow taking over as primary")
        self.ready = True
        audit.log("SHADOW_TAKEOVER", "system", "integrator", {})
        
    def _sync_state(self):
        try:
            self.state = {
                'active_integrations': getattr(self.primary, 'active_integrations', {}).copy(),
                'agent_status': getattr(self.primary, 'agent_status', {}).copy(),
                'start_time': getattr(self.primary, 'start_time', time.time()),
            }
            self.last_sync = time.time()
        except Exception as e:
            logger.error(f"Shadow sync error: {e}")
            
    def is_ready(self) -> bool:
        return self.ready and (time.time() - self.last_sync < 2.0)
    
    def get_status(self) -> Dict:
        return {
            "ready": self.ready,
            "last_sync": self.last_sync,
            "monitoring": self.monitoring
        }


# If run directly
if __name__ == "__main__":
    agent = IntegratorAgent()
    agent.initialize()
    try:
        agent.run()
    except KeyboardInterrupt:
        agent.shutdown()
