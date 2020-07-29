from flask_restful import Api
from .api_protocol_automation import AutomationAPI
from .api_protocol_types import ProtocolTypeAPI
import config


api = Api(prefix=config.API_PREFIX)

api.add_resource(AutomationAPI, '/automation')
api.add_resource(ProtocolTypeAPI, '/protocol_types')
