from flask_restful import Api
from .api_protocol_automation import AutomationAPI, AutomationAPI_MVP
import config


api = Api(prefix=config.API_PREFIX)

api.add_resource(AutomationAPI, '/automation')
api.add_resource(AutomationAPI_MVP, '/automation/<int:station>/<string:action>')
# api.add_resource(ProtocolTypeAPI, '/protocol_types')
