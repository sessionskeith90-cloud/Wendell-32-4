#!/usr/bin/env python3
"""
Agent 34 – Enhanced REST API Gateway
With query endpoint and Wendell integration
"""

from flask import Flask, jsonify, request
import threading
import time
import os
import json
from datetime import datetime

app = Flask(__name__)

# Store start time and request counter
start_time = time.time()
request_counter = 0
processed_files = set()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'agent': '34',
        'name': 'REST API Gateway',
        'uptime': f"{int(time.time() - start_time)} seconds",
        'timestamp': time.time()
    })

@app.route('/')
def home():
    """API home endpoint."""
    return jsonify({
        'name': 'Wendell Agent 34',
        'version': '2.0',
        'endpoints': [
            '/health - GET',
            '/stats - GET',
            '/query - POST',
            '/files - GET',
            '/incoming - GET'
        ]
    })

@app.route('/stats', methods=['GET'])
def stats():
    """Enhanced stats endpoint."""
    global request_counter
    request_counter += 1
    
    # Count files in incoming directory
    incoming_dir = os.path.expanduser('~/incoming')
    processed_dir = os.path.join(incoming_dir, 'processed')
    
    incoming_files = []
    processed_files_list = []
    
    if os.path.exists(incoming_dir):
        incoming_files = [f for f in os.listdir(incoming_dir) 
                         if os.path.isfile(os.path.join(incoming_dir, f))]
    
    if os.path.exists(processed_dir):
        processed_files_list = [f for f in os.listdir(processed_dir) 
                               if os.path.isfile(os.path.join(processed_dir, f))]
    
    return jsonify({
        'agent': '34',
        'requests_served': request_counter,
        'uptime': f"{int(time.time() - start_time)} seconds",
        'monitoring': {
            'incoming_count': len(incoming_files),
            'processed_count': len(processed_files_list),
            'incoming_dir': str(incoming_dir),
            'processed_dir': str(processed_dir)
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/incoming', methods=['GET'])
def list_incoming():
    """List files in incoming directory."""
    incoming_dir = os.path.expanduser('~/incoming')
    
    if not os.path.exists(incoming_dir):
        return jsonify({'error': 'Incoming directory not found'}), 404
    
    files = []
    for f in os.listdir(incoming_dir):
        file_path = os.path.join(incoming_dir, f)
        if os.path.isfile(file_path):
            stat = os.stat(file_path)
            files.append({
                'name': f,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    
    return jsonify({
        'count': len(files),
        'files': files
    })

@app.route('/query', methods=['POST'])
def query():
    """Submit a query to Wendell."""
    global request_counter
    request_counter += 1
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    query_text = data.get('query', '')
    case_id = data.get('case_id', 'default')
    
    # Here you would integrate with Wendell's core
    # For now, return a simple response
    
    return jsonify({
        'status': 'received',
        'case_id': case_id,
        'query': query_text[:100],
        'timestamp': datetime.now().isoformat(),
        'wendell_says': f"Query received for case {case_id}. Agents are analyzing."
    })

def run_server():
    """Run the Flask server."""
    print("🚀 Agent 34 (Enhanced) starting on http://0.0.0.0:5000")
    print("   Endpoints: /health, /stats, /incoming, /query")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def start():
    """Start Agent 34 in a background thread."""
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    print("✅ Agent 34 – Enhanced REST API Gateway started")
    return thread

if __name__ == '__main__':
    run_server()
