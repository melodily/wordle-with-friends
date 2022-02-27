#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
from dotenv import load_dotenv
import os
from telegram import ParseMode, Update
from telegram.ext import Updater, CommandHandler, CallbackContext, Filters, ConversationHandler, MessageHandler
from telegram.utils import helpers
from controller import GameController
from enum import IntEnum
from app import db

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

START_GAME_DEEP_LINK = 'start-game'
SET_WORD_DEEP_LINK = 'set-word'
MESSAGE_FOR_INVALID_COMMANDS_IN_PRIVATE_CHAT = "It's called Wordle with Friends! Use /start to start a game with your friends."

class ConversationStates(IntEnum):
    SET_WORD = 1


def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    if update.effective_chat.type == 'private':
        update.message.reply_text(
            f"Let's play Wordle with friends! First type your chosen word (4-6 letters) into the message box and press enter.")
        return ConversationStates.SET_WORD
    else:
        controller = GameController(update.effective_chat.id)
        if controller.is_game_ongoing():
            update.message.reply_text(
                f"{controller.game.setter_username} has started a game. Use /guess to guess the word!")
        else:
            # Redirect to bot if in group chat and no ongoing game
            url = helpers.create_deep_linked_url(context.bot.username, SET_WORD_DEEP_LINK)
            text = f"Let's play Wordle with Friends! Go here to set your word: \n[▶️ <a href='{url}'>Set word</a>]."
            update.message.reply_text(
                text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


def set_word(update: Update, context: CallbackContext):
    word = update.message.text.split(' ')[0] if update.message.text else ''
    if GameController.is_answer_legal(word):
        context.bot_data[update.effective_user.id] = word
        url = helpers.create_deep_linked_url(
            context.bot.username, START_GAME_DEEP_LINK, group=True)
        text = (f"Great, {word.upper()} is the answer! Now choose a chat to play with: \n[▶️ <a href='{url}'>Choose chat</a>].\n" 
        "Please make sure you have admin rights to the group, as this bot cannot be added otherwise.")
        update.message.reply_text(
            text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        return ConversationHandler.END
    else:
        update.message.reply_text(
            "Please set a valid word! \nWords must be between 4 to 6 letters and present in the dictionary. \nUse /cancel to exit.")


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Ok! Start a new game with /start")
    return ConversationHandler.END


def handle_after_choosing_group(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user = update.effective_user
    answer = context.bot_data.get(user.id)
    controller = GameController(chat_id)
    if answer:
        update.message.reply_text(controller.try_create_game(
            answer, update.effective_user.id, update.effective_user.first_name)
        )
    else:
        url = helpers.create_deep_linked_url(context.bot.username, SET_WORD_DEEP_LINK)
        update.message.reply_text(f"Sorry, we lost your answer. Try creating a new one here: \n[▶️ <a href='{url}'>Set word</a>]",
        parse_mode=ParseMode.HTML, disable_web_page_preview=True)


def history(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.type == 'private':
        update.message.reply_text(MESSAGE_FOR_INVALID_COMMANDS_IN_PRIVATE_CHAT)
        return
    controller = GameController(update.message.chat_id)
    update.message.reply_text(controller.display_past_guesses(), parse_mode=ParseMode.HTML)


def guess(update: Update, context: CallbackContext) -> None:
    if not update.message:
        return
    try:
        if update.effective_chat.type == 'private':
            update.message.reply_text(MESSAGE_FOR_INVALID_COMMANDS_IN_PRIVATE_CHAT)
            return
        # TODO: save history of games
        controller = GameController(update.message.chat_id)
        if not context.args:
            update.message.reply_text('Please type a word after /guess.')
            return
        update.message.reply_text(
            controller.try_guessing(context.args[0], update.effective_user.first_name), 
            parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(e)
        logger.error(update)


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text(
        '\n'.join([
            "This follows the rules of Wordle. Guess the word set by your friend." +
            "A green box shows a correct letter in the correct position," + 
            "a yellow box shows a correct letter in the wrong position, and a black box shows a wrong letter.",
            "/start to start a game",
            "/guess [word] to guess the word",
            "/history to see past guesses",
            "",
            "Please email wordlewithfriendsbot@gmail.com for bug reports and suggestions."
        ])
    )


def main() -> None:
    """Start the bot."""
    logger.info("bot started")
    if os.environ.get('ENV') != 'prod':
        load_dotenv()
    updater = Updater(os.environ.get('TELEGRAM_TOKEN'))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    # This handles the deep link after user has chosen a group to play with
    dispatcher.add_handler(
        CommandHandler("start", handle_after_choosing_group,
                       Filters.regex(START_GAME_DEEP_LINK))
    )

    dispatcher.add_handler(CommandHandler("history", history))
    dispatcher.add_handler(CommandHandler("guess", guess))
    dispatcher.add_handler(CommandHandler("help", help_command))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ConversationStates.SET_WORD: [MessageHandler(
                Filters.text & ~Filters.command, callback=set_word)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conv_handler)
    # Start the Bot        
    if os.environ.get('ENV') == 'prod':
        updater.start_webhook(listen=f'0.0.0.0',
                        port=443,
                        url_path=os.environ.get('TELEGRAM_TOKEN', ''),
                        webhook_url=f'https://{os.environ.get("HOSTNAME", "")}:443/{os.environ.get("TELEGRAM_TOKEN", "")}')
    else:
        updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
