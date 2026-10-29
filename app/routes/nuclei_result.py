from bson import ObjectId
from flask_restx import Resource, Api, reqparse, fields, Namespace
from app.utils import get_logger, auth
from . import base_query_fields, HarrierResource, get_harrier_parser
from app import utils
from app.modules import ErrorMsg

ns = Namespace('nuclei_result', description="nuclei scan results")

logger = get_logger()

base_search_fields = {
    'template_url': fields.String(required=False, description="Template file URL"),
    'template_id': fields.String(description="Template id"),
    'vuln_name': fields.String(description="Vulnerability name"),
    'vuln_severity': fields.String(description="Vulnerability severity"),
    'vuln_url': fields.String(description="Vulnerability URL"),
    'curl_command': fields.String(description="curl command"),
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
        Query nuclei scan results
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='nuclei_result')

        return data


delete_nuclei_result_fields = ns.model('deleteNucleiResultFields',  {
    '_id': fields.List(fields.String(required=True, description="nuclei scan result _id"))
})


@ns.route('/delete/')
class DeleteNucleiResult(HarrierResource):
    @auth
    @ns.expect(delete_nuclei_result_fields)
    def post(self):
        """
        Delete nuclei scan results
        """
        args = self.parse_args(delete_nuclei_result_fields)
        id_list = args.pop('_id', [])
        for _id in id_list:
            query = {'_id': ObjectId(_id)}
            utils.conn_db('nuclei_result').delete_one(query)

        return utils.build_ret(ErrorMsg.Success, {'_id': id_list})

