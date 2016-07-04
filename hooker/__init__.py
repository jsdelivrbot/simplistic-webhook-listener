import logging
import subprocess
import sys

from pydoc import locate


class Hooker(object):

    def __init__(self, config):
        try:
            hooker = config['HOOKER']
            self.delegate_authentication = locate('hooker.{}.authenticate'
                                                  .format(hooker))
            self.assess_reload = locate('hooker.{}.assess_reload'
                                        .format(hooker))
        except ImportError as err:
            logging.error('selected hooker not availabe')
            exit(1)
        except KeyError as err:
            logging.error('HOOKER is required, gitlab/github/travis')
            exit(1)
        try:
            self.command = config['COMMAND']
        except KeyError as err:
            logging.error('COMMAND is required to know what the webhook'
                          ' should execute on this server')
            exit(1)
        try:
            self.tokens = config['TOKENS']
        except KeyError as err:
            logging.info('No tokens provided, no authentication')
            self.tokens = False

    def authenticate(self, request):
        if self.tokens:
            return self.delegate_authentication(self.tokens, request)
        else:
            return True

    def execute_command(self):
        try:
            output = subprocess.check_output(self.command.split())
        except Exception as err:
            output = 'Error {} while executing {}'.format(err, self.command)
        return output


def compare(tokens, auth_header):

    major = sys.version_info.major
    minor = sys.version_info.minor
    micro = sys.version_info.micro

    logging.debug(tokens)
    for token in tokens.split(';'):
        if (major == 2 and minor <= 7 and micro < 7) \
                or (major == 3 and minor < 3):
            logging.debug('Using own compare function for authorization token')
            valid = True
            if len(token) != len(auth_header):
                valid = False
            for iterator, item in enumerate(token):
                if item != auth_header[iterator]:
                    valid = False
            if valid:
                return True
        else:
            logging.debug('Using hmac compare function for auth token')
            import hmac
            if hmac.compare_digest(unicode(token), auth_header):
                return True
