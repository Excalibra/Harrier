import copy
from bson import ObjectId
from flask_restx import Resource, Api, reqparse, fields, Namespace
from app.utils import get_logger, auth
from app.modules import ErrorMsg
from app import utils
from . import base_query_fields, HarrierResource, get_harrier_parser


ns = Namespace('site', description="Site information")

logger = get_logger()

base_search_fields = {
    'site': fields.String(required=False, description="Site URL"),
    'hostname': fields.String(description="Hostname"),
    'ip': fields.String(description="ip"),
    'title': fields.String(description="Title"),
    'http_server': fields.String(description="Web servers"),
    'headers': fields.String(description="headers"),
    'finger.name': fields.String(description="Fingerprint"),
    'status': fields.Integer(description="Status code"),
    'favicon.hash': fields.Integer(description="favicon hash"),
    'task_id': fields.String(description="Task ID"),
    'tag': fields.String(description="Tag list")
}

site_search_fields = copy.copy(base_search_fields)

base_search_fields.update(base_query_fields)


@ns.route('/')
class HarrierSite(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query site information
        """
        args = self.parser.parse_args()
        data = self.build_data(args = args,  collection = 'site')

        return data


@ns.route('/export/')
class HarrierSiteExport(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Export sites
        """
        args = self.parser.parse_args()
        response = self.send_export_file(args=args, _type="site")

        return response


@ns.route('/save_result_set/')
class HarrierSaveResultSet(HarrierResource):
    parser = get_harrier_parser(site_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Save sites to a result set
        """
        args = self.parser.parse_args()
        query = self.build_db_query(args)
        items = utils.conn_db('site').distinct("site", query)

        items = list(set([utils.url.cut_filename(x) for x in items]))

        if len(items) == 0:
            return utils.build_ret(ErrorMsg.QueryResultIsEmpty, {})

        data = {
            "items": items,
            "type": "site",
            "total": len(items)
        }
        result = utils.conn_db('result_set').insert_one(data)

        ret_data = {
            "result_set_id": str(result.inserted_id),
            "result_total": len(items),
            "type": "site",
        }

        return utils.build_ret(ErrorMsg.Success, ret_data)


add_site_tag_fields = ns.model('AddSiteTagFields',  {
    "tag": fields.String(required=True, description="Site tag to add"),
    "_id": fields.String(description="Site ID", required=True)
})


@ns.route('/add_tag/')
class AddSiteTagHarrier(HarrierResource):

    @auth
    @ns.expect(add_site_tag_fields)
    def post(self):
        """
        Add a tag to a site
        """
        args = self.parse_args(add_site_tag_fields)
        site_id = args.pop("_id")
        tag = args.pop("tag")

        query = {"_id": ObjectId(site_id)}
        data = utils.conn_db('site').find_one(query)
        if not data:
            return utils.build_ret(ErrorMsg.SiteIdNotFound, {"site_id": site_id})

        tag_list = []
        old_tag = data.get("tag")
        if old_tag:
            if isinstance(old_tag, str):
                tag_list.append(old_tag)

            if isinstance(old_tag, list):
                tag_list.extend(old_tag)

        if tag in tag_list:
            return utils.build_ret(ErrorMsg.SiteTagIsExist, {"tag": tag})

        tag_list.append(tag)

        utils.conn_db('site').update_one(query, {"$set": {"tag": tag_list}})

        return utils.build_ret(ErrorMsg.Success, {"tag": tag})


delete_site_tag_fields = ns.model('DeleteSiteTagFields',  {
    "tag": fields.String(required=True, description="Site tag to delete"),
    "_id": fields.String(description="Site ID", required=True)
})


@ns.route('/delete_tag/')
class DeleteSiteTagHarrier(HarrierResource):

    @auth
    @ns.expect(delete_site_tag_fields)
    def post(self):
        """
        Delete a tag from a site
        """
        args = self.parse_args(delete_site_tag_fields)
        site_id = args.pop("_id")
        tag = args.pop("tag")

        query = {"_id": ObjectId(site_id)}
        data = utils.conn_db('site').find_one(query)
        if not data:
            return utils.build_ret(ErrorMsg.SiteIdNotFound, {"site_id": site_id})

        tag_list = []
        old_tag = data.get("tag")
        if old_tag:
            if isinstance(old_tag, str):
                tag_list.append(old_tag)

            if isinstance(old_tag, list):
                tag_list.extend(old_tag)

        if tag not in tag_list:
            return utils.build_ret(ErrorMsg.SiteTagNotExist, {"tag": tag})

        tag_list.remove(tag)

        utils.conn_db('site').update_one(query, {"$set": {"tag": tag_list}})

        return utils.build_ret(ErrorMsg.Success, {"tag": tag})


delete_site_fields = ns.model('deleteSiteFields',  {
    '_id': fields.List(fields.String(required=True, description="Site _id"))
})


@ns.route('/delete/')
class DeleteHarrierSite(HarrierResource):
    @auth
    @ns.expect(delete_site_fields)
    def post(self):
        """
        Delete sites
        """
        args = self.parse_args(delete_site_fields)
        id_list = args.pop('_id', [])
        for _id in id_list:
            query = {'_id': ObjectId(_id)}
            utils.conn_db('site').delete_one(query)

        return utils.build_ret(ErrorMsg.Success, {'_id': id_list})