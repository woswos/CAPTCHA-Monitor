import email
import io
import json


def tb(requests_data):
    cleaned = {'data': []}
    for request in requests_data['data']:
        temp = {}
        for key, value in request.items():
            if value is not '':
                temp[key] = parse_headers(value)

        # Skip the internal request to the browser extension
        if '255.255.255.255' not in str(temp['url']):
            cleaned['data'].append(temp)
    return json.dumps(cleaned)


def seleniumwire(requests_data):
    cleaned = {'data': []}
    for request in requests_data:
        temp = {}
        #temp['post_data'] = ''
        if request.headers is not None:
            temp['request_headers'] = dict(request.headers)
        if request.response is not None:
            temp['response_headers'] = dict(request.response.headers)
            temp['status_line'] = parse_headers(
                (str(request.method) + ': ' + str(request.response.status_code) + ' ' + str(request.response.reason)))
        if request.path is not None:
            temp['url'] = request.path
        cleaned['data'].append(temp)
    return json.dumps(dict(cleaned))


def curl(request_headers, response_headers, status_line):
    cleaned = {'data': []}
    temp = {}
    temp['request_headers'] = request_headers
    temp['response_headers'] = response_headers
    temp['status_line'] = parse_headers('GET: ' + str(status_line))
    cleaned['data'].append(temp)
    return json.dumps(cleaned)


def requests(request_headers, response_headers, status_code):
    cleaned = {'data': []}
    temp = {}
    temp['request_headers'] = request_headers
    temp['response_headers'] = response_headers
    temp['status_line'] = parse_headers('GET: ' + str(status_code))
    cleaned['data'].append(temp)
    return json.dumps(cleaned)


def parse_headers(raw_headers):
    # Check if the header is a single word string
    if ' ' in raw_headers:
        #request_line, headers_alone = request_text.split('\r\n', 1)
        message = email.message_from_file(io.StringIO(raw_headers))
        return dict(message.items())
    else:
        return raw_headers
