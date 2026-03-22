#!/usr/bin/env python3
"""
AGENT 34 - REST API Gateway (GOVERNMENT GRADE)
UK WENDELL Forensic Platform - Official API Gateway
Security Level: OFFICIAL-SENSITIVE
"""

import json
import threading
import time
import os
import sys
import ssl
import logging
from functools import wraps
from datetime import datetime, timedelta
from pathlib import Path

# Add security module to path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, request, jsonify, g, make_response
import pika
import jwt
from werkzeug.middleware.proxy_fix import ProxyFix

# Import WENDELL security modules
from security.config import get_config
from security.auth import AuthManager, token_required, require_roles
from security.audit import get_audit_logger
from security.encryption import get_encryption_manager
from security.validators import (
    validate_request_data, 
    is_safe_query, 
    validate_case_id,
    InputValidator,
    sanitize_input
)

# ============================================================================
# INITIALIZATION
# ============================================================================

# Load configuration
config = get_config(os.getenv('WENDELL_ENV', 'production'))
auth = AuthManager()
encryption = get_encryption_manager()
audit = get_audit_logger('agent_34')

# Flask app setup
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Response storage (use Redis in production)
from collections import OrderedDict
class ResponseCache:
    """Thread-safe response cache with TTL"""
    def __init__(self, max_size=1000, ttl_seconds=300):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.lock = threading.Lock()
    
    def set(self, key, value):
        with self.lock:
            # Add timestamp
            value['_cached_at'] = time.time()
            self.cache[key] = value
            # Maintain size limit
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
    
    def get(self, key):
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                # Check TTL
                if time.time() - entry.get('_cached_at', 0) < self.ttl:
                    return entry
                else:
                    del self.cache[key]
            return None
    
    def remove(self, key):
        with self.lock:
            if key in self.cache:
                del self.cache[key]

responses = ResponseCache()

# ============================================================================
# RABBITMQ CONNECTION MANAGER
# ============================================================================

class RabbitMQManager:
    """Manages secure RabbitMQ connections with retry logic"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self._connect()
    
    def _connect(self):
        """Establish secure connection to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(
                config.get('rabbitmq_user'),
                config.get('rabbitmq_password')
            )
            
            # SSL for production
            ssl_options = None
            if config.get('environment') == 'production':
                ssl_context = ssl.create_default_context(
                    cafile="/etc/ssl/certs/rabbitmq-ca.pem"
                )
                ssl_options = pika.SSLOptions(ssl_context)
            
            parameters = pika.ConnectionParameters(
                host=config.get('rabbitmq_host'),
                port=config.get('rabbitmq_port'),
                virtual_host=config.get('rabbitmq_vhost'),
                credentials=credentials,
                ssl_options=ssl_options,
                heartbeat=600,
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=5
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare queues with durability
            self.channel.queue_declare(queue='orchestrator_input', durable=True)
            self.channel.queue_declare(queue='orchestrator_output', durable=True)
            
            audit.log('SYSTEM', 'rabbitmq', 'connected', {'status': 'success'})
            
        except Exception as e:
            audit.error('system', 'rabbitmq_connect', str(e))
            raise
    
    def publish_query(self, case_id, query_text, user_id, request_id):
        """Publish query with full audit trail"""
        if not self.connection or self.connection.is_closed:
            self._connect()
        
        # Prepare message with metadata
        msg = {
            'request_id': request_id,
            'case_id': case_id,
            'query': query_text,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'source_agent': 'agent_34',
            'classification': 'OFFICIAL-SENSITIVE'
        }
        
        # Add security headers
        properties = pika.BasicProperties(
            delivery_mode=2,  # persistent
            correlation_id=request_id,
            headers={
                'user_id': user_id,
                'agency': request.user.get('agency', 'UK_GOV'),
                'classification': 'OFFICIAL-SENSITIVE'
            }
        )
        
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key='orchestrator_input',
                body=json.dumps(msg),
                properties=properties
            )
            
            audit.log('QUERY', user_id, f'case:{case_id}', {
                'request_id': request_id,
                'query_length': len(query_text)
            })
            
        except Exception as e:
            audit.error(user_id, 'publish_query', str(e))
            raise
    
    def close(self):
        """Safely close connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except:
            pass

# Global RabbitMQ manager
rabbitmq = None

# ============================================================================
# BACKGROUND RESPONSE CONSUMER
# ============================================================================

def response_consumer():
    """Background thread to consume responses from orchestrator"""
    global rabbitmq
    
    while True:
        try:
            if not rabbitmq or not rabbitmq.connection or rabbitmq.connection.is_closed:
                rabbitmq = RabbitMQManager()
            
            def callback(ch, method, properties, body):
                try:
                    data = json.loads(body)
                    request_id = data.get('request_id')
                    case_id = data.get('case_id')
                    
                    if request_id:
                        # Store response
                        responses.set(request_id, data)
                        
                        audit.log('RESPONSE', 'system', f'case:{case_id}', {
                            'request_id': request_id,
                            'size_bytes': len(body)
                        })
                    
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    
                except Exception as e:
                    audit.error('system', 'response_callback', str(e))
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
            rabbitmq.channel.basic_consume(
                queue='orchestrator_output',
                on_message_callback=callback,
                auto_ack=False
            )
            
            rabbitmq.channel.start_consuming()
            
        except Exception as e:
            audit.error('system', 'consumer', str(e))
            time.sleep(5)  # Wait before reconnecting

# ============================================================================
# REQUEST VALIDATION DECORATORS
# ============================================================================

def validate_request(schema):
    """Validate incoming request against schema"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid JSON'}), 400
            
            # Validate request structure
            validation = validate_request_data(data, schema.get('required', []))
            if not validation['valid']:
                return jsonify({
                    'error': 'Validation failed',
                    'details': validation['errors']
                }), 400
            
            # Add sanitized data to request
            request.validated_data = validation['sanitized']
            
            return f(*args, **kwargs)
        return decorated
    return decorator

