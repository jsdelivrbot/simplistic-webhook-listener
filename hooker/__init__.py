import logging
import sys


def compare(tokens, auth_header):

    major = sys.version_info.major
    minor = sys.version_info.minor
    micro = sys.version_info.micro
    for token in tokens.split(';'):
        if (major == 2 and minor <= 7 and micro < 7) \
                or (major == 3 and minor < 3):
            logging.debug('Using own compare function for authorization token')
            valid = True
            if len(token) != len(auth_header):
                return False
            for iterator, item in enumerate(token):
                if item != auth_header[iterator]:
                    valid = False
            return valid
        else:
            logging.debug('Using hmac compare function for auth token')
            import hmac
            return hmac.compare_digest(unicode(token), auth_header)
