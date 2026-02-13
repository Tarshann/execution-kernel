import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from engine import PolicyEngine

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
                
                # Simple Decision Log (to stdout for now)
                print(f"[LOG] {result['timestamp']} | {request_data.get('agent_id')} | {request_data.get('artifact_type')} | {result['decision']}")
                
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, KernelHandler)
    print(f"Strix Labs Execution Kernel v1.1 starting on port {port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
