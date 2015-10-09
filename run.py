import argparse
import logging
import os
import subprocess
import time

from datetime import datetime
from flask import Flask, render_template, send_from_directory as send_file
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///logs.db'
Bootstrap(app)
db = SQLAlchemy(app)

command = ''


class WebhookCall(db.Model):
    __tablename__ = 'webhookcall'
    timestamp = db.Column(db.Integer, primary_key=True, unique=True)
    repository = db.Column(db.String(20))
    success = db.Column(db.Boolean)
    results = db.relationship('WebhookCallResult',
                              backref=db.backref('webhookcall'))

    def __init__(self, timestamp, repository, success):
        self.timestamp = timestamp
        self.repository = repository
        self.success = success

    def __repr__(self):
        return '<WebhookCall %r>' % self.timestamp

    def __gt__(self, other):
        return True if int(self.timestamp) > int(other.timestamp) else False

    def __lt__(self, other):
        return True if int(self.timestamp) < int(other.timestamp) else False


class WebhookCallResult(db.Model):
    __tablename__ = 'webhookcallresult'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.Integer, db.ForeignKey('webhookcall.timestamp'))
    output = db.Column(db.String(1000))

    def __init__(self, timestamp, output):
        self.timestamp = timestamp
        self.output = output

    def __repr__(self):
        return '<WebhookCallResult %r>' % self.id


def _restart():
    global command
    success = True
    try:
        output = subprocess.check_output([command])
    except Exception as err:
        output = 'Error {} while executing {}'.format(err, command)
    return output


@app.route('/', methods=['POST'])
@app.route('/<hooking_repository>/', methods=['POST'])
def post_hook(hooking_repository=None):
    if hooking_repository:
        if len(hooking_repository) < 20:
            repository = hooking_repository
        else:
            repository = hooking_repository[0:20]
    else:
        repository = 'unknown'
    current_time = int(time.time())
    output = _restart()
    success = False if 'Error' in output else True
    output = output.strip()
    item = WebhookCall.query.filter_by(timestamp=current_time).first()
    if not item:
        db.session.add(WebhookCall(current_time, repository, success))
        db.session.add(WebhookCallResult(timestamp=current_time,
                                         output=output))
    else:
        db.session.add(WebhookCallResult(timestamp=current_time,
                                         output=output))
    db.session.commit()

    response = 'Executed restart action at {} with output:\n{}'\
        .format(format_datetime(current_time), output)
    if success:
        return response, 200
    else:
        return response, 500


@app.route('/logs/', methods=['GET'])
def get_logs():
    return render_template('logs.html', content=WebhookCall.query.all())


@app.route('/logs/<log_id>', methods=['GET'])
def get_log(log_id):
    logs = WebhookCallResult.query.filter(
        WebhookCallResult.timestamp == log_id).all()
    if logs:
        return render_template('log.html', timestamp=log_id, logs=logs)
    else:
        return '', 404


@app.route('/favicon.ico')
def favicon():
    return send_file(os.path.join(app.root_path, 'static'), 'favicon.ico')


@app.template_filter('datetime')
def format_datetime(value):
    return datetime.fromtimestamp(int(value))\
        .strftime("%Y-%m-%d_%H-%M-%S")


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
        debug = True
    else:
        logging.basicConfig(format='%(message)s', level=logging.INFO)
        debug = False
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    if args.logstash:
        try:
            import logstash
            host, port = args.logstash.split(':')
            logger.addHandler(logstash.TCPLogstashHandler(host=host,
                                                          port=int(port),
                                                          version=1))
        except ImportError as err:
            logging.error('Logstash module not available %s', err)

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
    db.create_all()
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
