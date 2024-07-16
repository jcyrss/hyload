import time, http.client, socket, gzip
from urllib.parse import urlencode
from hyload.stats import Stats,bcolors
from hyload.util import getCurTime
from hyload.logger import TestLogger
import json as jsonlib
from http.cookies import SimpleCookie
from typing import Union, Dict, List
from functools import cached_property
import random, string, mimetypes,os



_common_headers = {
    # 'User-Agent' : "hyload tester"
}


# begin ** for patch http built-in funcs

_http_req_msg_buf_cpy = b''

_ori_http_send = http.client.HTTPConnection.send

def _patch_httplib_funcs():
    def new_send(self, data):
        global _http_req_msg_buf_cpy
        if hasattr(data, "read"):
            return
        _http_req_msg_buf_cpy += data        
        return _ori_http_send(self, data)
    http.client.HTTPConnection.send = new_send


def _unpatch_httplib_funcs():
    http.client.HTTPConnection.send = _ori_http_send


# end  ** for patch http built-in funcs


def _guessEncodingFromContentType(contentType):
    if contentType is not None:
        for one in contentType.replace(' ','').split(';'):
            if one.startswith('charset='):
                return one[8:]
    return 'utf-8'


_string_range = string.ascii_lowercase + string.digits
_upload_file_cache = {}
def create_ct_body_for_uploading(params, use_file_cache=True, file_type=None):
    """helper function to compose a request of uploading file

    call it like :

    header_ct, body = create_ct_body_for_uploading([
            ("param1", 'value1' ),
            ("param2", 'value2' ),
            'file1.mp4',
            'file2.mp4',
        ])

    response = client.post(
        'http://127.0.0.1/upload',        
        headers={
            'Content-Type': header_ct
        },
        data=body,
    )
    """

    boundary = ''.join(random.choices(_string_range, k=32))
    header_ct = f'multipart/form-data; boundary={boundary}' # Content-Type

    boundary = boundary.encode()
    BNL = b'\r\n'
    BOUNDARY_LINE = b'--' + boundary + BNL
    BOUNDARY_LINE_END   = b'--' + boundary + b'--' + BNL*2

    body = b''
    
    for entry in params:
        body += BOUNDARY_LINE

        if type(entry)==tuple and len(entry) == 2:  # **** other entries
                        
            name, value = entry

            body += f'Content-Disposition: form-data; name="{name}"'.encode() + BNL*2
            body += value.encode() + BNL

        elif type(entry)==str : # **** file         
            file_path = entry
            fileName = os.path.basename(file_path)

            body += f'Content-Disposition: form-data; name="file"; filename={fileName}'.encode() + BNL

            if file_type is None:
                file_type = mimetypes.guess_type(fileName)[0] or 'application/octet-stream'
            body += f'Content-Type: {file_type}'.encode() + BNL*2

            content = None
            if use_file_cache:
                content = _upload_file_cache.get(file_path)

            if content is None:
                with open(file_path,'rb') as f: 
                    # Bad for large files
                    content = f.read()
            
            if use_file_cache:
                _upload_file_cache[file_path] = content
            
            body +=  content + BNL


    # **** end
    body += BOUNDARY_LINE_END

    return header_ct, body


# HTTPResponse Wrapper obj
# refer to https://docs.python.org/3/library/http.client.html#httpresponse-objects
class HttpResponse():
    def __init__(self,
                 http_response=None,
                 raw_body=None,
                 response_time=None, # in ms
                 url=None,
                 error_type=None): 
        self._http_response = http_response
        self.content = raw_body
        self.response_time = response_time
        self.url = url

        self.error_type  = error_type
        self.status_code = http_response.status

        self._encoding = None
    
    def __getattr__(self, attr):
        return getattr(self._http_response, attr) 
  
    @property
    def encoding(self):
        if self._encoding is None:
            self._encoding = _guessEncodingFromContentType(self.getheader('Content-Type'))
        return self._encoding
    
    
    @encoding.setter
    def encoding(self, value):
        self._encoding = value


    @property
    def text(self):
        if self._encoding is None:
            self._encoding = _guessEncodingFromContentType(self.getheader('Content-Type'))
                
        try:
            return self.content.decode(self._encoding)
        except:
            print(f'message body decode with {self._encoding} failed!!')
            return None
    
    def json(self): 
        """Parse response body as json

        Parameters
        ----------
        encoding : str   (optional)
            by default None

        Returns
        -------
        Any
            Return Python object if parsing successfully, Or raise Exception if parsing failed.
        """
        
        return jsonlib.loads(self.text)
       

    
    def get_all_cookies(self):
        cookiesStr = self._http_response.getheader('Set-Cookie')
        if not cookiesStr:
            return {}
            
        cookieList = self._http_response.getheader('Set-Cookie').split(',')

        cookieDict = {}
        for c in cookieList:
            kv = c.split(';')[0].split('=')
            cookieDict[kv[0]] = kv[1]
        return cookieDict

    def get_cookie(self,cookieName):
        cookieDict = self.get_all_cookies()
        return cookieDict.get(cookieName)



