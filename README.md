# Wordle with Friends Bot
This is a Telegram bot for you to set a 4-6 letter word for your groups to guess.

## Usage
### Setup
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

### Run
1. `docker-compose up`

### Create a DB migration
```
flask db migrate -m "Migration message"
```
### [Optional] Use pipenv for package management
1. Install pipenv: `pip3 install --user --upgrade pipenv`
1. Install packages: `pipenv --three install`

Currently the Dockerfile uses `requirements.txt` to speed up deployment, so `pipenv lock -r > requirements.txt` is necessary when you install pacakges.

## Maintainers
@melodily

## Contribute
PRs accepted

## Licence
MIT © 2022 Melody Lee

## Credits
Josh Wardle for creating Wordle