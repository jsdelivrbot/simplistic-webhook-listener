from hooker import compare


def authenticate(tokens, request):
    auth_header = request.headers.get('Authorization')

    return compare(tokens, auth_header) if auth_header else False
