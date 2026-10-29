from bson import ObjectId
from flask_restx import Resource, Api, reqparse, fields, Namespace
from app.utils import get_logger, auth
from app import utils
from app.modules import ErrorMsg
from . import base_query_fields, HarrierResource, get_harrier_parser

ns = Namespace('domain', description="Domain information")

logger = get_logger()

base_search_fields = {
    'domain': fields.String(required=False, description="Domain"),
    'record': fields.String(description="Resolution value"),
    'type': fields.String(description="Resolution type"),
    'ips': fields.String(description="IP"),
    'source': fields.String(description="Source"),
    "task_id": fields.String(description="Task ID")
}

base_search_fields.update(base_query_fields)


@ns.route('/')
class HarrierDomain(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query domain information
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='domain')

        return data


@ns.route('/export/')
class HarrierDomainExport(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Export domains
        """
        args = self.parser.parse_args()
        response = self.send_export_file(args=args, _type="domain")

        return response


delete_domain_fields = ns.model('deleteDomainFields',  {
    '_id': fields.List(fields.String(required=True, description="Domain _id"))
})


@ns.route('/delete/')
class DeleteHarrierDomain(HarrierResource):
    @auth
    @ns.expect(delete_domain_fields)
    def post(self):
        """
        Delete domains
        """
        args = self.parse_args(delete_domain_fields)
        id_list = args.pop('_id', [])
        for _id in id_list:
            query = {'_id': ObjectId(_id)}
            utils.conn_db('domain').delete_one(query)

        return utils.build_ret(ErrorMsg.Success, {'_id': id_list})
