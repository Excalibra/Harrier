from bson import ObjectId
from flask_restx import Resource, Api, reqparse, fields, Namespace
from app.utils import get_logger, auth
from . import base_query_fields, HarrierResource, get_harrier_parser
from app import utils
from app.modules import ErrorMsg

ns = Namespace('cert', description="Certificate information")

logger = get_logger()

base_search_fields = {
    'ip': fields.String(description="ip"),
    'port': fields.Integer(description="Port"),
    'cert.subject_dn': fields.String(description="Subject name"),
    'cert.issuer_dn': fields.String(description="Issuer name"),
    'cert.serial_number ': fields.String(description="Serial number"),
    'cert.validity.start': fields.String(description="Start time"),
    'cert.validity.end': fields.String(description="End time"),
    'cert.fingerprint.sha256': fields.String(description="SHA-256"),
    'cert.fingerprint.sha1': fields.String(description="SHA-1"),
    'cert.fingerprint.md5': fields.String(description="MD5"),
    'cert.extensions.subjectAltName': fields.String(description="Alternative name"),
    'task_id': fields.String(description="Task ID"),
}

base_search_fields.update(base_query_fields)


@ns.route('/')
class HarrierCert(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query SSL certificates
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args,  collection='cert')

        return data


delete_cert_fields = ns.model('deleteCertFields',  {
    '_id': fields.List(fields.String(required=True, description="Certificate _id"))
})


@ns.route('/delete/')
class DeleteHarrierCert(HarrierResource):
    @auth
    @ns.expect(delete_cert_fields)
    def post(self):
        """
        Delete SSL certificate information
        """
        args = self.parse_args(delete_cert_fields)
        id_list = args.pop('_id', [])
        for _id in id_list:
            query = {'_id': ObjectId(_id)}
            utils.conn_db('cert').delete_one(query)

        return utils.build_ret(ErrorMsg.Success, {'_id': id_list})