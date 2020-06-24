import email
import io


def clean_requests(requests_data):
    cleaned = {'data': []}
    for request in requests_data['data']:
        temp = {}

        for key, value in request.items():
            if value is not '':
                temp[key] = parse_headers(value)

        cleaned['data'].append(temp)
    return cleaned


def parse_headers(raw_headers):
    # Check if the header is a single word string
    if ' ' in raw_headers:
        #request_line, headers_alone = request_text.split('\r\n', 1)
        message = email.message_from_file(io.StringIO(raw_headers))
        return dict(message.items())
    else:
        return raw_headers
