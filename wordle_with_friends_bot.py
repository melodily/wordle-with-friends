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
import uuid
from dotenv import load_dotenv
import os
from uuid import uuid4
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, ParseMode, InputTextMessageContent, Update
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, CallbackContext, CallbackQueryHandler, Filters
from telegram.utils import helpers
from controller import GameController

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

START_GAME = 'start-game'


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        f"Let's play Wordle with friends! First set a word")
    # Todo: insert command to set word


def set_word(update: Update, context: CallbackContext) -> None:
    word = context.args[0]
    logger.info(word)
    if GameController.is_answer_legal(word):
        context.bot_data[update.effective_user.id] = word
        bot = context.bot
        url = helpers.create_deep_linked_url(
            bot.username, START_GAME, group=True)
        text = f"Great! Now choose a chat to play with [▶️ CHOOSE]({url})."
        update.message.reply_text(
            text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    else:
        update.message.reply_text(
            "Please set a valid word! Words must be between 4 to 6 characters and present in the dictionary.")


# # TODO: Make callback button
# def choose_group_callback(update: Update, context: CallbackContext) -> None:
#     bot = context.bot
#     url = helpers.create_deep_linked_url(
#         bot.username, START_GAME, group=True)
#     update.callback_query.answer(url=url)


def handle_after_choosing_group(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user = update.effective_user
    answer = context.bot_data[user.id]
    controller = GameController(chat_id)
    update.message.reply_text(controller.try_create_game(
        answer, update.effective_user.id))


def history(update: Update, context: CallbackContext) -> None:
    controller = GameController(update.message.chat_id)
    update.message.reply_text(controller.display_past_guesses())


def guess(update: Update, context: CallbackContext) -> None:
    controller = GameController(update.message.chat_id)
    update.message.reply_text(controller.try_guessing(context.args[0]))


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text(
        "Let's play Wordle with friends! Go to the chat and type @WordleWithFriendsBot to start a game.")


def main() -> None:
    load_dotenv()
    """Start the bot."""
    logger.info("bot started")
    updater = Updater(os.environ.get('TELEGRAM_TOKEN'))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    dispatcher.add_handler(
        CommandHandler("start", handle_after_choosing_group,
                       Filters.regex(START_GAME))
    )
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("history", history))
    dispatcher.add_handler(CommandHandler("play", set_word))
    dispatcher.add_handler(CommandHandler("guess", guess))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
