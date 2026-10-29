from bson import ObjectId
from flask_restx import Resource, Api, reqparse, fields, Namespace
from app.utils import get_logger, auth
from app import utils
from app.modules import ErrorMsg
from . import base_query_fields, HarrierResource, get_harrier_parser

ns = Namespace('ip', description="IP information")

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
    "ip_type": fields.String(description="IP type: public (PUBLIC) or private (PRIVATE)"),
    "cdn_name": fields.String(description="CDN provider name"),
    "geo_asn.number": fields.Integer(description="AS number"),
    "geo_asn.organization": fields.String(description="AS organization"),
    "geo_city.region_name": fields.String(description="GEO region_name")
}

base_search_fields.update(base_query_fields)


@ns.route('/')
class HarrierIP(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query IP information
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='ip')

        return data


@ns.route('/export/')
class HarrierIPExport(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Export ports
        """
        args = self.parser.parse_args()
        response = self.send_export_file(args=args, _type="ip")

        return response


@ns.route('/export_domain/')
class HarrierIPExportDomain(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Export domains from IPs
        """
        args = self.parser.parse_args()
        response = self.send_export_file_attr(args=args, collection="ip", field="domain")

        return response


@ns.route('/export_ip/')
class HarrierIPExportIp(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Export IPs from IPs
        """
        args = self.parser.parse_args()
        response = self.send_export_file_attr(args=args, collection="ip", field="ip")

        return response


delete_ip_fields = ns.model('deleteIpFields',  {
    '_id': fields.List(fields.String(required=True, description="IP _id"))
})


@ns.route('/delete/')
class DeleteHarrierIP(HarrierResource):
    @auth
    @ns.expect(delete_ip_fields)
    def post(self):
        """
        Delete IPs
        """
        args = self.parse_args(delete_ip_fields)
        id_list = args.pop('_id', [])
        for _id in id_list:
            query = {'_id': ObjectId(_id)}
            utils.conn_db('ip').delete_one(query)

        return utils.build_ret(ErrorMsg.Success, {'_id': id_list})
