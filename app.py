from api import api
from database import init_db
from flask import Flask
from flask_cors import CORS
from services import task_runner
from views import bp_automation


def create_app():
    app = Flask(__name__)
    app.secret_key = b'_5#y2L"s8zxec]/'
    app.config.from_object('config')

    # Init all plugins
    CORS(app)
    init_db(app)
    api.init_app(app)

    # Register all views blueprints
    app.register_blueprint(bp_automation)
    return app


if __name__ == "__main__":
    local_app = create_app()
    task_runner.start_scheduler(local_app)
    local_app.run(host='127.0.0.1', port=5001, debug=True)
