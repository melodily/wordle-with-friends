#!/usr/bin/env bash
flask db upgrade head
python wordle_with_friends_bot.py