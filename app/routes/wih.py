from flask_restx import fields, Namespace
from app.utils import get_logger, auth
from . import base_query_fields, HarrierResource, get_harrier_parser
from bson import ObjectId
from app.modules import ErrorMsg
from app import utils

ns = Namespace('wih', description="WEB Info Hunter information")

logger = get_logger()

base_search_fields = {
    'record_type': fields.String(required=False, description="Record type"),
    'record_type__neq': fields.String(required=False, description="Record type not equal (full match)"),
    'record_type__not': fields.String(required=False, description="Record type does not contain"),
    'content': fields.String(description="Content"),
    'source': fields.String(description="Source JS URL"),
    'site': fields.String(description="Site URL"),
    'task_id': fields.String(description="Task ID"),
}


base_search_fields.update(base_query_fields)


@ns.route('/')
class HarrierWebInfoHunter(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query WEB Info Hunter information
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='wih')

        return data


@ns.route('/export/')
class HarrierWihExport(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Export WIH
        """
        args = self.parser.parse_args()
        response = self.send_export_file(args=args, _type="wih")

        return response


delete_wih_fields = ns.model('deleteWih',  {
    '_id': fields.List(fields.String(required=True, description="Data _id"))
})


@ns.route('/delete/')
class DeleteHarrierWIH(HarrierResource):
    @auth
    @ns.expect(delete_wih_fields)
    def post(self):
        """
        Delete WIH data from a task
        """
        args = self.parse_args(delete_wih_fields)
        id_list = args.pop('_id', "")
        for _id in id_list:
            query = {'_id': ObjectId(_id)}
            utils.conn_db('wih').delete_one(query)

        return utils.build_ret(ErrorMsg.Success, {'_id': id_list})