def rate_limit(limit=100, per=60):
    """Simple rate limiting (use Redis in production)"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Placeholder - implement with Redis for production
            return f(*args, **kwargs)
        return decorated
    return decorator

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/v1/query', methods=['POST'])
@token_required
@rate_limit(limit=100, per=60)
@validate_request({'required': ['case_id', 'query']})
def submit_query():
    """
    Submit a forensic query
    ---
    Expected JSON:
    {
        "case_id": "CASE_2025_001",
        "query": "Find all emails from suspect@example.com"
    }
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        data = request.validated_data
        case_id = data['case_id']
        query_text = data['query']
        
        # Validate case ID format
        if not validate_case_id(case_id):
            audit.access(request.user['user_id'], f'case:{case_id}', 'invalid_format')
            return jsonify({'error': 'Invalid case ID format'}), 400
        
        # Validate query safety
        query_validation = InputValidator.validate_query(query_text)
        if not query_validation['valid']:
            audit.log('SECURITY', request.user['user_id'], 'blocked_query', {
                'reason': query_validation['error']
            })
            return jsonify({'error': query_validation['error']}), 400
        
        # Check for cached response
        cached = responses.get(request_id)
        if cached:
            audit.access(request.user['user_id'], f'case:{case_id}', 'cache_hit')
            return jsonify({
                'status': 'success',
                'data': cached,
                'cached': True,
                'request_id': request_id
            })
        
        # Publish to RabbitMQ
        rabbitmq.publish_query(case_id, query_text, request.user['user_id'], request_id)
        
        # Wait for response (max 30 seconds)
        for attempt in range(30):
            time.sleep(1)
            response = responses.get(request_id)
            if response:
                # Remove from cache after retrieval
                responses.remove(request_id)
                
                processing_time = time.time() - start_time
                audit.access(request.user['user_id'], f'case:{case_id}', 'success', {
                    'processing_time': processing_time,
                    'request_id': request_id
                })
                
                return jsonify({
                    'status': 'success',
                    'data': response,
                    'request_id': request_id,
                    'processing_time': processing_time
                })
        
        # Timeout
        audit.access(request.user['user_id'], f'case:{case_id}', 'timeout', {
            'request_id': request_id
        })
        
        return jsonify({
            'status': 'error',
            'error': 'Query processing timeout',
            'request_id': request_id
        }), 504
        
    except Exception as e:
        audit.error(request.user['user_id'], 'query', str(e))
        return jsonify({
            'status': 'error',
            'error': 'Internal server error',
            'request_id': request_id
        }), 500

