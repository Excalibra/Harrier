from flask_restx import Resource, Api, reqparse, fields, Namespace
from app.utils import get_logger, auth
from . import base_query_fields, HarrierResource, get_harrier_parser

ns = Namespace('npoc_service', description="System service (python) information")

logger = get_logger()

base_search_fields = {
    'scheme': fields.String(description="System service name"),
    'host': fields.String(required=False, description="host"),
    'port': fields.String(description="Port number"),
    'target': fields.String(description="Target"),
    "task_id": fields.String(description="Task ID")
}

base_search_fields.update(base_query_fields)


@ns.route('/')
class NpocService(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query service (python) information
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='npoc_service')

        return data