# refer to https://docs.python.org/3/library/http.client.html#http.client.HTTPConnection
class HttpClient:
    
    def __init__(self, timeout:int=10, proxy:Union[None,str]=None): 
        """One HttpClient object represents a http client

        Parameters
        ----------
        timeout : int   (optional)
            It is the timeout value for network operations, like connecting. , by default 10
        proxy : Union[None,str]   (optional)
            It is to specify the proxy, like '127.0.0.1:10888', by default None
        """
        
        self.timeout     = timeout
        self.proxy       = proxy    # in form of 127.0.0.1:8888
        self._conn       = None     # default HTTPConnection or  HTTPSConnection
        self._conn_table = {}

        self._httplibPathced = False

    def _create_connection(self, protocol, host, port):
        
        if protocol == 'http':
            connection_class = http.client.HTTPConnection
        elif protocol == 'https':
            connection_class = http.client.HTTPSConnection
        else:
            raise Exception(f'unsupported protocol: {protocol}')
        
        # set default connection
        if self.proxy is None:
            self._conn = connection_class(host, port, timeout=self.timeout)
        else:
            self._conn = connection_class(self.proxy, timeout=self.timeout)
            self._conn.set_tunnel(host, port)
            
        self._conn.protocol = protocol
        self._conn.cookie = SimpleCookie()


        self._conn_table[(protocol, host, port)] = self._conn
        
        self.host, self.port = self._conn.host, self._conn.port

        try:
            self._conn.connect()
        except ConnectionRefusedError:
            errInfo = 'connection refused, maybe server not started'
            print('!!! ConnectionRefusedError\n' + errInfo)
            TestLogger.write(f'80|{errInfo}')
            
            raise

        Stats.connection_num_increace()

    @staticmethod
    def _print_msg(msg :bytes, encoding: str, color=bcolors.OKGREEN, limit=4096):
        toolong = False
        if len(msg) > limit:
            msg = msg[:limit]
            toolong = True

        if encoding == 'hex':
            ostr = msg.hex('\n',-32).upper()           
        else:
            if encoding is None: encoding = 'utf8'
            ostr = msg.decode(encoding, errors="replace")
        
        if toolong:
            ostr += '\n.................'

        print(color + ostr + bcolors.ENDC, end='')

    

    @staticmethod
    def _urlAnalyze(url):
        protocol, host, port, path = None, None, None, None

        def handleUrlAfterHttpPrefix(url, urlPart, isSecure):
            if len(urlPart) == 0:
                raise Exception(f'url error:{url}')
            
            parts = urlPart.split('/',1)
            host = parts[0]
            path = '/' if len(parts)==1 else '/' + parts[1]

            if ':' not in host:
                port = 443 if isSecure else 80
            else:
                host, port = host.split(':')
                port = int(port)

            return host, port, path


        if url.startswith('http://'):
            protocol = 'http'
            host, port, path = handleUrlAfterHttpPrefix(url, url[7:], False)

        elif url.startswith('https://'):
            protocol = 'https'
            host, port, path = handleUrlAfterHttpPrefix(url, url[8:], True)

        else: # url only contain path
            path = url

        return protocol, host, port, path


    # send request, refer to https://docs.python.org/3/library/http.client.html#http.client.HTTPConnection.request
    def send(self,
            method:str,
            url:str,
            *,
            params:Union[None,Dict[str,str]]=None,
            headers:Union[None,Dict[str,str]]=None, 
            data:Union[None,Dict[str,str],str,bytes]=None, 
            json:Union[None,Dict[str,str]]=None,
            files:Union[None, List]=None,
            request_body_encoding:Union[None,str]=None,
            debug:bool=False,
            debug_print_request_body_encoding:Union[None,str]=None,
            debug_print_response_body_encoding:Union[None,str]=None,    
            debug_print_body_max_len:int=4096,        
            # duration:int=None,
        ):
        """Send HTTP request to server and receive response from server.

        Parameters
        ----------
        method : str
            HTTP method name, like 'GET', 'POST','PUT', 'DELETE','PATCH' ... 
            
            
        url : str
            HTTP URL for the HTTP request. 
            The first call must specify protocol/host/port prefix, like 'http://www.abc.com/a/b/c'.
            The following call could omit that, implying to use previous used protocol/host/port

        params : Dict[str, str] | None   (optional)
            Dictionary to send in the query string for the HTTP requests.

        headers : Dict[str, str] | None   (optional)
            Dictionary of HTTP Headers to send with the HTTP requests.

        data : Dict[str, str] | str | bytes | None   (optional)
            Dictionary, bytes, strings to send in the body of the HTTP requests.
            The usage is similar to library Requests.

        json : Dict[str, str] | None   (optional)
            A JSON serializable Python object to send in the body of the HTTP requests.   
            The usage is similar to library Requests.

        files: 
            This argument is used to upload files.
        
            call it like :

            client.post(
                'http://www.url-to-upload',
                files = [
                    'file1.mp4',  # file1 to upload
                    'file2.mp4',  # file2 to upload

                    # other form-data parameters
                    ("param1", 'value1' ), 
                    ("param2", 'value2' ),
                ],
                headers={
                    # necessary headers
                }
            )
            
        request_body_encoding : str | None   (optional)
            HTTP request body bytes encoding, all Python char-encoding are supported. 
            if not specified, hyload will use 'utf8' as text-encoding.  

        debug : bool   (optional)
            Whether print whole HTTP request and response, by default False means not print.

        debug_print_request_body_encoding : str | None   (optional)
            HTTP request body bytes encoding used for debug printing, all Python char-encoding are supported. 
            If not specified, hyload will used the value of paramter `request_body_encoding` .
            If the value is None finally, it will use 'utf8' as text-encoding.   
            If set to 'hex', it will print message body as bytes in hex string format.

        debug_print_response_body_encoding : str | None   (optional)
            HTTP response body bytes encoding used for debug printing, all Python char-encoding are supported. 
            if not specified, hyload will try to guess it from `Content-Type`.
            if no clue in `Content-Type`, it will use 'utf8' as text-encoding.   
            if set to 'hex', print bytes in hex string format.   

        debug_print_body_max_len : int    (optional)        
            If debug set to True, at most how many chars of HTTP body will be printed. 
            By default 4096.
            If body length is larger, the remaining will be displayed as "....."

        Returns
        -------
        HttpResponse
            

        Raises
        ------
        Exception
        """ 
        
        global _http_req_msg_buf_cpy

        if debug:
            if not self._httplibPathced:
                _patch_httplib_funcs()
                self._httplibPathced = True

        
        protocol, host, port, path = self._urlAnalyze(url)

        if not self._conn_table:  # no existing connections
            if protocol is None:
                raise Exception(f'url error:{url}, should have "http" or "https" as prefix')
            
            self._create_connection(protocol, host, port)
            # print('no existing connections, create new connection')

        else:                     # there are existing connections

            if protocol is not None:
                # print('protocol/host/port specified')
                self._conn = self._conn_table.get((protocol, host, port))
                if not self._conn:
                    # print('protocol/host/port not used before, create new connection')
                    self._create_connection(protocol, host, port)
                else:
                    # print('protocol/host/port used before , use old connection')
                    pass

            else:
                # print('protocol/host/port not specified, use default connection self._conn')
                pass   
             
            
        beforeSendTime = getCurTime()

        # headers 
        if headers is None: 
            headers = {}
        for k,v in _common_headers.items():
            if k not in headers:
                headers[k] = v

        # cookies
        if len(self._conn.cookie) > 0:
            headers.update({'Cookie':self._conn.cookie.output(header="",attrs=[],sep=';')})

        # url params
        if params is not None:
            queryStr = urlencode(params)
            if '?' in path:
                path += '&' + queryStr
            else:
                path += '?' + queryStr


        # body        
        body = None

        # msg body is in format of JSON
        if json is not None:
            if (request_body_encoding is None): request_body_encoding='utf-8'
            headers['Content-Type'] = 'application/json; charset=' + request_body_encoding
            body = jsonlib.dumps(json,ensure_ascii=False).encode(request_body_encoding)

        # multipart/form-data upload
        elif files is not None:
            header_ct, body = create_ct_body_for_uploading(files)
            headers['Content-Type'] = header_ct
        
        # msg body is in format of urlencoded
        elif data is not None:                        
            if type(data) == dict:
                if (request_body_encoding is None): request_body_encoding='utf-8'
                headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=' + request_body_encoding
                body = urlencode(data).encode(request_body_encoding)
            elif type(data) == str:
                if (request_body_encoding is None): request_body_encoding='utf-8'
                body = data.encode(request_body_encoding)
            elif type(data) == bytes:
                body = data

        try:
            self._conn.request(method, path, body, headers)
            if debug:
                headers,body = _http_req_msg_buf_cpy.split(b"\r\n\r\n",1)
                print('\n===========================')  
                self._print_msg(
                    headers, 
                    'utf8', 
                    bcolors.OKGREEN, 
                    100000)  
                
                if body:
                    print('\r\n\r\n',end='')

                    if debug_print_request_body_encoding is None:
                        debug_print_request_body_encoding = request_body_encoding
                    self._print_msg(
                        body, 
                        debug_print_request_body_encoding, 
                        bcolors.OKGREEN, 
                        debug_print_body_max_len)  
                    _http_req_msg_buf_cpy = b''
                print('\n---------------------------')    

        except ConnectionRefusedError:
            errInfo = 'connection refused, maybe server not started'
            print('!!! ConnectionRefusedError\n' + errInfo)
            TestLogger.write(f'80|{errInfo}')
            
            self._conn.close()
            
            raise
        
        except socket.timeout as e:
            print('!!! socket timeout', e)
            Stats.one_timeout()

            self._conn.close()
            Stats.connection_num_decreace()

            TestLogger.write(f'100|time out|{url}')

            return HttpResponse(error_type=100)
        
        except ConnectionAbortedError as e:
            print('!!! Connection Aborted during sending',e)
            Stats.one_error()

            self._conn.close()
            Stats.connection_num_decreace()
            
            TestLogger.write(f'101|Connection Aborted during sending|{url}')

            return HttpResponse(error_type=101)

        afterSendTime = Stats.one_sent()


        # recv response
        try:
            # getresponse() of http.client.Connection only gets reponse status line and headers.
            http_response = self._conn.getresponse()
            
            if debug:
                print(bcolors.OKBLUE + f"HTTP/{'1.1' if http_response.version==11 else '1.0'} {http_response.status} {http_response.reason}" + bcolors.ENDC)
                print(bcolors.OKBLUE + http_response.msg.as_string() + bcolors.ENDC,end='')
        except socket.timeout as e:
            print('!!! response timeout')

            Stats.one_timeout()

            self._conn.close()
            Stats.connection_num_decreace()
            
            TestLogger.write(f'110|response time out|{url}')
            return HttpResponse(error_type=110)
            
        except ConnectionAbortedError as e:
            print('!!! Connection Aborted during receiving response',e)
            Stats.one_error()

            self._conn.close()
            Stats.connection_num_decreace()
            
            TestLogger.write(f'111|Connection Aborted during receiving response|{url}')
            return HttpResponse(error_type=111)

        except http.client.RemoteDisconnected as e:    
            self._conn.close()
            Stats.connection_num_decreace()

            try:
                self._conn.request(method, path, body, headers)
                afterSendTime = Stats.one_sent()
                http_response = self._conn.getresponse()

                info = f'* after sending, server closed connection, reconnect and resending succeed|{url}'
                print(info)
                TestLogger.write(info)
            except:
                Stats.one_error()
                self._conn.close()
                Stats.connection_num_decreace()
                            
                err = f'120|after sending, server closed connection, reconnect and resending failed|{url}'
                print(err)
                TestLogger.write(err)
                return HttpResponse(error_type=120)
              
        recvTime = Stats.one_recv(afterSendTime)

        # check cookie
        cookieHdrs = http_response.getheader('set-cookie')
        if cookieHdrs:
            # print (cookieHdrs)
            self._conn.cookie.load(cookieHdrs)

        # if duration:
            
        #     # print(f'send {beforeSendTime} -- recv {recvTime}')
        #     extraWait = duration-(recvTime-beforeSendTime)
        #     if extraWait >0:  
        #         # print(f'sleep {extraWait}')
        #         time.sleep(extraWait)

        
        raw_body = http_response.read()
        
        if debug:
            contentEncoding = http_response.getheader('Content-Encoding')
            if contentEncoding == 'gzip':
                try: raw_body = gzip.decompress(raw_body)
                except OSError: pass      

            if debug_print_response_body_encoding is None:
                contentType = http_response.getheader('Content-Type')
                debug_print_response_body_encoding = _guessEncodingFromContentType(contentType)

            self._print_msg(
                raw_body,
                debug_print_response_body_encoding, 
                bcolors.OKBLUE,
                debug_print_body_max_len)     
            
            print('\n===========================\n')  


        self.response = HttpResponse(http_response,
                                   raw_body,
                                   int((recvTime-afterSendTime)*1000),
                                   path)
        
     
            
            
        return self.response
    
    def get(self, 
            url:str, 
            *,
            params:Union[None,Dict[str,str]]=None,
            headers:Union[None,Dict[str,str]]=None, 
            data:Union[None,Dict[str,str],str,bytes]=None, 
            json:Union[None,Dict[str,str]]=None,
            request_body_encoding:Union[None,str]=None,
            debug:bool=False,
            debug_print_request_body_encoding:Union[None,str]=None,
            debug_print_response_body_encoding:Union[None,str]=None,    
            debug_print_body_max_len:int=4096):
        """send HTTP request of 'get' method

        Parameters
        ----------
      
        url : str
            HTTP URL for the HTTP request. 
            The first call must specify protocol/host/port prefix, like 'http://www.abc.com/a/b/c'.
            The following call could omit that, implying to use previous used protocol/host/port

        params : Dict[str, str] | None   (optional)
            Dictionary to send in the query string for the HTTP requests.

        headers : Dict[str, str] | None   (optional)
            Dictionary of HTTP Headers to send with the HTTP requests.

        data : Dict[str, str] | str | bytes | None   (optional)
            Dictionary, bytes, strings to send in the body of the HTTP requests.
            The usage is similar to library Requests.

        json : Dict[str, str] | None   (optional)
            A JSON serializable Python object to send in the body of the HTTP requests.   
            The usage is similar to library Requests.

        request_body_encoding : str | None   (optional)
            HTTP request body bytes encoding, all Python char-encoding are supported. 
            if not specified, hyload will use 'utf8' as text-encoding.  

        debug : bool   (optional)
            Whether print whole HTTP request and response, by default False means not print.

        debug_print_request_body_encoding : str | None   (optional)
            HTTP request body bytes encoding used for debug printing, all Python char-encoding are supported. 
            If not specified, hyload will used the value of paramter `request_body_encoding` .
            If the value is None finally, it will use 'utf8' as text-encoding.   
            If set to 'hex', it will print message body as bytes in hex string format.

        debug_print_response_body_encoding : str | None   (optional)
            HTTP response body bytes encoding used for debug printing, all Python char-encoding are supported. 
            if not specified, hyload will try to guess it from `Content-Type`.
            if no clue in `Content-Type`, it will use 'utf8' as text-encoding.   
            if set to 'hex', print bytes in hex string format.   

        debug_print_body_max_len : int    (optional)        
            If debug set to True, at most how many chars of HTTP body will be printed. 
            By default 4096.
            If body length is larger, the remaining will be displayed as "....."

        Returns
        -------
        HttpResponse
            

        Raises
        ------
        Exception
        """
        return self.send('GET', url, 
                         params=params, 
                         headers=headers, 
                         data=data, 
                         json=json, 
                         request_body_encoding=request_body_encoding, 
                         debug=debug, 
                         debug_print_request_body_encoding=debug_print_request_body_encoding, 
                         debug_print_response_body_encoding=debug_print_response_body_encoding, 
                         debug_print_body_max_len=debug_print_body_max_len)
        
    def post(self, 
            url:str,
            *,
            params:Union[None,Dict[str,str]]=None,
            headers:Union[None,Dict[str,str]]=None, 
            data:Union[None,Dict[str,str],str,bytes]=None, 
            json:Union[None,Dict[str,str]]=None,
            files:Union[None, List]=None,
            request_body_encoding:Union[None,str]=None,
            debug:bool=False,
            debug_print_request_body_encoding:Union[None,str]=None,
            debug_print_response_body_encoding:Union[None,str]=None,    
            debug_print_body_max_len:int=4096,   ):
        """send HTTP POST request

        Parameters
        ----------
      
        url : str
            HTTP URL for the HTTP request. 
            The first call must specify protocol/host/port prefix, like 'http://www.abc.com/a/b/c'.
            The following call could omit that, implying to use previous used protocol/host/port

        params : Dict[str, str] | None   (optional)
            Dictionary to send in the query string for the HTTP requests.

        headers : Dict[str, str] | None   (optional)
            Dictionary of HTTP Headers to send with the HTTP requests.

        data : Dict[str, str] | str | bytes | None   (optional)
            Dictionary, bytes, strings to send in the body of the HTTP requests.
            The usage is similar to library Requests.

        json : Dict[str, str] | None   (optional)
            A JSON serializable Python object to send in the body of the HTTP requests.   
            The usage is similar to library Requests.

        files: 
            This argument is used to upload files.
        
            call it like :

            client.post(
                'http://www.url-to-upload',
                files = [
                    'file1.mp4',  # file1 to upload
                    'file2.mp4',  # file2 to upload

                    # other form-data parameters
                    ("param1", 'value1' ), 
                    ("param2", 'value2' ),
                ],
                headers={
                    # necessary headers
                }
            )

        request_body_encoding : str | None   (optional)
            HTTP request body bytes encoding, all Python char-encoding are supported. 
            if not specified, hyload will use 'utf8' as text-encoding.  

        debug : bool   (optional)
            Whether print whole HTTP request and response, by default False means not print.

        debug_print_request_body_encoding : str | None   (optional)
            HTTP request body bytes encoding used for debug printing, all Python char-encoding are supported. 
            If not specified, hyload will used the value of paramter `request_body_encoding` .
            If the value is None finally, it will use 'utf8' as text-encoding.   
            If set to 'hex', it will print message body as bytes in hex string format.

        debug_print_response_body_encoding : str | None   (optional)
            HTTP response body bytes encoding used for debug printing, all Python char-encoding are supported. 
            if not specified, hyload will try to guess it from `Content-Type`.
            if no clue in `Content-Type`, it will use 'utf8' as text-encoding.   
            if set to 'hex', print bytes in hex string format.   

        debug_print_body_max_len : int    (optional)        
            If debug set to True, at most how many chars of HTTP body will be printed. 
            By default 4096.
            If body length is larger, the remaining will be displayed as "....."

        Returns
        -------
        HttpResponse
            

        Raises
        ------
        Exception
        """
        return self.send('POST', url,
                         params=params, 
                         headers=headers, 
                         data=data, 
                         json=json, 
                         files=files,
                         request_body_encoding=request_body_encoding, 
                         debug=debug, 
                         debug_print_request_body_encoding=debug_print_request_body_encoding, 
                         debug_print_response_body_encoding=debug_print_response_body_encoding, 
                         debug_print_body_max_len=debug_print_body_max_len)
        
    def put(self, 
            url:str,
            *,
            params:Union[None,Dict[str,str]]=None,
            headers:Union[None,Dict[str,str]]=None, 
            data:Union[None,Dict[str,str],str,bytes]=None, 
            json:Union[None,Dict[str,str]]=None,
            request_body_encoding:Union[None,str]=None,
            debug:bool=False,
            debug_print_request_body_encoding:Union[None,str]=None,
            debug_print_response_body_encoding:Union[None,str]=None,    
            debug_print_body_max_len:int=4096,   ):
        """send HTTP PUT request

        Parameters
        ----------
      
        url : str
            HTTP URL for the HTTP request. 
            The first call must specify protocol/host/port prefix, like 'http://www.abc.com/a/b/c'.
            The following call could omit that, implying to use previous used protocol/host/port

        params : Dict[str, str] | None   (optional)
            Dictionary to send in the query string for the HTTP requests.

        headers : Dict[str, str] | None   (optional)
            Dictionary of HTTP Headers to send with the HTTP requests.

        data : Dict[str, str] | str | bytes | None   (optional)
            Dictionary, bytes, strings to send in the body of the HTTP requests.
            The usage is similar to library Requests.

        json : Dict[str, str] | None   (optional)
            A JSON serializable Python object to send in the body of the HTTP requests.   
            The usage is similar to library Requests.

        request_body_encoding : str | None   (optional)
            HTTP request body bytes encoding, all Python char-encoding are supported. 
            if not specified, hyload will use 'utf8' as text-encoding.  

        debug : bool   (optional)
            Whether print whole HTTP request and response, by default False means not print.

        debug_print_request_body_encoding : str | None   (optional)
            HTTP request body bytes encoding used for debug printing, all Python char-encoding are supported. 
            If not specified, hyload will used the value of paramter `request_body_encoding` .
            If the value is None finally, it will use 'utf8' as text-encoding.   
            If set to 'hex', it will print message body as bytes in hex string format.

        debug_print_response_body_encoding : str | None   (optional)
            HTTP response body bytes encoding used for debug printing, all Python char-encoding are supported. 
            if not specified, hyload will try to guess it from `Content-Type`.
            if no clue in `Content-Type`, it will use 'utf8' as text-encoding.   
            if set to 'hex', print bytes in hex string format.   

        debug_print_body_max_len : int    (optional)        
            If debug set to True, at most how many chars of HTTP body will be printed. 
            By default 4096.
            If body length is larger, the remaining will be displayed as "....."

        Returns
        -------
        HttpResponse
            

        Raises
        ------
        Exception
        """
        return self.send('PUT', url,
                         params=params, 
                         headers=headers, 
                         data=data, 
                         json=json, 
                         request_body_encoding=request_body_encoding, 
                         debug=debug, 
                         debug_print_request_body_encoding=debug_print_request_body_encoding, 
                         debug_print_response_body_encoding=debug_print_response_body_encoding, 
                         debug_print_body_max_len=debug_print_body_max_len)
        
    def delete(self, 
            url:str,
            *,
            params:Union[None,Dict[str,str]]=None,
            headers:Union[None,Dict[str,str]]=None, 
            data:Union[None,Dict[str,str],str,bytes]=None, 
            json:Union[None,Dict[str,str]]=None,
            request_body_encoding:Union[None,str]=None,
            debug:bool=False,
            debug_print_request_body_encoding:Union[None,str]=None,
            debug_print_response_body_encoding:Union[None,str]=None,    
            debug_print_body_max_len:int=4096,   ):
        """send HTTP DELETE request

        Parameters
        ----------
      
        url : str
            HTTP URL for the HTTP request. 
            The first call must specify protocol/host/port prefix, like 'http://www.abc.com/a/b/c'.
            The following call could omit that, implying to use previous used protocol/host/port

        params : Dict[str, str] | None   (optional)
            Dictionary to send in the query string for the HTTP requests.

        headers : Dict[str, str] | None   (optional)
            Dictionary of HTTP Headers to send with the HTTP requests.

        data : Dict[str, str] | str | bytes | None   (optional)
            Dictionary, bytes, strings to send in the body of the HTTP requests.
            The usage is similar to library Requests.

        json : Dict[str, str] | None   (optional)
            A JSON serializable Python object to send in the body of the HTTP requests.   
            The usage is similar to library Requests.

        request_body_encoding : str | None   (optional)
            HTTP request body bytes encoding, all Python char-encoding are supported. 
            if not specified, hyload will use 'utf8' as text-encoding.  

        debug : bool   (optional)
            Whether print whole HTTP request and response, by default False means not print.

        debug_print_request_body_encoding : str | None   (optional)
            HTTP request body bytes encoding used for debug printing, all Python char-encoding are supported. 
            If not specified, hyload will used the value of paramter `request_body_encoding` .
            If the value is None finally, it will use 'utf8' as text-encoding.   
            If set to 'hex', it will print message body as bytes in hex string format.

        debug_print_response_body_encoding : str | None   (optional)
            HTTP response body bytes encoding used for debug printing, all Python char-encoding are supported. 
            if not specified, hyload will try to guess it from `Content-Type`.
            if no clue in `Content-Type`, it will use 'utf8' as text-encoding.   
            if set to 'hex', print bytes in hex string format.   

        debug_print_body_max_len : int    (optional)        
            If debug set to True, at most how many chars of HTTP body will be printed. 
            By default 4096.
            If body length is larger, the remaining will be displayed as "....."

        Returns
        -------
        HttpResponse
            

        Raises
        ------
        Exception
        """
        return self.send('DELETE', url,
                         params=params, 
                         headers=headers, 
                         data=data, 
                         json=json, 
                         request_body_encoding=request_body_encoding, 
                         debug=debug, 
                         debug_print_request_body_encoding=debug_print_request_body_encoding, 
                         debug_print_response_body_encoding=debug_print_response_body_encoding, 
                         debug_print_body_max_len=debug_print_body_max_len)
        
    def head(self,
            url:str,
            *,
            params:Union[None,Dict[str,str]]=None,
            headers:Union[None,Dict[str,str]]=None, 
            data:Union[None,Dict[str,str],str,bytes]=None, 
            json:Union[None,Dict[str,str]]=None,
            request_body_encoding:Union[None,str]=None,
            debug:bool=False,
            debug_print_request_body_encoding:Union[None,str]=None,
            debug_print_response_body_encoding:Union[None,str]=None,    
            debug_print_body_max_len:int=4096,   ):
        """send HTTP HEAD request

        Parameters
        ----------
      
        url : str
            HTTP URL for the HTTP request. 
            The first call must specify protocol/host/port prefix, like 'http://www.abc.com/a/b/c'.
            The following call could omit that, implying to use previous used protocol/host/port

        params : Dict[str, str] | None   (optional)
            Dictionary to send in the query string for the HTTP requests.

        headers : Dict[str, str] | None   (optional)
            Dictionary of HTTP Headers to send with the HTTP requests.

        data : Dict[str, str] | str | bytes | None   (optional)
            Dictionary, bytes, strings to send in the body of the HTTP requests.
            The usage is similar to library Requests.

        json : Dict[str, str] | None   (optional)
            A JSON serializable Python object to send in the body of the HTTP requests.   
            The usage is similar to library Requests.

        request_body_encoding : str | None   (optional)
            HTTP request body bytes encoding, all Python char-encoding are supported. 
            if not specified, hyload will use 'utf8' as text-encoding.  

        debug : bool   (optional)
            Whether print whole HTTP request and response, by default False means not print.

        debug_print_request_body_encoding : str | None   (optional)
            HTTP request body bytes encoding used for debug printing, all Python char-encoding are supported. 
            If not specified, hyload will used the value of paramter `request_body_encoding` .
            If the value is None finally, it will use 'utf8' as text-encoding.   
            If set to 'hex', it will print message body as bytes in hex string format.

        debug_print_response_body_encoding : str | None   (optional)
            HTTP response body bytes encoding used for debug printing, all Python char-encoding are supported. 
            if not specified, hyload will try to guess it from `Content-Type`.
            if no clue in `Content-Type`, it will use 'utf8' as text-encoding.   
            if set to 'hex', print bytes in hex string format.   

        debug_print_body_max_len : int    (optional)        
            If debug set to True, at most how many chars of HTTP body will be printed. 
            By default 4096.
            If body length is larger, the remaining will be displayed as "....."

        Returns
        -------
        HttpResponse
            

        Raises
        ------
        Exception
        """
        return self.send('HEAD', url,
                         params=params, 
                         headers=headers, 
                         data=data, 
                         json=json, 
                         request_body_encoding=request_body_encoding, 
                         debug=debug, 
                         debug_print_request_body_encoding=debug_print_request_body_encoding, 
                         debug_print_response_body_encoding=debug_print_response_body_encoding, 
                         debug_print_body_max_len=debug_print_body_max_len)

    def patch(self, url, **kargs):
        """send HTTP PATCH request

        Parameters
        ----------
      
        url : str
            HTTP URL for the HTTP request. 
            The first call must specify protocol/host/port prefix, like 'http://www.abc.com/a/b/c'.
            The following call could omit that, implying to use previous used protocol/host/port

        params : Dict[str, str] | None   (optional)
            Dictionary to send in the query string for the HTTP requests.

        headers : Dict[str, str] | None   (optional)
            Dictionary of HTTP Headers to send with the HTTP requests.

        data : Dict[str, str] | str | bytes | None   (optional)
            Dictionary, bytes, strings to send in the body of the HTTP requests.
            The usage is similar to library Requests.

        json : Dict[str, str] | None   (optional)
            A JSON serializable Python object to send in the body of the HTTP requests.   
            The usage is similar to library Requests.

        request_body_encoding : str | None   (optional)
            HTTP request body bytes encoding, all Python char-encoding are supported. 
            if not specified, hyload will use 'utf8' as text-encoding.  

        debug : bool   (optional)
            Whether print whole HTTP request and response, by default False means not print.

        debug_print_request_body_encoding : str | None   (optional)
            HTTP request body bytes encoding used for debug printing, all Python char-encoding are supported. 
            If not specified, hyload will used the value of paramter `request_body_encoding` .
            If the value is None finally, it will use 'utf8' as text-encoding.   
            If set to 'hex', it will print message body as bytes in hex string format.

        debug_print_response_body_encoding : str | None   (optional)
            HTTP response body bytes encoding used for debug printing, all Python char-encoding are supported. 
            if not specified, hyload will try to guess it from `Content-Type`.
            if no clue in `Content-Type`, it will use 'utf8' as text-encoding.   
            if set to 'hex', print bytes in hex string format.   

        debug_print_body_max_len : int    (optional)        
            If debug set to True, at most how many chars of HTTP body will be printed. 
            By default 4096.
            If body length is larger, the remaining will be displayed as "....."

        Returns
        -------
        HttpResponse
            

        Raises
        ------
        Exception
        """
        return self.send('PATCH', url,**kargs)


