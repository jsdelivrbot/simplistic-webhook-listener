

from run import app as application

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8082, debug=True, use_reloader=False)
