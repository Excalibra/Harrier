from flask_restx import Resource, Api, reqparse, fields, Namespace
from app.utils import get_logger, auth
from . import base_query_fields, HarrierResource, get_harrier_parser

ns = Namespace('url', description="URL information")

logger = get_logger()

base_search_fields = {
    'fld': fields.String(required=False, description="IP"),
    'site': fields.String(description="Domain"),
    'url': fields.String(required=False, description="URL"),
    'content_length': fields.Integer(description="Body length"),
    'status_code': fields.Integer(description="Status code"),
    'title': fields.String(description="Title"),
    'source': fields.String(description="Source"),
    "task_id": fields.String(description="Task ID")
}

base_search_fields.update(base_query_fields)


@ns.route('/')
class HarrierUrl(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query URL information
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='url')

        return data


@ns.route('/export/')
class HarrierUrlExport(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Export URLs
        """
        args = self.parser.parse_args()
        response = self.send_export_file(args=args, _type="url")

        return response
