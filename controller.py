import logging
from models.game import Game
from app import db

logger = logging.getLogger(__name__)
legal_words = []

with open("models/legal_words.txt") as file:
    legal_words = {word.strip() for word in file.readlines()}
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
        try:
            return Game.query.filter_by(chat_id=self.chat_id).first()
        except Exception as e:
            logger.error(e)
            db.session.rollback()
            return None

    def try_create_game(self, answer, setter_chat_id, setter_username) -> str:
        if self.is_game_ongoing():
            return 'There is an ongoing game already!'
        elif not self.is_answer_legal(answer):
            return 'Please set a valid word! Words must be between 4 to 6 letters and present in the dictionary.'
        elif not self.create_game(answer, setter_chat_id, setter_username):
            return 'Error encountered in the server. Please try again with /start.'
        return f'{setter_username} has started Wordle with Friends! \nThe word is {len(answer)} letters long. \nUse /guess [word] to guess. \nYou have 6 tries.'

    def try_guessing(self, word, guesser_username) -> str:
        word = word.lower()
        if not self.is_game_ongoing():
            return 'There is no ongoing game! Start a new one with /start.'
        if not self.is_guess_legal(word):
            return f'"{word}" is invalid! Your guess must be a legal word of {len(self.game.answer)} letters! Use /guess to try again.'
        if not self.add_guess(word, guesser_username):
            return 'Error encountered in the server. Please try again with /guess.'
        return self.display_past_guesses()

    def is_game_ongoing(self) -> bool:
        if not self.game:
            return False
        guesses = self.game.get_guesses()
        return not guesses or (len(guesses) < self.MAX_GUESSES and guesses[-1]['guess'] != self.game.answer)

    def display_past_guesses(self) -> str:
        if not self.game:
            return 'No games have been played. Start a new one with /start.'
        guesses = self.game.get_guesses()
        if not guesses:
            return 'There have been no guesses so far. Use /guess to guess.'
        row = []
        for i in range(len(guesses)):
            row.append(f"""<code>{'  '.join([c for c in guesses[i]['guess'].upper()])}</code>""")
            row.append(self.format_guess_result(guesses[i]['guess']))
            row.append(f"({guesses[i]['by']}: {i+1}/{self.MAX_GUESSES})")
        history = f"Game started by {self.game.setter_username}\n" + "\n".join(row)
        if guesses[-1]['guess'].lower() == self.game.answer:
            history += "\nCongratulations! Use /start to play again! #wordlewithfriends"
        elif len(guesses) == self.MAX_GUESSES:
            history += f"\nBetter luck next time! The answer was {self.game.answer.upper()}. Use /start to start another game! #wordlewithfriends"
        else:
            history += f"\n{self.format_keyboard()}"
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
        return ' '.join(guess_result)
    
    def format_keyboard(self):
        if not self.game or not self.game.get_guesses():
            return ''
        guesses = self.game.get_guesses()
        answer = self.game.answer
        # 0 for wrong letter, 1 for wrong position, 2 for right position
        output_dict = {}
        for guess in guesses:
            word = guess['guess']
            for i in range(len(word)):
                c = word[i]
                if c == answer[i]:
                    output_dict[c] = 2
                elif c in answer:
                    output_dict[c] = 2 if output_dict.get(c) == 2 else 1
                else:
                    output_dict[c] = 0

        keyboard_rows = ['qwertyuiop', 'asdfghjkl', 'zxcvbnm']
        output = []
        for row in keyboard_rows:
            output_row = []
            for c in row:
                if c in output_dict:
                    if output_dict[c] == 2:
                        result = f"<u><b>{c}</b></u>"
                    elif output_dict[c] == 1:
                        result = f"<u><i>{c}</i></u>"
                    else:
                        result = "  "
                else:
                    result = c
                output_row.append(result)
            output.append('  '.join(output_row))
        return '\n'.join(output).upper()


    def create_game(self, answer: str, setter_chat_id: str, setter_username: str) -> bool:
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
            db.session.rollback()
            return False

    def add_guess(self, guess: str, guesser_username: str) -> bool:
        try:
            self.game.add_guess(guess, guesser_username)
            db.session.commit()
            return True
        except Exception as e:
            logger.error(e)
            db.session.rollback()
            return False

    def is_guess_legal(self, guess: str) -> bool:
        answer = self.game.answer
        return type(guess) == str and len(guess) == len(answer) and guess.lower() in legal_words

    @classmethod
    def is_answer_legal(cls, answer: str) -> bool:
        return type(answer) == str and 4 <= len(answer) <= 6 and answer.lower() in legal_words
