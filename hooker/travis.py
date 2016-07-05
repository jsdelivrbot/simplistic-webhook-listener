from hooker import compare


def authenticate(tokens, request):
    auth_header = request.headers.get('Authorization')

    return compare(tokens, auth_header) if auth_header else False

def assess_reload(request):
    webhook_action = request.headers.get('X-Gitlab-Event')
    if webhook_action == u'Build Hook':
        payload = request.get_json()
        if payload and payload['build_status'] == 'success':
            logging.debug('Got successfull build_status from gitlab, reload')
            return True
        else:
            return False
    elif webhook_action == u'Push Hook':
        logging.debug('Got push from gitlab, reload')
        return True
    else:
        return False