import os


class BaseConfig():
    API_PREFIX = '/api'
    TESTING = False
    DEBUG = False


class DevConfig(BaseConfig):
    FLASK_ENV = 'development'


class ProductionConfig(BaseConfig):
    FLASK_ENV = 'production'


class TestConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = "sqlite:///store\\app.db"
    FLASK_ENV = "test"
    # OpenTrons protocol modules
    OT2_MODULES_PATH = r"C:\Development\Charity\LocalWebServer\opentrons_modules"
    # OpenTrons parameters
    OT2_SSH_KEY_FILENAME = "ot2_ssh_key"
    OT2_SSH_KEY_PATH = "C:/Users/inse9/"
    OT2_SSH_KEY = os.path.join(OT2_SSH_KEY_PATH, OT2_SSH_KEY_FILENAME)
    OT2_PROTOCOL_PATH = "/var/lib/jupyter/notebooks"
    OT2_PROTOCOL_FILE = "new_protocol.py"
    OT2_REMOTE_LOG_FILEPATH = "/var/lib/jupyter/notebooks/outputs/completion_log.json"
    OT2_TARGET_IP_ADDRESS = "192.168.1.14"
    OT2_ROBOT_USER = "root"
    OT2_ROBOT_PASSWORD = "opentrons"
