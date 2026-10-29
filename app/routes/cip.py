from flask_restx import Resource, Api, reqparse, fields, Namespace
from app.utils import get_logger, auth
from . import base_query_fields, HarrierResource, get_harrier_parser

ns = Namespace('cip', description="C-class segment IP statistics")

logger = get_logger()

base_search_fields = {
    'cidr_ip': fields.String(required=False, description="C-class segment"),
    "task_id": fields.String(description="Task ID"),
    "ip_count": fields.Integer(description="IP count"),
    "domain_count": fields.Integer(description="Number of domains resolving to this C-class segment")
}

base_search_fields.update(base_query_fields)


@ns.route('/')
class HarrierCIPList(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query C-class segment statistics
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='cip')

        return data


@ns.route('/export/')
class HarrierCIPExport(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Export C-class segment IPs
        """
        args = self.parser.parse_args()
        response = self.send_export_file(args=args, _type="cip")

        return response
