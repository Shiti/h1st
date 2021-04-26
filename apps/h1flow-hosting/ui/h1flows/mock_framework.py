from django.http import HttpResponse

class HasWebUI():
    def handle_request(self, req):
        if (req.method == 'GET'):
            return self.handle_get(req)
        else:
            return self.handle_post(req)
    
    def handle_post(self, req):
        return HttpResponse(self.get_response(req, True))

    def handle_get(self, req):
        return HttpResponse(self.get_response(req, False))

    def get_response(self, req, isPost=False):
        raise NotImplementedError('Please implement this method')

class H1Step():
    def __init__(self):
        pass

    def execute(self):
        raise NotImplementedError('Please implement this method')

class H1StepWithWebUI(H1Step, HasWebUI):
    def __init__(self):
        pass