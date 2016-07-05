# webhook listener for HTTP POST requests from repositories or CI servers.

## Configure

The webhook listener expects a configuration file at /etc/hooker_config.ini.
There you need at least the following content:
```
[default]
DEBUG=false
SQLALCHEMY_DATABASE_URI=sqlite:///logs.db
COMMAND=<the command that should be executed>
HOOKER=gitlab (travis and github are also supported)
SECRET_KEY=(some random secret used by flask)
```
Additional fields are:
```
TOKENS=(; delimited list of access tokens)
LOGSTASH=<HOST:PORT>
```

## Execution

You can directly execute run.py or use run.wsgi for Apache mod_wsgi.
