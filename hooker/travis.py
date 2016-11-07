"""Hooker authenticator for travis."""

from OpenSSL.crypto import verify, load_publickey, FILETYPE_PEM, X509
from OpenSSL.crypto import Error as SignatureError
from urlparse import parse_qs

import base64
import logging
import requests


def authenticate(config, request):
    """
    Validate the webhook request from travis using certificates.

    Got inspiration for this from the official travis docs and
    https://gist.github.com/andrewgross/8ba32af80ecccb894b82774782e7dcd4
    :param config: dict
    :param request: request
    :return: boolean
    """
    travis_url = config['PUBKEY_URL']

    signature = _get_signature(request)
    json_payload = parse_qs(request.get_data())['payload'][0]

    try:
        public_key = _get_travis_public_key(travis_url)
    except requests.Timeout:
        logging.error({"message": "Timed out when attempting to retrieve Travis CI public key"})
        return False
    except requests.RequestException as e:
        logging.error({"message": "Failed to retrieve Travis CI public key", 'error': e.message})
        return False
    try:
        check_authorized(signature, public_key, json_payload)
    except SignatureError:
        logging.error({"message": "Request with invalid Signature from Travis"})
        return False
    return True


def assess_reload(request):
    """
    Decision on whether to reload or not done in travis.yaml.

    :param request: request
    :return: booleam
    """
    return True


def check_authorized(signature, public_key, payload):
    """Convert PEM encoded public key to a format palatable for pyOpenSSL."""
    pkey_public_key = load_publickey(FILETYPE_PEM, public_key)
    certificate = X509()
    certificate.set_pubkey(pkey_public_key)
    verify(certificate, signature, payload, str('sha1'))


def _get_signature(request):
    """Extract the raw bytes of the request signature provided by travis."""
    signature = request.headers.get('Signature')
    return base64.b64decode(signature)


def _get_travis_public_key(travis_url):
    """Return the PEM encoded public key from the Travis /config endpoint."""
    response = requests.get(travis_url, timeout=10.0)
    response.raise_for_status()
    return response.json()['config']['notifications']['webhook']['public_key']