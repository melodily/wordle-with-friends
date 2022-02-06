from sqlalchemy.dialects.postgresql import JSON
from app import db


class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    setter_chat_id = db.Column(db.Integer, nullable=False)
    setter_username = db.Column(db.String(), nullable=False)
    chat_id = db.Column(db.Integer, nullable=False, unique=True)
    answer = db.Column(db.String(), nullable=False)
    guesses = db.Column(JSON)

    def __repr__(self):
        return '<id {}>'.format(self.id)

    def get_guesses(self):
        return self.guesses.get('guesses', []) if self.guesses else []

    def add_guess(self, guess: str):
        self.guesses = {
            'guesses': self.get_guesses() + [guess]
        }
