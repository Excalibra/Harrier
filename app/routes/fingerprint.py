import json
import time
import yaml
from werkzeug.datastructures import FileStorage
from urllib.parse import quote
from flask import make_response
from flask_restx import Resource, Api, reqparse, fields, Namespace
from bson import ObjectId
from app.utils import get_logger, auth, parse_human_rule, transform_rule_map
from app import utils
from app.modules import ErrorMsg
from app.services import check_expression_with_error, have_human_rule_from_db
from app.services import check_expression
from . import base_query_fields, HarrierResource, get_harrier_parser

ns = Namespace('fingerprint', description="Fingerprint information")

logger = get_logger()

base_search_fields = {
    'name': fields.String(required=False, description="Name"),
    "update_date__dgt": fields.String(description="Update time greater than"),
    "update_date__dlt": fields.String(description="Update time less than")
}

base_search_fields.update(base_query_fields)


add_fingerprint_fields = ns.model('addFingerSite', {
    'name': fields.String(required=True, description="Name"),
    'human_rule': fields.String(required=True, description="Rule"),
})


@ns.route('/')
class HarrierFingerprint(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query fingerprint information
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='fingerprint')

        return data

    @auth
    @ns.expect(add_fingerprint_fields)
    def post(self):
        """
        Add a fingerprint
        """
        args = self.parse_args(add_fingerprint_fields)

        human_rule = args.pop('human_rule')
        name = args.pop('name')

        if have_human_rule_from_db(human_rule):
            return utils.build_ret(ErrorMsg.RuleAlreadyExists, {"rule": human_rule})

        flag, err = check_expression_with_error(human_rule)
        if not flag:
            return utils.build_ret(ErrorMsg.RuleInvalid, {"error": str(err)})

        data = {
            "name": name,
            "human_rule": human_rule,
            "update_date": utils.curr_date_obj()
        }

        utils.conn_db('fingerprint').insert_one(data)

        finger_id = str(data.pop('_id'))

        data.pop('update_date')

        return utils.build_ret(ErrorMsg.Success, {"_id": finger_id, "data": data})


delete_finger_fields = ns.model('deleteFingerSite',  {
    '_id': fields.List(fields.String(required=True, description="Fingerprint _id"))
})


@ns.route('/delete/')
class DeleteHarrierFinger(HarrierResource):
    @auth
    @ns.expect(delete_finger_fields)
    def post(self):
        """
        Delete fingerprints
        """
        args = self.parse_args(delete_finger_fields)
        id_list = args.pop('_id', "")
        for _id in id_list:
            query = {'_id': ObjectId(_id)}
            utils.conn_db('fingerprint').delete_one(query)

        return utils.build_ret(ErrorMsg.Success, {'_id': id_list})


@ns.route('/export/')
class ExportHarrierFinger(HarrierResource):

    @auth
    def get(self):
        """
        Export fingerprints
        """
        items = []
        results = list(utils.conn_db('fingerprint').find())
        for result in results:
            item = dict()
            item["name"] = result["name"]
            item["rule"] = result["human_rule"]
            items.append(item)

        data = yaml.dump(items, default_flow_style=False, sort_keys=False, allow_unicode=True)
        response = make_response(data)
        filename = "fingerprint_{}_{}.yml".format(len(items), int(time.time()))
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
        response.headers["Content-Disposition"] = "attachment; filename={}".format(quote(filename))

        return response


file_upload = reqparse.RequestParser()
file_upload.add_argument('file',
                         type=FileStorage,
                         location='files',
                         required=True,
                         help='JSON file')


@ns.route('/upload/')
class UploadHarrierFinger(HarrierResource):

    @auth
    @ns.expect(file_upload)
    def post(self):
        """
        Upload fingerprints
        """
        args = file_upload.parse_args()
        file_data = args['file'].read()
        try:
            obj = yaml.safe_load(file_data)
            if not isinstance(obj, list):
                return utils.build_ret(ErrorMsg.Error, {'msg': "not list obj"})

            error_cnt = 0
            success_cnt = 0
            repeat_cnt = 0

            for rule in obj:
                human_rule = rule["rule"]
                rule_name = rule['name']

                rule_flag = check_expression(human_rule)
                if not rule_flag:
                    error_cnt += 1
                    continue

                result = utils.conn_db('fingerprint').find_one({"human_rule": human_rule})
                if result:
                    repeat_cnt += 1
                    continue

                data = {
                    "name": rule_name,
                    "human_rule": human_rule,
                    "update_date": utils.curr_date_obj()
                }
                success_cnt += 1

                utils.conn_db('fingerprint').insert_one(data)

            return utils.build_ret(ErrorMsg.Success, {'error_cnt': error_cnt,
                                                      'repeat_cnt': repeat_cnt,'success_cnt': success_cnt})
        except Exception as e:
            return utils.build_ret(ErrorMsg.Error, {'msg': str(e)})


