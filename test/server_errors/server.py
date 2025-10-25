import http.server
import socketserver
import urllib.parse
from time import sleep

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        no_response = query_components.get("no_response", [None])[0]
        partial_status = query_components.get("partial_status", [None])[0]
        status_only = query_components.get("status_only", [None])[0]
        headers_only = query_components.get("headers_only", [None])[0]
        partial_body = query_components.get("partial_body", [None])[0]

        if no_response:
            # Don't send any response
            sleep(2)
            return
        
        if partial_status:
            # Don't send any response
            self.wfile.write(b"HT")
            sleep(2)
            return

        if status_only:
            self.wfile.write(b"HTTP/1.1 200 OK\r\n")
            sleep(2)
            return

        html = "<html><head><title>Test Server</title></head><body><h1>Hello, World!</h1></body></html>"
        body = html.encode()
        bodyLen = str(len(body))

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", bodyLen)
        self.end_headers()

        if headers_only:
            sleep(2)
            return
        

        if partial_body:
            print("Sending partial body")
            body = body[:len(body)//2]

        self.wfile.write(body)
        
        sleep(2)

PORT = 8000

Handler = MyHttpRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()
