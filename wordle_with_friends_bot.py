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
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, ParseMode, InputTextMessageContent, ReplyKeyboardMarkup, Update
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, CallbackContext, CallbackQueryHandler, Filters, ConversationHandler, MessageHandler
from telegram.utils import helpers
from controller import GameController
from enum import IntEnum
from typing import Optional

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

START_GAME_DEEP_LINK = 'start-game'
MESSAGE_FOR_INVALID_COMMANDS_IN_PRIVATE_CHAT = "It's Wordle not Solitaire! Use /start to start a game with your friends."


class ConversationStates(IntEnum):
    SET_WORD = 1


def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    if update.effective_chat.type == 'private':
        update.message.reply_text(
            f"Let's play Wordle with friends! First type your chosen word (4-6 characters) into the message box and press enter.")
        return ConversationStates.SET_WORD
    else:
        controller = GameController(update.effective_chat.id)
        if controller.is_game_ongoing():
            # TODO: insert setter username
            update.message.reply_text(
                f"There is an ongoing game. Use /guess to guess the word!")
        else:
            # Redirect to bot if in group chat and no ongoing game
            url = helpers.create_deep_linked_url(context.bot.username)
            text = f"Let's play Wordle with Friends! Go here to set your word: \n[▶️ Set word]({url})."
            update.message.reply_text(
                text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


def set_word(update: Update, context: CallbackContext):
    word = update.message.text.split(' ')[0] if update.message.text else ''
    if GameController.is_answer_legal(word):
        context.bot_data[update.effective_user.id] = word
        url = helpers.create_deep_linked_url(
            context.bot.username, START_GAME_DEEP_LINK, group=True)
        text = f"Great, {word.upper()} is the answer! Now choose a chat to play with: \n[▶️ Choose chat]({url})."
        update.message.reply_text(
            text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        return ConversationHandler.END
    else:
        update.message.reply_text(
            "Please set a valid word! Words must be between 4 to 6 characters and present in the dictionary. Use /cancel to exit.")


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Ok! Start a new game with /start")
    return ConversationHandler.END


def handle_after_choosing_group(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user = update.effective_user
    answer = context.bot_data[user.id]
    controller = GameController(chat_id)
    update.message.reply_text(controller.try_create_game(
        answer, update.effective_user.id, update.effective_user.username)
    )


def history(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.type == 'private':
        update.message.reply_text(MESSAGE_FOR_INVALID_COMMANDS_IN_PRIVATE_CHAT)
        return
    controller = GameController(update.message.chat_id)
    update.message.reply_text(controller.display_past_guesses())


def guess(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.type == 'private':
        update.message.reply_text(MESSAGE_FOR_INVALID_COMMANDS_IN_PRIVATE_CHAT)
        return
    # TODO: save user id of guess
    # TODO: save history of games
    controller = GameController(update.message.chat_id)
    update.message.reply_text(controller.try_guessing(context.args[0]))


def help_command(update: Update, context: CallbackContext) -> None:
    # TODO: Put commands in inline buttons
    """Send a message when the command /help is issued."""
    update.message.reply_text(
        '\n'.join([
            "/start to start a game",
            "/guess to guess the word",
            "/history to see past guesses"
        ])
    )


def main() -> None:
    load_dotenv()
    """Start the bot."""
    logger.info("bot started")
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
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
