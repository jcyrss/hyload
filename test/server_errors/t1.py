from hyload import *

client = HttpClient(timeout=1)
                   
response = client.get(
    # 'http://127.0.0.1:8000?no_response=true',
    'http://127.0.0.1:8000?partial_status=true',
    # 'http://127.0.0.1:8000?status_only=true',
    # 'http://127.0.0.1:8000?headers_only=true',
    #  'http://127.0.0.1:8000?partial_body=true',
    # 'http://127.0.0.1:8000',
    debug = True # to print HTTP message
)

