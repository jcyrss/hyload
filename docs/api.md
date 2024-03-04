---
title: API Reference
---


## Stats

### start

it should be call first to start stats task, so all stats info could be sent to realtime monitor and recorded into stats files for later use.

### set_response_time_ranges

It is to set response time ranges, so in the statistics we could see how many reponses in what response time range.

If not called, default ranges are: 0-100ms , 100-500ms, 500-1000ms , >1000ms 


<br>

It should be called before calling the method `start`, and the paramter is a list of int to specify the ranges.

The following code will set the ranges to 0-100ms , 100-500ms, 500-1000ms , >1000ms

```py
Stats.set_response_time_ranges([100, 500, 1000])
```

After testing done, we will get stats like this

```py
0-100ms      : 100
100-500ms    : 130
500-1000ms   : 23
>1000ms      : 3
```

if not set, [100, 500, 1000,3000] will be the default one.




## HttpClient 

One `HttpClient` object represents a http client，it is defined as this

```py
def __init__(self, timeout:int=10, proxy: None|str=None)
```
<br>

Parameters:

- timeout : int  (optional)
        
    It is the timeout value for network operations, like connecting. , by default 10

  
- proxy :  `None|str`  (optional)
        
    It is to specify the proxy, like '127.0.0.1:10888', by default None

  
 


### send 

`send`  method is used to send HTTP request to server and receive response from server.

```py
def send(self,
    method: str,
    url:    str,
    params: Dict[str, str] | None=None,
    headers:Dict[str, str] | None=None, 
    data:   Dict[str, str] | str | bytes | None=None, 
    json:   Dict[str, str] | None=None,
    request_body_encoding:str | None=None,
    debug:bool=False,
    debug_print_request_body_encoding:  str | None=None,
    debug_print_response_body_encoding: str | None=None,    
    debug_print_body_max_len:           int=4096,  
):
```



Parameters:


- method : str
    HTTP method name, like 'GET', 'POST','PUT', 'DELETE','PATCH','HEAD'.
    
    For example:

    ```py
    client.send('GET', '/api/path1')
    ```

    <br>

    hyload also has some shotcuts methods to use `get/post/put/delete/patch/head` as method names.

    The above code could be simpified like this,

    ```py
    client.get('/api/path1')
    ```

    
    
- url : str
    HTTP URL for the HTTP request. 

    The first call must specify protocol/host/port prefix, like 'http://www.abc.com/a/b/c'.

    The following call could omit that, implying to use previous used protocol/host/port.

    like

    ```py
    client.send(
            'POST', 
            'http://127.0.0.1/api/mgr/signin',
            data={
                'username':'byhy',
                'password':'88888888'
            },
            
        )

    client.get('/your-url-path')
    ```

- params :  `Dict[str, str] | None`    (optional)
  
    Dictionary to send in the query string for the HTTP requests.

    The usage is similar to library  `Requests` .

    Like,
    
    ```py
    client.get(
      'http://127.0.0.1/api/path1'
      params={
          'p1':'value1',
          'p2':'value2'
      }
    )
    ```

    <br>

    You could also put urlencoded params in query string directly, like

   
    ```py
    client.get('http://127.0.0.1/api/path1?p1=value1&p2=value2')
    ```


- headers :  `Dict[str, str] | None`    (optional)
  
    Dictionary of HTTP Headers to send with the HTTP requests.

    The usage is similar to library  `Requests` .

    Just put key/value pair into a dict, and pass it to parameter `headers`, like

    ```py
    client.get(
        '/api/path1',
        headers={
            'header1':'value1',
            'header2':'value2'
        })
    ```



- data :  `Dict[str, str] | str | bytes | None`    (optional)
  
    Dictionary, bytes, strings to send in the body of the HTTP requests.
    
    The usage is similar to library  `Requests`.

    <br>

    Like, if messasge body is  `application/x-www-form-urlencoded` format, the code could be like this


    ```py
    client.post(
        '/api/path1',
        data={
            'action':'addfriends'
            'userid': '3344',
            'friends': '3242,234545,232'
        })
    ```


    hyload uses  `utf8`  encoding by default.

    If you want other encoding type, specify it with parameter  `request_body_encoding`, like

    ```py
    client.post(
        '/api/path1',
        data={
            'action':'addfriends'
            'userid': 3344,
            'friends': '白月黑羽, 紫气一元'
        },
        request_body_encoding = 'gbk'
    )        
    ```

    We don't have to set HTTP header  `Content-Type` to `application/x-www-form-urlencoded` here, because hyload will do that automatically.

    <br>

    If message body is in other format, like XML, YAML, TOML, etc, we still use parameter `data` with the  **string**  value in corresponding format, and set HTTP header `Content-Type` accordingly.

    Like,

    ```py
    client.post(
        '/api/path1',
        headers={
            # message type is XML
            'Content-Type':'application/xml'
        }
        # message body
        data='''
        <?xml version="1.0" encoding="UTF-8"?>
        <CreateBucketConfiguration>
            <StorageClass>Standard</StorageClass>
        </CreateBucketConfiguration>
        '''
        )
    ```


    Similarly, hyload uses  `utf8`  encoding by default. If you want other encoding type, specify it with parameter  `request_body_encoding`.

    <br>

    
    If message body is not text chars at all, like self define binary format, or image file content, we still use parameter `data` with   **bytes**   value, and set HTTP header `Content-Type` accordingly.

    Like,

    ```py
    client.post(
        '/api/path1',
        headers={
            'Content-Type':'application/some-bin-format'
        }
        data=b'\x9f\x5c\x56\x90\xee\x34\x5c\x90\xee\x34\x56\x90'
        )
    ```

