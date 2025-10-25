implement a http server to test http client.

When receiving a http request, the server could be set to 

- not send any response;

- just send part of the status line;

- just send the status line of http response;

- just send the status line and http headers of response without msg body;

- just send part of the msg body of http response




* No response: http://localhost:8000/?no_response=true
* partial status line:  http://127.0.0.1:8000?partial_status=true
* Status line only: http://localhost:8000/?status_only=true
* Status and headers only: http://localhost:8000/?headers_only=true
* Partial body: http://localhost:8000/?partial_body=true
* Full response: http://localhost:8000/