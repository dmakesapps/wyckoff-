
import http.server
import socketserver
import json
import os
import urllib.parse

# Configuration
PORT = 8080
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(AGENT_DIR, "agent_log.txt")
TARGET_FILE = os.path.abspath(os.path.join(AGENT_DIR, "../api/services/bot_brain.py"))
TEST_FILE = os.path.abspath(os.path.join(AGENT_DIR, "../test_brain.py"))
MESSAGE_FILE = os.path.join(AGENT_DIR, "message_to_agent.txt")
CHAT_HISTORY_FILE = os.path.join(AGENT_DIR, "chat_history.json")
DASHBOARD_DIR = os.path.join(AGENT_DIR, "dashboard")

class AgentDashboardHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "OK")
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
        
        # Log Endpoint
        if self.path == "/api/logs":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            logs = []
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r') as f:
                    logs = f.readlines()[-50:] # Last 50 lines
            self.wfile.write(json.dumps({"logs": logs}).encode())
            return

        # State Endpoint
        if self.path == "/api/state":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            target_code = ""
            if os.path.exists(TARGET_FILE):
                with open(TARGET_FILE, 'r') as f:
                    target_code = f.read()
            
            test_code = ""
            if os.path.exists(TEST_FILE):
                with open(TEST_FILE, 'r') as f:
                    test_code = f.read()

            self.wfile.write(json.dumps({
                "target_code": target_code,
                "test_code": test_code
            }).encode())
            return
            
        # Chat History Endpoint
        if self.path == "/api/chat/history":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            history = []
            if os.path.exists(CHAT_HISTORY_FILE):
                try:
                    with open(CHAT_HISTORY_FILE, 'r') as f:
                        history = json.load(f)
                except:
                    pass
            self.wfile.write(json.dumps({"history": history}).encode())
            return
            
        # Serve static files from dashboard directory
        try:
            # Check if file exists in dashboard dir
            file_path = os.path.join(DASHBOARD_DIR, self.path.lstrip("/"))
            if os.path.exists(file_path) and os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                     content = f.read()
                self.send_response(200)
                if file_path.endswith(".html"):
                    self.send_header('Content-type', 'text/html')
                elif file_path.endswith(".css"):
                    self.send_header('Content-type', 'text/css')
                elif file_path.endswith(".js"):
                    self.send_header('Content-type', 'application/javascript')
                self.end_headers()
                self.wfile.write(content)
                return
        except Exception as e:
            print(f"Error serving file: {e}")
            
        self.send_error(404, "File not found")

    def do_POST(self):
        if self.path == "/api/message":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            message = data.get("message", "")
            if message:
                with open(MESSAGE_FILE, 'w') as f:
                    f.write(message)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "sent"}).encode())
            return

print(f"Serving Dashboard at http://localhost:{PORT}")

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

with ReusableTCPServer(("", PORT), AgentDashboardHandler) as httpd:
    httpd.serve_forever()
