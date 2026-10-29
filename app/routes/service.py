from flask_restx import Resource, Api, reqparse, fields, Namespace
from app.utils import get_logger, auth
from . import base_query_fields, HarrierResource, get_harrier_parser

ns = Namespace('service', description="System service information")

logger = get_logger()

base_search_fields = {
    'service_name': fields.String(description="System service name"),
    'service_info.ip': fields.String(required=False, description="IP"),
    'service_info.port_id': fields.Integer(description="Port number"),
    'service_info.version': fields.String(description="System service version"),
    'service_info.product': fields.String(description="Product"),
    "task_id": fields.String(description="Task ID")
}

base_search_fields.update(base_query_fields)


@ns.route('/')
class HarrierService(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query service information
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='service')

        return data
