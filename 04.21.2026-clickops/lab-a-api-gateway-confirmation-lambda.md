Incoming event: {
    "version": "2.0",
    "routeKey": "GET /python",
    "rawPath": "/prod/python",
    "rawQueryString": "name=Chewbacca",
    "headers": {
        "accept": "*/*",
        "content-length": "0",
        "host": "5npm41zgj7.execute-api.us-west-2.amazonaws.com",
        "user-agent": "curl/8.7.1",
        "x-amzn-trace-id": "Root=1-69e8589d-57479de51aeebd0a67aee37b",
        "x-forwarded-for": "174.53.22.49",
        "x-forwarded-port": "443",
        "x-forwarded-proto": "https"
    },
    "queryStringParameters": {
        "name": "Chewbacca"
    },
    "requestContext": {
        "accountId": "390402551087",
        "apiId": "5npm41zgj7",
        "domainName": "5npm41zgj7.execute-api.us-west-2.amazonaws.com",
        "domainPrefix": "5npm41zgj7",
        "http": {
            "method": "GET",
            "path": "/prod/python",
            "protocol": "HTTP/1.1",
            "sourceIp": "174.53.22.49",
            "userAgent": "curl/8.7.1"
        },
        "requestId": "cNLIqhTsPHcEJSA=",
        "routeKey": "GET /python",
        "stage": "prod",
        "time": "22/Apr/2026:05:11:57 +0000",
        "timeEpoch": 1776834717419
    },
    "isBase64Encoded": false
}

Response: {
    "message": "Hello Chewbacca from Python!",
    "timestamp": "2026-04-22T05:11:57.747370"
}

