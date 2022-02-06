# wordle-with-friends

## Setup
1. Install pipenv: `pip3 install --user --upgrade pipenv`
1. Install packages: `pipenv --three install`
1. Create database 
    ```
    # psql
    create database wordle;
    ```
  
1. Use flask-migrate to initialise DB
    ```
    # bash
    export FLASK_APP=flaskr
    export FLASK_ENV=development
    flask db init
    ```
1. Copy `.env_example` to `.env`
1. Run `wordle_with_friends_bot.py`

## To create a DB migration
```
flask db migrate -m "Migration message"
flask db upgrade head
```