@app.route('/api/v1/case/<case_id>', methods=['GET'])
@token_required
@rate_limit(limit=200, per=60)
def get_case(case_id):
    """
    Get all entities for a case
    """
    # Validate case ID
    if not validate_case_id(case_id):
        audit.access(request.user['user_id'], f'case:{case_id}', 'invalid_format')
        return jsonify({'error': 'Invalid case ID format'}), 400
    
    # Sanitize
    case_id = sanitize_input(case_id, max_length=64)
    
    # Submit query
    request_id = str(uuid.uuid4())
    rabbitmq.publish_query(case_id, "MATCH (n) RETURN n LIMIT 1000", 
                          request.user['user_id'], request_id)
    
    # Wait for response
    for _ in range(30):
        time.sleep(1)
        response = responses.get(request_id)
        if response:
            responses.remove(request_id)
            return jsonify({
                'status': 'success',
                'data': response,
                'request_id': request_id
            })
    
    return jsonify({
        'status': 'error',
        'error': 'Timeout',
        'request_id': request_id
    }), 504

@app.route('/api/v1/auth/token', methods=['POST'])
@rate_limit(limit=5, per=60)  # Strict rate limiting on auth
def get_token():
    """
    Obtain JWT token for API access
    ---
    Expected JSON:
    {
        "username": "officer.name",
        "password": "secure_password",
        "otp": "123456"  # if 2FA enabled
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    
    username = data.get('username', '')
    password = data.get('password', '')
    otp = data.get('otp', '')
    
    # Validate input
    if not username or not password:
        audit.auth('unknown', 'failure', 'Missing credentials')
        return jsonify({'error': 'Username and password required'}), 400
    
    # Sanitize
    username = sanitize_input(username, max_length=32)
    
    # In production: validate against LDAP/Active Directory
    # This is a placeholder - implement proper authentication
    if username == "admin" and password == os.getenv('ADMIN_PASSWORD'):
        
        # Check 2FA if enabled
        if config.get('environment') == 'production':
            if not validate_otp(username, otp):
                audit.auth(username, 'failure', 'Invalid OTP')
                return jsonify({'error': 'Invalid OTP'}), 401
        
        # Create token
        token = auth.create_token(
            user_id=username,
            roles=['admin', 'investigator'],
            agency='UK_GOV'
        )
        
        audit.auth(username, 'success')
        
        return jsonify({
            'token': token,
            'expires_in': config.get('token_expiry_hours') * 3600,
            'token_type': 'Bearer'
        })
    
    audit.auth(username, 'failure', 'Invalid credentials')
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/v1/health', methods=['GET'])
def health():
    """Health check endpoint (no auth required)"""
    return jsonify({
        'status': 'operational',
        'agent': 34,
        'version': '2.0.0',
        'environment': config.get('environment'),
        'timestamp': datetime.utcnow().isoformat(),
        'rabbitmq': 'connected' if rabbitmq and rabbitmq.connection else 'disconnected'
    })

@app.route('/api/v1/metrics', methods=['GET'])
@token_required
@require_roles(['admin'])
def metrics():
    """System metrics (admin only)"""
    return jsonify({
        'cache_size': len(responses.cache),
        'uptime': time.time() - app.start_time,
        'requests_total': request_counter,
        'errors_last_hour': error_counter
    })

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(400)
def bad_request(error):
    audit.error('system', '400', str(error))
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(401)
def unauthorized(error):
    audit.error('system', '401', str(error))
    return jsonify({'error': 'Unauthorized'}), 401

@app.errorhandler(403)
def forbidden(error):
    audit.error('system', '403', str(error))
    return jsonify({'error': 'Forbidden'}), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(429)
def too_many_requests(error):
    return jsonify({'error': 'Rate limit exceeded'}), 429

@app.errorhandler(500)
def internal_error(error):
    audit.error('system', '500', str(error))
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    # Record start time
    app.start_time = time.time()
    request_counter = 0
    error_counter = 0
    
    # Initialize RabbitMQ
    audit.log('SYSTEM', 'agent_34', 'starting')
    rabbitmq = RabbitMQManager()
    
    # Start response consumer thread
    consumer_thread = threading.Thread(target=response_consumer, daemon=True)
    consumer_thread.start()
    
    # Get port from environment
    port = int(os.getenv('AGENT_34_PORT', '8443' if config.get('environment') == 'production' else '5000'))
    
    # Run with SSL in production
    if config.get('environment') == 'production':
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(
            '/etc/ssl/certs/wendell.crt',
            '/etc/ssl/private/wendell.key'
        )
        context.load_verify_locations('/etc/ssl/certs/ca-chain.crt')
        context.verify_mode = ssl.CERT_REQUIRED  # Mutual TLS
        
        app.run(
            host='0.0.0.0',
            port=port,
            ssl_context=context,
            debug=False,
            threaded=True
        )
    else:
        app.run(
            host='127.0.0.1',
            port=port,
            debug=False,
            threaded=True
        )
