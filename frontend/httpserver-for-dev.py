from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class SPAHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if not os.path.exists(self.translate_path(self.path)):
            self.path = '/not_found.html'
        return super().do_GET()

HTTPServer(('localhost', 8000), SPAHandler).serve_forever()
