import argparse
import datetime
import logging
import subprocess

from flask import Flask, render_template

app = Flask(__name__)
command = ''
log = dict()


def _restart():
    global command
    success = True
    try:
        output = subprocess.check_output([command])
    except Exception as err:
        success = False
        output = 'Error {} while executing {}'.format(err, command)
    return success, output

@app.route('/', methods=['POST'])
def post_hook():
    global log
    logging.debug('post')
    #gitlab_header = request.headers.get('X-Gitlab-Event')
    #if gitlab_header :
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    response = 'Executing restart action at {}'.format(current_time)
    logging.info(response)
    success, output = _restart()
    log[current_time] = output

    if success:
        return output, 200
    else:
        return output, 500
    #else:
    #    response = 'Not gitlab, no action'
    #    logging.info(response)


@app.route('/logs/', methods=['GET'])
def get_logs():
    global log
    return render_template('logs.html', logs=log.keys())


@app.route('/logs/<log_id>', methods=['GET'])
def get_log(log_id):
    global log
    return render_template('log.html', log_timestamp=log_id, content=log[log_id])


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
