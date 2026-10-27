from aguia.server import handler
from aguia.server.auth_api import handle_auth_me

class Dummy(handler.AguiaRequestHandler):
    def __init__(self):
        pass
    def _send_json(self, data, status_code=200):
        print(status_code)
        print(data)
    def send_response(self, *args, **kwargs): pass
    def send_header(self, *args, **kwargs): pass
    def end_headers(self): pass

d = Dummy.__new__(Dummy)
d.path = '/api/auth/me'
d.headers = {}
try:
    d._route()
except Exception as e:
    print(e)
