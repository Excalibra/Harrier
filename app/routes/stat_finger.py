from flask_restx import fields, Namespace
from app.utils import get_logger, auth
from . import base_query_fields, HarrierResource, get_harrier_parser

ns = Namespace('stat_finger', description="Fingerprint statistics")

logger = get_logger()

base_search_fields = {
    'name': fields.String(required=False, description="Fingerprint name"),  # the field name is not well chosen
    "task_id": fields.String(description="Task ID"),
    "cnt": fields.Integer(description="Count"),
}

base_search_fields.update(base_query_fields)


@ns.route('/')
class HarrierStatFingerprint(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query fingerprint statistics
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='stat_finger')

        return data
