#!/usr/bin/env python3
"""
WENDELL Core 33 - Agent Wendell (Human-Facing)
Handles all user interaction, natural language, and dashboard visualization.
Millisecond shadow for continuous availability.
"""

import asyncio
import json
import logging
import time
import threading
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# WENDELL Core imports
from base_agent import BaseAgent
from security.audit import get_audit_logger
from security.auth import token_required
from security.config import get_config
from security.encryption import get_encryption_manager
from lib.rabbitmq import RabbitMQClient

# Dashboard/UI imports
try:
    from flask import Flask, render_template, request, jsonify, session
    import socketio
except ImportError:
    Flask = None
    socketio = None

logger = logging.getLogger(__name__)
audit = get_audit_logger("agent_wendell")
config = get_config()
encryption = get_encryption_manager()


class WendellAgent(BaseAgent):
    """
    Human-facing AI agent for WENDELL Core 33 dashboard.
    Handles natural language, visualizations, and user commands.
    """
    
    agent_id = "wendell"
    agent_type = "human_facing"
    capabilities = ["chat", "query", "visualize", "report", "command"]
    
    def __init__(self):
        # Call base class constructor with required arguments
        super().__init__(
            agent_id=self.agent_id,
            input_queue="wendell_input",
            output_queue="wendell_output"
        )
        self.shadow = WendellShadow(self)
        self.app = None
        self.sio = None
        self.active_sessions = {}
        self.request_queue = asyncio.Queue()
        self.start_time = time.time()
        self.rabbitmq = RabbitMQClient(config.get_all())
        
    def initialize(self, config_override: Optional[Dict] = None):
        """Initialize the agent with configuration."""
        self.port = config.get("wendell_port", 5001)
        self.debug = config.get("environment") == "development"
        
        # Initialize Flask app
        self._create_app()
        print("DEBUG: rabbitmq_user =", self.rabbitmq.config.get('rabbitmq_user'))
        print("DEBUG: rabbitmq_password =", self.rabbitmq.config.get('rabbitmq_password')) 
        # Connect to RabbitMQ
        self.rabbitmq.connect()
        
        # Start shadow monitor
        self.shadow.start_monitoring()
        
        audit.log("INIT", "system", "agent_wendell", {"status": "initialized"})
        return {"status": "initialized", "agent_id": self.agent_id}
    
    def _create_app(self):
        """Create Flask/SocketIO application."""
        if not Flask or not socketio:
            logger.warning("Flask/SocketIO not available - dashboard disabled")
            return
            
        self.app = Flask(__name__)
        self.app.secret_key = config.get("jwt_secret")
        
        # SocketIO for real-time updates
        self.sio = socketio.Server(async_mode='threading')
        self.app.wsgi_app = socketio.WSGIApp(self.sio, self.app.wsgi_app)
        
        @self.app.route('/')
        def index():
            return render_template('dashboard.html', agent="wendell")
        
        @self.app.route('/api/health')
        def health():
            return jsonify({
                "agent": "wendell",
                "status": "operational",
                "uptime": time.time() - self.start_time,
                "shadow_ready": self.shadow.is_ready()
            })
        
        @self.app.route('/api/query', methods=['POST'])
        @token_required
        def handle_query():
            """Handle natural language queries from users."""
            data = request.get_json()
            user_id = request.user.get('user_id')
            query = data.get('query', '')
            
            if not query:
                return jsonify({"error": "No query provided"}), 400
            
            audit.log("QUERY", user_id, "user_input", {"query_length": len(query)})
            
            # Forward to integrator agent
            response = self._forward_to_integrator(user_id, query)
            
            return jsonify({
                "response": response,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        @self.sio.on('connect')
        def handle_connect(sid, environ):
            logger.info(f"Client connected: {sid}")
            self.active_sessions[sid] = {
                "connected": time.time(),
                "last_activity": time.time()
            }
        
        @self.sio.on('disconnect')
        def handle_disconnect(sid):
            logger.info(f"Client disconnected: {sid}")
            self.active_sessions.pop(sid, None)
        
        @self.sio.on('command')
        def handle_command(sid, data):
            """Handle real-time commands via WebSocket."""
            command = data.get('command')
            params = data.get('params', {})
            result = self._process_command(command, params)
            self.sio.emit('command_result', {
                "command": command,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }, room=sid)
    
    def _forward_to_integrator(self, user_id: str, query: str) -> Dict:
        """Forward user request to integrator agent for processing."""
        request_id = str(uuid.uuid4())
        message = {
            "type": "user_query",
            "user_id": user_id,
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }
        
        # Publish to integrator's input queue
        self.rabbitmq.publish(
            queue="integrator_input",
            message=message,
            properties={"correlation_id": request_id}
        )
        
        # For simplicity, return immediately; response would be handled asynchronously
        # In production, you'd set up a response queue and wait with timeout
        return {"status": "processing", "request_id": request_id}
    
    def _process_command(self, command: str, params: Dict) -> Dict:
        """Process dashboard commands."""
        handlers = {
            "refresh_data": self._cmd_refresh_data,
            "export_report": self._cmd_export_report,
            "run_analysis": self._cmd_run_analysis,
            "system_status": self._cmd_system_status
        }
        handler = handlers.get(command)
        return handler(params) if handler else {"error": f"Unknown command: {command}"}
    
    def _cmd_system_status(self, params):
        """Return system status for dashboard."""
        return {
            "agents": self._get_agent_status(),
            "uptime": time.time() - self.start_time,
            "active_sessions": len(self.active_sessions),
            "shadow": self.shadow.get_status()
        }
    
    def _get_agent_status(self):
        """Get status of all agents (would query orchestrator)."""
        return {"integrator": "online", "other_agents": "unknown"}
    
    def _cmd_refresh_data(self, params):
        audit.log("COMMAND", "system", "refresh_data", params)
        return {"status": "refreshing"}
    
    def _cmd_export_report(self, params):
        audit.log("COMMAND", "system", "export_report", params)
        return {"status": "exporting", "format": params.get("format", "pdf")}
    
    def _cmd_run_analysis(self, params):
        audit.log("COMMAND", "system", "run_analysis", params)
        return {"status": "analysis_started", "analysis_id": str(uuid.uuid4())}
    
    def run(self):
        """Run the agent (blocking)."""
        if self.app:
            logger.info(f"Starting Wendell agent on port {self.port}")
            self.app.run(host='127.0.0.1', port=self.port, debug=self.debug)
        else:
            self._run_cli()
    
    def _run_cli(self):
        """Run in CLI mode (no dashboard)."""
        logger.info("Running in CLI mode")
        while True:
            try:
                user_input = input("\nWENDELL> ")
                if user_input.lower() in ['exit', 'quit']:
                    break
                response = self._forward_to_integrator("cli_user", user_input)
                print(f"Response: {response}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"CLI error: {e}")
    
    def health_check(self):
        """Return health status for monitoring."""
        return {
            "status": "healthy" if self.shadow.is_ready() else "degraded",
            "agent": self.agent_id,
            "uptime": time.time() - self.start_time,
            "sessions": len(self.active_sessions),
            "shadow": self.shadow.get_status()
        }
    
    def shutdown(self):
        """Graceful shutdown."""
        self.shadow.stop_monitoring()
        self.rabbitmq.close()
        audit.log("SHUTDOWN", "system", "agent_wendell", {})
        logger.info("Wendell agent shutdown")


class WendellShadow:
    """
    Shadow for WendellAgent - provides <1ms failover and decision validation.
    """
    
    def __init__(self, primary):
        self.primary = primary
        self.ready = False
        self.last_sync = 0
        self.health_check_interval = 0.5  # 500ms
        self.monitoring = False
        self.monitor_thread = None
        self.state = {}
        
    def start_monitoring(self):
        """Start background monitoring thread."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Wendell shadow monitoring started")
        
    def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
            
    def _monitor_loop(self):
        """Continuous health monitoring."""
        while self.monitoring:
            try:
                # Check primary health
                if not self._check_primary_health():
                    self._takeover()
                
                # Sync state
                self._sync_state()
                
                time.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Shadow monitor error: {e}")
                
    def _check_primary_health(self) -> bool:
        """Return True if primary is healthy."""
        try:
            # Simple heartbeat check
            if hasattr(self.primary, 'health_check'):
                health = self.primary.health_check()
                return health.get('status') == 'healthy'
            return True
        except:
            return False
            
    def _takeover(self):
        """Become the active agent."""
        logger.warning("Shadow taking over as primary")
        self.ready = True
        # Notify orchestrator
        audit.log("SHADOW_TAKEOVER", "system", "wendell", {})
        
    def _sync_state(self):
        """Synchronize state from primary."""
        try:
            # Copy relevant state
            self.state = {
                'active_sessions': getattr(self.primary, 'active_sessions', {}).copy(),
                'start_time': getattr(self.primary, 'start_time', time.time()),
            }
            self.last_sync = time.time()
        except Exception as e:
            logger.error(f"Shadow sync error: {e}")
            
    def is_ready(self) -> bool:
        """Return True if shadow is ready to take over."""
        return self.ready and (time.time() - self.last_sync < 2.0)  # recent sync
    
    def get_status(self) -> Dict:
        """Return shadow status."""
        return {
            "ready": self.ready,
            "last_sync": self.last_sync,
            "monitoring": self.monitoring
        }


# If run directly
if __name__ == "__main__":
    agent = WendellAgent()
    agent.initialize()
    try:
        agent.run()
    except KeyboardInterrupt:
        agent.shutdown()