- json :  `Dict[str, str] | None`    (optional)
  
    A JSON serializable Python object to send in the body of the HTTP requests.   

    The usage is similar to library  `Requests` .

    <br>

    Like,

    ```py
    client.post(
        '/api/path1',
        json={
            'action':'addfriends'
            'userid': 3344,
            'friends': [3242,234545,232]
        })
    ```

    
    We don't have to set HTTP header  `Content-Type` to `application/json` here, because hyload will do that automatically.

    Similarly, hyload uses  `utf8`  encoding by default. If you want other encoding type, specify it with parameter  `request_body_encoding`, like

    ```py
    client.post(
        '/api/path1',
        json={
            'action':'addfriends'
            'userid': 3344,
            'friends': ['白月黑羽', '紫气一元']
        },
        request_body_encoding = 'gbk'
    )        
    ```

- request_body_encoding :  `str | None`    (optional)
  
    HTTP request body bytes encoding, it is used when request message body is a text string.
    
    All Python char-encoding values are supported. 

    If not specified, hyload will use 'utf8' as text-encoding.  

- debug : bool   (optional)
  
    Whether print whole HTTP request and response, by default it is `False` not to print anything.

- debug_print_request_body_encoding :  `str | None`    (optional)
  
    HTTP request body bytes encoding used for debug printing, all Python char-encoding are supported. 

    If not specified, hyload will used the value of paramter `request_body_encoding` .

    If the value is None finally, it will use 'utf8' as text-encoding.   

    If set to 'hex', it will print message body as bytes in hex string format.

- debug_print_response_body_encoding :  `str | None`    (optional)
  
    HTTP response body bytes encoding used for debug printing, all Python char-encoding are supported. 

    If not specified, hyload will try to guess it from `Content-Type`.

    If no clue in `Content-Type`, it will use 'utf8' as text-encoding.   

    If set to 'hex', print bytes in hex string format.   

- debug_print_body_max_len : int    (optional)        
  
    If debug set to True, at most how many chars of HTTP body will be printed. 

    By default 4096.

    If body length is larger, the remaining will be displayed as  `.....` 

<br>

`send` method returns a  `HttpResponse` object.



### get/post/put/delete/patch/head

They are shotcut methods of  `send(method=xxx, ...)` 




## HttpResponse 

`send` method returns a  `HttpResponse` object through which we could get information like response status code/headers/body, response time, etc.


### error_type

If server did reponse, the value of the attribute `error_type` of HttpResponse is  `None` .

Otherwise, it is a integer value indicate no reponse, and something wrong happend.

- 100 sending request timeout
- 101 connection aborted during sending request
- 110 receieving reponse timeout
- 111 connection aborted during receieving reponse
- 120 reconnect and resending failed


### response_time

We could get response time by the attribute `response_time` of HttpResponse.

It is in milliseconds.

Like

```py
res = client.get('/api/path1' )
print(f"response time is {res.response_time} ms") 
```


### status_code


We could get status code by the attribute `status_code` of HttpResponse.

Like

```py
res = client.get('/api/path1' )
print(f"status code is {res.status_code} ") 
```


### headers


We could get status code by the attribute `headers` of HttpResponse.

We can view the server’s response headers like this:

```py
client = HttpClient() 
res = client.get('/api/path1' )

print(res.headers)
```

The output is like this

```
Content-Type: application/json; charset=utf-8
Date: Tue, 06 Feb 2024 03:41:17 GMT
Content-Length: 141


```

<br>


HTTP Header names are case-insensitive.

So, we can access the headers using any capitalization we want:

```py
>>> res.headers['Content-Type']
'application/json'

>>> res.headers.get('content-type')
'application/json'
```




### text

If response body is text, We can read the content of the server’s response as string by attribute `text`, like this

```py
client = HttpClient() 
res = client.get('https://api.github.com/events' )
print(f"response body is:\n {res.text} ") 
```

`hyload`  will automatically decode content from the server. 

`hyload` makes guesses about the encoding of the response based on the HTTP headers. The text encoding guessed by hyload is used when you access r.text. You can find out what encoding hyload is using, and change it, using the  `encoding`  attribute:

比如

```py
client = HttpClient() 
res = client.get('https://www.163.com/' )

r.encoding = 'gbk'
print(f"response body is:\n{res.text} ") 
```



### json()


If response body is text in JSON format, you could just use method `json()` of reponse object to parse it and get corresponding Python object.

Like

```py
client = HttpClient() 
res = client.get('https://httpbin.org/json' )
print(f"response body is:\n{res.json()} ") 
```



### content

You can also access the response body as bytes, usually for non-text requests, by attribute `content`,:

```py
client = HttpClient() 
res = client.get('https://httpbin.org/image' )

body = res.content
```


## run_task

By calling `run_task` with passing callable object as parameter `target` , usually a function or method, hyload will run target code in `hyload task`, which is a  `greenlet` (a coroutine, a light-weight thread) under the hood.

All tasks run in parallel.

## wait_for_tasks_done

Calling `wait_for_tasks_done` will wait until all `hyload tasks` are over.