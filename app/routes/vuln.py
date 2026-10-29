from bson import ObjectId
from flask_restx import Resource, Api, reqparse, fields, Namespace
from app.utils import get_logger, auth
from . import base_query_fields, HarrierResource, get_harrier_parser
from app import utils
from app.modules import ErrorMsg

ns = Namespace('vuln', description="Vulnerability information")

logger = get_logger()

base_search_fields = {
    'plg_name': fields.String(required=False, description="plugin ID"),
    'plg_type': fields.String(description="Type"),
    'vul_name': fields.String(description="Vulnerability name"),
    'app_name': fields.String(description="Application name"),
    'target': fields.String(description="Target"),
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
        Query vulnerability information
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='vuln')

        return data


delete_vuln_fields = ns.model('deleteVulnFields',  {
    '_id': fields.List(fields.String(required=True, description="Risk information _id"))
})


@ns.route('/delete/')
class DeleteHarrierVuln(HarrierResource):
    @auth
    @ns.expect(delete_vuln_fields)
    def post(self):
        """
        Delete risk information
        """
        args = self.parse_args(delete_vuln_fields)
        id_list = args.pop('_id', [])
        for _id in id_list:
            query = {'_id': ObjectId(_id)}
            utils.conn_db('vuln').delete_one(query)

        return utils.build_ret(ErrorMsg.Success, {'_id': id_list})

