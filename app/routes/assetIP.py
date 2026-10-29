from bson import ObjectId
from flask_restx import Resource, Api, reqparse, fields, Namespace
from app.utils import get_logger, auth
from . import base_query_fields, HarrierResource, get_harrier_parser
from app.modules import ErrorMsg
from app import utils

ns = Namespace('asset_ip', description="Asset group IP information")

logger = get_logger()

base_search_fields = {
    'ip': fields.String(required=False, description="IP"),
    'domain': fields.String(description="Domain"),
    'port_info.port_id': fields.Integer(description="Port number"),
    'port_info.service_name': fields.String(description="System service name"),
    'port_info.version': fields.String(description="System service version"),
    'port_info.product': fields.String(description="Product"),
    'os_info.name': fields.String(description="OS name"),
    "task_id": fields.String(description="Task ID"),
    "update_date__dgt": fields.String(description="Update time greater than"),
    "update_date__dlt": fields.String(description="Update time less than"),
    "scope_id": fields.String(description="Asset scope ID"),
    "ip_type": fields.String(description="IP type: public (PUBLIC) or private (PRIVATE)"),
    "cdn_name": fields.String(description="CDN provider name")
}

base_search_fields.update(base_query_fields)


@ns.route('/')
class HarrierAssetIP(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query IP information
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='asset_ip')

        return data


@ns.route('/export/')
class HarrierAssetIPExport(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Export asset group ports
        """
        args = self.parser.parse_args()
        response = self.send_export_file(args=args, _type="asset_ip")

        return response


@ns.route('/export_ip/')
class HarrierIPExportIp(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Export IPs from asset group IPs
        """
        args = self.parser.parse_args()
        response = self.send_export_file_attr(args=args, collection="asset_ip", field="ip")

        return response


@ns.route('/export_domain/')
class HarrierIPExportIp(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Export domains from asset group IPs
        """
        args = self.parser.parse_args()
        response = self.send_export_file_attr(args=args, collection="asset_ip", field="domain")

        return response


delete_ip_fields = ns.model('deleteAssetIP',  {
    '_id': fields.List(fields.String(required=True, description="Data _id"))
})


@ns.route('/delete/')
class DeleteHarrierAssetIP(HarrierResource):
    @auth
    @ns.expect(delete_ip_fields)
    def post(self):
        """
        Delete IPs from an asset group
        """
        args = self.parse_args(delete_ip_fields)
        id_list = args.pop('_id', "")
        for _id in id_list:
            query = {'_id': ObjectId(_id)}
            utils.conn_db('asset_ip').delete_one(query)

        return utils.build_ret(ErrorMsg.Success, {'_id': id_list})