import argparse
import datetime
import logging
import subprocess

from flask import Flask, request
from flask_api.decorators import set_parsers
from flask_api.parsers import URLEncodedParser

app = Flask(__name__)

command = ''


def _restart():
    global command
    return subprocess.call(command, shell=True)


@app.route('/', methods=['POST'])
@set_parsers(URLEncodedParser)
def post_hook():
    logging.debug('post')
    #gitlab_header = request.headers.get('X-Gitlab-Event')
    #if gitlab_header :
    response = 'Executing restart action at {}'.format(
        datetime.datetime.now())
    logging.info(response)
    _restart()
    #else:
    #    response = 'Not gitlab, no action'
    #    logging.info(response)
    return response, 200

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--command",
                        help="reload command that should be executed")
    parser.add_argument("--debug",
                        help="get debug output",
                        action="store_true")
    parser.add_argument("--logstash",
                        help="log everything (in addition) to logstash "
                             ", give host:port")
    parser.add_argument("--port",
                        help="port to use for listening")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(format='%(message)s', level=logging.DEBUG)
        debug=True
    else:
        logging.basicConfig(format='%(message)s', level=logging.INFO)
        debug=False
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    if args.logstash:
        import logstash
        host, port = args.logstash.split(':')
        logger.addHandler(logstash.TCPLogstashHandler(host=host,
                                                      port=int(port),
                                                      version=1))

    if args.command:
        global command
        command = args.command
    else:
        logging.error('--command <script> is required for this webhook')
        exit(1)
    if args.port:
        port = int(args.port)
    else:
        port = 7010
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
