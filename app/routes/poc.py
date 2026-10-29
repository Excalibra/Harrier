from bson import ObjectId
from flask_restx import Resource, Api, reqparse, fields, Namespace
from app.utils import get_logger, auth
from . import base_query_fields, HarrierResource, get_harrier_parser
from app.services.npoc import NPoC
from app import utils, celerytask
from app.modules import ErrorMsg, TaskStatus, CeleryAction
import copy

ns = Namespace('poc', description="PoC information")

logger = get_logger()

base_search_fields = {
    'plugin_name': fields.String(description="PoC name ID"),
    'app_name': fields.String(description="Application name"),
    'scheme': fields.String(description="Supported protocols"),
    'vul_name': fields.String(description="Vulnerability name"),
    'plugin_type': fields.String(description="Plugin type", enum=['poc', 'brute']),
    'update_date': fields.String(description="Update time"),
    'category': fields.String(description="PoC category")
}

base_search_fields.update(base_query_fields)


@ns.route('/')
class HarrierPoC(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query PoC information
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args,  collection='poc')

        return data


@ns.route('/sync/')
class HarrierPoCSync(HarrierResource):

    @auth
    def get(self):
        """
        Update PoC information
        """
        n = NPoC()
        plugin_cnt = len(n.plugin_name_list)
        n.sync_to_db()
        n.delete_db()

        return utils.build_ret(ErrorMsg.Success, {"plugin_cnt": plugin_cnt})


@ns.route('/delete/')
class HarrierPoCDelete(HarrierResource):

    @auth
    def get(self):
        """
        Clear PoC information
        """
        result = utils.conn_db('poc').delete_many({})

        delete_cnt = result.deleted_count

        return utils.build_ret(ErrorMsg.Success, {"delete_cnt": delete_cnt})


