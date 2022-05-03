from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api
from sqlalchemy.engine.url import URL
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_apispec.extension import FlaskApiSpec
from threading import Thread
from engine.engine import Engine

from db.db import DB

# Load environment variables and config
from dotenv import load_dotenv
load_dotenv()

from config import config  # pylint: disable=wrong-import-position

# Manage DB connection
db_uri = URL(**config.DB_CONFIG)

# Init Flask and set config
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["ERROR_404_HELP"] = False

app.config["JWT_TOKEN_LOCATION"] = ['headers', 'cookies']
app.config["JWT_COOKIE_SECURE"] = config.ENVIRONMENT != "dev"
app.config['JWT_COOKIE_CSRF_PROTECT'] = False

app.config['CORS_HEADERS'] = 'Content-Type'
app.config["CORS_SUPPORTS_CREDENTIALS"] = True
app.config["CORS_ORIGINS"] = config.CORS_ORIGINS if config.CORS_ORIGINS else []

app.config['PROPAGATE_EXCEPTIONS'] = config.ENVIRONMENT == "dev"

app.config['SCHEDULER_API_ENABLED'] = False

app.config['APISPEC_SWAGGER_URL'] = '/doc/json'
app.config['APISPEC_SWAGGER_UI_URL'] = '/doc/'
app.config['APISPEC_SPEC'] = APISpec(
    title='CYBERLUX CRON ENGINE',
    version='v0.1',
    plugins=[MarshmallowPlugin()],
    openapi_version='2.0.0'
)

# Create DB instance
db = DB(app)

# Add additional plugins
cors = CORS(app)
jwt = JWTManager(app)
docs = FlaskApiSpec(app)

# Init and set the resources for Flask
api = Api(app)

# Init cron manager
engine = Engine(db)
cron_manager = Thread(target=engine.run)
cron_manager.start()


@app.route('/<generic>')
def undefined_route(_):
    return '', 404


if __name__ in ('app', '__main__'):
    from routes import set_routes
    set_routes({"api": api, "db": db, "docs": docs, "engine": engine})

    app.debug = config.ENVIRONMENT == "dev"

    if __name__ == "__main__":
        app.run(port=config.PORT)
