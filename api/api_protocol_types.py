from database import session
from flask import jsonify
from flask_restful import Resource
from flask_restful import reqparse
from models.protocols import ProtocolType


# Define endpoint methods
# noinspection PyMethodMayBeStatic
class ProtocolTypeAPI(Resource):

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help='name of the new protocol type', required=True)
        parser.add_argument('created_by', type=str, help='ID of the user creating the protocol', required=True)
        parser.add_argument('filename', type=str, help='name of the python file to be used', required=True)
        parser.add_argument('module_name', type=str, help='name of the module within python file to be used',
                            required=True)
        parser.add_argument('checksum', type=str, help='checksum of the python file', required=True)
        args = parser.parse_args()
        try:
            new_protocol_type = ProtocolType(
                created_by=args["created_by"],
                name=args["name"],
                filename=args["filename"],
                module_name=args["module_name"],
                checksum=args["checksum"]
            )
            session.add(new_protocol_type)
            session.commit()
            res = {
                "id": new_protocol_type.id,
                "name": new_protocol_type.name,
                "checksum": new_protocol_type.checksum
            }
            return res, 201
        except Exception as e:
            res = {
                "status": "failed",
                "name": args['process_uuid'],
                "message": str(e)
            }
            return jsonify(res), 500

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help='name of the new protocol type', required=False)
        parser.add_argument('created_by', type=str, help='ID of the user creating the protocol', required=False)
        parser.add_argument('filename', type=str, help='name of the python file to be used', required=False)
        parser.add_argument('module_name', type=str, help='name of the module within python file to be used',
                            required=False)
        parser.add_argument('checksum', type=str, help='checksum of the python file', required=False)
        args = parser.parse_args()
        empty_keys = list()
        for key, value in args.items():
            print(key)
            if not value:
                empty_keys.append(key)
        for k in empty_keys:
            args.pop(k)
        protocol_types_list = list()
        if len(args.keys()):
            protocol_types = ProtocolType.query.filter_by(**args).all()
            for p in protocol_types:
                protocol_types_list.append(p.serialize())
        else:
            protocol_types = ProtocolType.query.all()
            for p in protocol_types:
                protocol_types_list.append(p.serialize())
        return protocol_types_list, 200
