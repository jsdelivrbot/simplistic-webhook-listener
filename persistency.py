"""Implement database connection for webhook output."""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class WebhookCall(db.Model):
    """Database stuff for a webhook call, time/repo/success."""

    __tablename__ = 'webhookcall'
    timestamp = db.Column(db.Integer, primary_key=True, unique=True)
    repository = db.Column(db.String(20))
    success = db.Column(db.Boolean)
    results = db.relationship('WebhookCallResult',
                              backref=db.backref('webhookcall'))

    def __init__(self, timestamp, repository, success):
        """Instantiate entity."""
        self.timestamp = timestamp
        self.repository = repository
        self.success = success

    def __repr__(self):
        """String representation of entity."""
        return '<WebhookCall %r>' % self.timestamp

    def __gt__(self, other):
        """Compare functions for timestamp."""
        return True if int(self.timestamp) > int(other.timestamp) else False

    def __lt__(self, other):
        """Compare functions for timestamp."""
        return True if int(self.timestamp) < int(other.timestamp) else False


class WebhookCallResult(db.Model):
    """String Output for Webhook Call."""

    __tablename__ = 'webhookcallresult'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.Integer, db.ForeignKey('webhookcall.timestamp'))
    output = db.Column(db.String(1000))

    def __init__(self, timestamp, output):
        """Instantiate entity."""
        self.timestamp = timestamp
        self.output = output

    def __repr__(self):
        """String representation of entity."""
        return '<WebhookCallResult %r>' % self.id
