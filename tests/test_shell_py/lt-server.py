
#
#   "emulation" of LT server
#

from http.server import HTTPServer, BaseHTTPRequestHandler
import json

addr = 'localhost'
port = 8081

max_req = 2     # then exit
cnt_req = 0

match = {
    'offset': 5,
    'length': 3,
    'message': 'Error',
    'rule': {'id': 'None'},
    'replacements': [{'value': 'is'}],
    'context': {
        'text': 'This isx a test. ',
        'offset': 5,
        'length': 3,
    },
}
message = {'matches': [match]}

class Handler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def do_POST(self):
        self._set_headers()
        self.wfile.write(json.dumps(message).encode('ascii'))

        global cnt_req
        cnt_req += 1
        if cnt_req == max_req:
            exit()


if __name__ == "__main__":
    server_address = (addr, port)
    httpd = HTTPServer(server_address, Handler)
    httpd.serve_forever(0.1)

