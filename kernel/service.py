import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
from engine import PolicyEngine

LOG_DIR = os.getenv("LOG_DIR", "/home/ubuntu/execution-kernel/logs")

class KernelHandler(BaseHTTPRequestHandler):
    engine = PolicyEngine()

    def do_POST(self):
        if self.path == "/evaluate":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                request_data = json.loads(post_data.decode('utf-8'))
                result = self.engine.evaluate(request_data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
                
                # Persistent Decision Log
                self.log_decision(request_data, result)
                
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_decision(self, request, result):
        """Logs the decision to a structured JSON file."""
        try:
            if not os.path.exists(LOG_DIR):
                os.makedirs(LOG_DIR)
            
            log_file = os.path.join(LOG_DIR, f"{datetime.utcnow().strftime('%Y-%m-%d')}.jsonl")
            log_entry = {"request": request, "response": result}
            
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"[ERROR] Failed to write to decision log: {e}")

def run(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, KernelHandler)
    print(f"Strix Labs Execution Kernel v1.1 starting on port {port}...")
    print(f"Decision logs will be written to: {LOG_DIR}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
