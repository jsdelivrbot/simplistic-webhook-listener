"""Start script for Hooker."""
import logging
import os
import time

from datetime import datetime
from flask import Flask, render_template, request,\
    send_from_directory as send_file
from flask_bootstrap import Bootstrap
from flask_iniconfig import INIConfig
from hooker import Hooker
from persistency import db, WebhookCall, WebhookCallResult


def configure_logging():
    """Configure debug logging based on app config."""
    global debug
    try:
        debug = app.config['DEBUG']
        if debug:
            logging.basicConfig(format='%(message)s', level=logging.DEBUG)
        else:
            logging.basicConfig(format='%(message)s', level=logging.INFO)
    except KeyError as err:
        debug = False

    try:
        logstash_config = app.config['LOGSTASH']
        logger = logging.getLogger()
        import logstash
        host, ls_port = logstash_config.split(':')
        logger.addHandler(logstash.TCPLogstashHandler(host=host,
                                                      port=int(ls_port),
                                                      version=1))
    except ImportError as err:
        logstash = None
        logging.error('python-logstash module not available %s', err)
    except KeyError as err:
        pass


app = Flask(__name__)
INIConfig(app)
app.config.from_inifile_sections('/etc/hooker_config.ini', section_list=['default'])
app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', True)
configure_logging()
hook_executor = Hooker(app.config)
Bootstrap(app)
db.init_app(app)
with app.app_context():
    db.create_all()


@app.route('/', methods=['POST'])
@app.route('/<hooking_repository>/', methods=['POST'])
def post_hook(hooking_repository=None):
    """Post request behaviour."""
    if not hook_executor.authenticate(request):
        return 'Access forbidden', 403

    if hooking_repository:
        if len(hooking_repository) < 20:
            repository = hooking_repository
        else:
            repository = hooking_repository[0:20]
    else:
        repository = 'unknown'

    if hook_executor.assess_reload(request):
        current_time = int(time.time())
        output = hook_executor.execute_command()
        success = False if output.startswith('Error') else True
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
            return response, 201
        else:
            return response, 500
    else:
        return 'OK', 200


@app.route('/', methods=['GET'])
@app.route('/logs/', methods=['GET'])
def get_logs():
    """GET request behaviour on log list."""
    return render_template('logs.html', content=WebhookCall.query.all())


@app.route('/<log_id>/', methods=['GET'])
@app.route('/logs/<log_id>', methods=['GET'])
def get_log(log_id):
    """GET request behaviour for one log."""
    logs = WebhookCallResult.query.filter(
        WebhookCallResult.timestamp == log_id).all()
    if logs:
        return render_template('log.html', timestamp=log_id, logs=logs)
    else:
        return '', 404


@app.route('/favicon.ico')
def favicon():
    """Favicon due to lots of 404 requests."""
    return send_file(os.path.join(app.root_path, 'static'), 'favicon.ico')


@app.template_filter('datetime')
def format_datetime(value):
    """Datetime formatter."""
    return datetime.fromtimestamp(int(value))\
        .strftime("%Y-%m-%d_%H-%M-%S")


if __name__ == '__main__':
    try:
        port = int(app.config['PORT'])
    except KeyError as err:
        port = 7010
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
