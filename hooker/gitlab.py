"""Hooker authenticator for gitlab."""

import logging
from hooker import compare


def authenticate(config, request):
    """
    Check request for X-Gitlab-Token and validate it with configured tokens.

    The authenticate implementation for gitlab takes a request header and
    compares it to a list of token from config file.
    :param config: dict
    :param request: request
    :return: boolean
    """
    try:
        tokens = config['TOKENS']
    except KeyError as err:
        logging.info('No tokens provided, no authentication')
        return False

    auth_header = request.headers.get('X-Gitlab-Token')
    return compare(tokens, auth_header) if auth_header else False


def assess_reload(request):
    """
    Assess whether the webhook is allowed to execute the reload command.

    Based on the X-Gitlab-Header decide on whether to execute the reload
    command or not.
    :param request: request
    :return: boolean
    """
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
