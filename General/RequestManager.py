import requests
import General.Logger as Logger
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ErrorResponse:
    def __init__(self, response, error="RequestError"):
        self.response = response
        self.status_code = 0
        if ( response!= None ):
            self.status_code = response.status_code
        self.Error = error

class RequestManager:
    def __init__(self, apikey, localhostproxy=True):
        self.default_headers =self.generate_headers(apikey)
        self.csrfToken = None
        self.session = requests.Session()
        if localhostproxy:
            self.proxies = self.get_localhost_proxy()
        else:
            self.proxies = {}
    
    def get_localhost_proxy(self):
        return  {
            'http': 'http://127.0.0.1:8888',
            'https': 'http://127.0.0.1:8888' }

    def generate_headers(self, apikey):
        return {
            "api-token" : apikey,
            "Content-Type" : "application/json"}


    def SendRequestWithRetry(self, url, headers={}, parameters={}, method="get", body=None, retries=3):
        for i in range(retries):
            try:
                response = self.SendRequest(url, headers, parameters, method, body)
                if response.status_code == 200:
                    return response
            except requests.RequestException as e:
                Logger.log_error(f"Error in request, retrying... {e}")
                response = e.response
            except Exception as e:
                Logger.log_error(f"Error in request, retrying... {e}")
                response = None

        if ( response != None and response.status_code > 400):
            er = ErrorResponse(response, "Token might need a refresh.")
        else:
            er = ErrorResponse(response)
        
        Logger.log_error(f"Error in request, status-code: {er.status_code}, reason: {er.Error}")
        return er

    def SendRequest(self, url, headers, parameters, method="get", body=None):
        method = method.lower()
        #new headers:
        headers = dict(headers)
        headers.update(self.default_headers)
        if ( method == "get" ):
            response = self.session.get(url,headers=headers, params= parameters, verify=False,  proxies=self.proxies)
            if response.status_code == 200:
                return response
        
        if ( method == "post" ):
            # in case the body is not a webForm - body variable should contain the data
            response = self.session.post(url, headers=headers ,params=parameters, data = body, verify=False,  proxies=self.proxies)
            if response.status_code == 200:
                return response
        
        if ( method == "jsonpost"):
            response = self.session.post(url, headers=headers ,params=parameters, json = body, verify=False,  proxies=self.proxies)
            if response.status_code == 200:
                return response
        
        if ( method == "put" ):
            response = self.session.put(url, headers=headers ,params=parameters, json = body, verify=False,  proxies=self.proxies)
            if response.status_code == 200:
                return response

        return ErrorResponse(response)
    