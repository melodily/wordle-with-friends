import os


class Config:
    DEBUG = False
    DEVELOPMENT = False
    # SECRET_KEY = os.getenv("SECRET_KEY")
    CSRF_ENABLED = True
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']


class ProductionConfig(Config):
    pass


class StagingConfig(Config):
    DEBUG = True


class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True
