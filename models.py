from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def is_authenticated(self):
        return True  

    @property
    def is_active(self):
        return True  

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    audio_file = db.Column(db.String(100), nullable=True)
    duration = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Schedule {self.time} - {self.subject}>'
