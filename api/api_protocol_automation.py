from database import session
from flask import jsonify
from flask_restful import Resource
from flask_restful import reqparse
from models.protocols import Protocol
from sqlalchemy import or_


# Define endpoint methods
# noinspection PyMethodMayBeStatic
class AutomationAPI(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('process_uuid', type=str, help='process uuid to search for', required=False)
        args = parser.parse_args()
        process_uuid = args['process_uuid']
        runs_list = list()
        if process_uuid:
            runs = Protocol.query.filter_by(process_uuid=args['process_uuid']).all()
            for s in runs:
                runs_list.append(s.serialize())
        else:
            runs = Protocol.query.filter_by().all()
            for s in runs:
                runs_list.append(s.serialize())
        return runs_list, 200

    # def post(self):
    #     parser = reqparse.RequestParser()
    #     parser.add_argument('process_uuid', type=str, help='process uuid', required=True)
    #     parser.add_argument('protocol_id', type=int, help='the ID of the specific protocol used', required=True)
    #     parser.add_argument('supervisor_id', type=str, help='personal ID of the supervisor', required=False)
    #     parser.add_argument('operator_id', type=str, help='personal ID of the operator', required=False)
    #     parser.add_argument('container_in', type=str, help='barcode of the input container', required=True)
    #     parser.add_argument('container_out', type=str, help='barcode of the output container', required=True)
    #     args = parser.parse_args()
    #     try:
    #         queued_protocols = Protocol.query.filter_by(status='queued').all()
    #         running_protocols = Protocol.query.filter_by(status='running').all()
    #         if not (queued_protocols or running_protocols):
    #             protocol = Protocol(
    #                 process_uuid=args['process_uuid'],
    #                 protocol_id=args['protocol_id'],
    #                 container_in=args['container_in'],
    #                 container_out=args['container_out'],
    #                 operator_id=args['operator_id'],
    #                 supervisor_id=args['supervisor_id']
    #             )
    #             session.add(protocol)
    #             session.commit()
    #             res = {"status": protocol.status, "id": protocol.id, "process_uuid": protocol.process_uuid}
    #             return res, 201
    #         else:
    #             res = {"status": "failed", "process_uuid": args['process_uuid'],
    #                    "message": "There's a task already queued or in progress. Please try again later"}
    #             return res, 403
    #     except Exception as e:
    #         res = {"status": "failed", "process_uuid": args['process_uuid'], "message": str(e)}
    #         return res, 500


class AutomationAPI_MVP(Resource):

    def get(self, station, action):
        try:
            queued_protocols = Protocol.query.filter_by(status='queued').all()
            running_protocols = Protocol.query.filter_by(status='running').all()
            if not (queued_protocols or running_protocols):
                protocol = Protocol(
                    station=station,
                    action=action
                )
                session.add(protocol)
                session.commit()
                res = {"status": protocol.status, "id": protocol.id}
                return res, 201
            else:
                res = {"status": "failed",
                       "message": "There's a task already queued or in progress. Please try again later"}
                return res, 403
        except Exception as e:
            res = {"status": "failed", "message": str(e)}
            return res, 500

class CheckFunction(Resource):

    def get(self):
        queued_protocols = Protocol.query.filter_by(status='queued').all()
        running_protocols = Protocol.query.filter_by(status='running').all()
        if not(queued_protocols or running_protocols):
            return {"status": True, "res": ":)"}, 200
        else:
            return {"status": False, "res": ":("}, 200
