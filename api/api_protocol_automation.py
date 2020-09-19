from database import session
from flask import jsonify
from flask_restful import Resource
from flask_restful import reqparse
from models.protocols import Protocol
from sqlalchemy import or_, desc
import glob
import os
from shutil import copy2
import json
from services.task_runner import create_ssh_client
from scp import SCPClient
from services.task_runner import OT2_TARGET_IP_ADDRESS, OT2_SSH_KEY, OT2_ROBOT_PASSWORD, OT2_REMOTE_LOG_FILEPATH

PCR_result_file_scheme = '????????_Data_??-??-????_??-??-??_Result.json'
PCR_results_path = 'C:/PCR_BioRad/json_results/'


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
        if not (queued_protocols or running_protocols):
            # FIXME: Check this
            last_protocol = Protocol.query.order_by(Protocol.creation_date.desc()).first()
            last_status = last_protocol.status
            print(last_status)
            if last_status == "failed":
                # last_protocol.set_running()
                session.remove()
                # session.add(last_protocol)
                session.commit()
                return "There has been an error in execution, please verify and try again", 400
            else:
                # Searching all PCR results file
                PCR_result_file = glob.glob(PCR_results_path + PCR_result_file_scheme)
                # Sorting the PCR's results
                PCR_result_file.sort(key=os.path.getctime)
                # Check if the results are available
                if not PCR_result_file:
                    print('there are no results available')
                    return {"status": True, "res": ":)"}, 200
                else:
                    # Opening the the last created and encoded with utf-8-sig
                    with open(str(PCR_result_file[-1]), 'r', encoding='utf-8-sig') as result:
                        read = json.load(result)
                    # Make the backup of the PCR results
                    copy2(PCR_result_file[-1], './')
                    # Delete the last file in order to don't create confusion
                    os.remove(PCR_result_file[-1])
                    return {"status": True, "res": read}, 200
                # return {"status": True, "res": ":)"}, 200
        else:
            client = create_ssh_client(usr='root', key_file=OT2_SSH_KEY, pwd=OT2_ROBOT_PASSWORD)
            scp_client = SCPClient(client.get_transport())
            logging_file = 'completion_log'
            scp_client.get(remote_path=OT2_REMOTE_LOG_FILEPATH, local_path=logging_file)
            scp_client.close()
            with open('./' + logging_file, 'r') as r:
                status = json.load(r)

            return {"status": False, "res": status["stages"][-1]["stage_name"]}, 200
