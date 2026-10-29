from bson import ObjectId
from flask_restx import Resource, Api, reqparse, fields, Namespace
from app.utils import get_logger, auth
from . import base_query_fields, HarrierResource, get_harrier_parser
from app import utils
from app.modules import ErrorMsg

ns = Namespace('fileleak', description="File leak information")

logger = get_logger()

base_search_fields = {
    'url': fields.String(required=False, description="URL"),
    'site': fields.String(description="Site"),
    'content_length': fields.Integer(description="Body length"),
    'status_code': fields.Integer(description="Status code"),
    'title': fields.String(description="Title"),
    "task_id": fields.String(description="Task ID")
}

base_search_fields.update(base_query_fields)


@ns.route('/')
class HarrierFileLeak(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query file leak information
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='fileleak')

        return data


delete_fileleak_fields = ns.model('deleteFileleakFields',  {
    '_id': fields.List(fields.String(required=True, description="File leak _id"))
})


@ns.route('/delete/')
class DeleteHarrierFileleak(HarrierResource):
    @auth
    @ns.expect(delete_fileleak_fields)
    def post(self):
        """
        Delete file leaks
        """
        args = self.parse_args(delete_fileleak_fields)
        id_list = args.pop('_id', [])
        for _id in id_list:
            query = {'_id': ObjectId(_id)}
            utils.conn_db('fileleak').delete_one(query)

        return utils.build_ret(ErrorMsg.Success, {'_id': id_list})

