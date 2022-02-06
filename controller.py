import logging
from models.game import Game
from app import db

logger = logging.getLogger(__name__)
legal_words = []

with open("models/legal_words.txt") as file:
    legal_words = [word.strip() for word in file.readlines()]
    logger.info('populating')


class GameController:
    MAX_GUESSES = 6
    GREEN_SQUARE = '\U0001F7E9'
    YELLOW_SQUARE = '\U0001F7E8'
    BLACK_SQUARE = '\U00002B1B'

    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.game = self.retrieve_game()

    def retrieve_game(self):
        return Game.query.filter_by(chat_id=self.chat_id).first()

    def try_create_game(self, answer, setter_chat_id, setter_username) -> str:
        if self.is_game_ongoing():
            return 'There is an ongoing game already!'
        elif not self.is_answer_legal(answer):
            return 'Please set a valid word! Words must be between 4 to 6 characters and present in the dictionary.'
        elif not self.create_game(answer, setter_chat_id, setter_username):
            return 'Error encountered in the server. Please try again with /start.'
        return f'@{setter_username} has started Wordle with Friends! The word is {len(answer)} characters long. Use /guess to guess. You have 6 tries.'

    def try_guessing(self, word) -> str:
        word = word.lower()
        if not self.is_game_ongoing():
            return 'There is no ongoing game! Start a new one with /start.'
        if not self.is_guess_legal(word):
            return f'"{word}" is invalid! Your guess must be a legal word of {len(self.game.answer)} characters! Use /guess to try again.'
        if not self.add_guess(word):
            return 'Error encountered in the server. Please try again with /guess.'
        return self.display_past_guesses()

    def is_game_ongoing(self) -> bool:
        if not self.game:
            return False
        guesses = self.game.get_guesses()
        return not guesses or (len(guesses) < self.MAX_GUESSES and guesses[-1] != self.game.answer)

    def display_past_guesses(self) -> str:
        if not self.game:
            return 'No games have been played. Start a new one with /start.'
        guesses = self.game.get_guesses()
        if not guesses:
            return 'There have been no guesses so far. Use /guess to guess.'
        row = []
        for i in range(len(guesses)):
            row.append(f"{guesses[i]} ({i+1}/{self.MAX_GUESSES})\n" +
                       self.format_guess_result(guesses[i]))
        history = f"Game started by @{self.game.setter_username}\n" + "\n".join(row)
        if guesses[-1].lower() == self.game.answer:
            history += "\nCongratulations!"
        return history

    def format_guess_result(self, guess: str) -> str:
        answer = self.game.answer
        has_char_in_answer_been_found = [False for _ in guess]
        guess_result = [self.BLACK_SQUARE for _ in guess]

        # Check green squares first
        for i in range(len(guess)):
            if answer[i] == guess[i]:
                guess_result[i] = self.GREEN_SQUARE
                has_char_in_answer_been_found[i] = True

        # Check for orange squres
        for i in range(len(guess)):
            # If it's not in answer or has already been filled, skip
            if guess_result[i] == self.GREEN_SQUARE or guess[i] not in answer:
                continue
            # Search
            for j in range(len(answer)):
                # There is a character in answer corresponding to guess
                if not has_char_in_answer_been_found[j] and guess[i] == answer[j]:
                    has_char_in_answer_been_found[j] = True
                    guess_result[i] = self.YELLOW_SQUARE
                    break
        return ''.join(guess_result)

    def create_game(self, answer, setter_chat_id, setter_username) -> bool:
        try:
            if self.game:
                db.session.delete(self.game)
                db.session.commit()
            game = Game(chat_id=self.chat_id, answer=answer.lower(),
                        setter_chat_id=setter_chat_id, setter_username=setter_username)
            db.session.add(game)
            db.session.commit()
            self.game = game
            return True
        except Exception as e:
            logger.error(e)
            return False

    def add_guess(self, guess) -> bool:
        try:
            self.game.add_guess(guess)
            db.session.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

    def is_guess_legal(self, guess: str) -> bool:
        answer = self.game.answer
        return len(guess) == len(answer) and guess.lower() in legal_words

    @classmethod
    def is_answer_legal(cls, answer: str) -> bool:
        return 4 <= len(answer) <= 6 and answer.lower() in legal_words
