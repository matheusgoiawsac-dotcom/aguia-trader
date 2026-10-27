from aguia.server import handler
from aguia.server import auth_api
# direct call
class Dummy:
    def __init__(self):
        self.headers = {}
        self.command = 'GET'
        self.wfile = type('obj', (), {'write': lambda self,x: print(x.decode() if isinstance(x,bytes) else x)})()
    def _send_json(self, data, status_code=200):
        print(status_code, data)
    def send_response(self, *args, **kwargs): pass
    def send_header(self, *args, **kwargs): pass
    def end_headers(self): pass

d = Dummy()
auth_api.handle_auth_me(d)
