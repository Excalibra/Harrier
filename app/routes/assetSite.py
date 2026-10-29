from bson import ObjectId
from flask_restx import Resource, Api, reqparse, fields, Namespace
from app.utils import get_logger, auth
from . import base_query_fields, HarrierResource, get_harrier_parser
from app.modules import ErrorMsg, TaskTag
from app import utils, services
from app.helpers import (
    find_asset_site_not_in_scope,
    submit_add_asset_site_task,
    target2list,
    get_options_by_policy_id
)

ns = Namespace('asset_site', description="Asset group site information")

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
    'scope_id': fields.String(description="Scope ID"),
    "update_date__dgt": fields.String(description="Update time greater than"),
    "update_date__dlt": fields.String(description="Update time less than"),
    'tag': fields.String(description="Tag list")
}

site_search_fields = base_search_fields.copy()

base_search_fields.update(base_query_fields)

add_site_fields = ns.model('addAssetSite',  {
    'site': fields.String(required=True, description="Site"),
    'scope_id': fields.String(required=True, description="Asset group scope ID"),
    'policy_id': fields.String(description="Policy ID"),
})


@ns.route('/')
class HarrierAssetSite(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query asset site information
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='asset_site')

        return data

    @auth
    @ns.expect(add_site_fields)
    def post(self):
        """
        Add sites to an asset group
        """
        args = self.parse_args(add_site_fields)
        site = args.pop("site")  # a large number of sites may be submitted here
        scope_id = args.pop("scope_id")
        policy_id = args.pop("policy_id")

        scope_data = utils.conn_db('asset_scope').find_one({"_id": ObjectId(scope_id)})
        if not scope_data:
            return utils.build_ret(ErrorMsg.NotFoundScopeID, {"scope_id": scope_id})

        scope_type = scope_data.get("scope_type", "domain")
        if scope_type == "ip":
            return utils.build_ret(ErrorMsg.AddAssetSiteNotSupportIP, {})

        sites = target2list(site)
        if not sites:
            return utils.build_ret(ErrorMsg.URLInvalid, {"site": site})

        not_in_scope_sites = find_asset_site_not_in_scope(sites, scope_id)
        if not_in_scope_sites:
            return utils.build_ret(ErrorMsg.TaskTargetNotInScope, {"not_in_scope_sites": site})

        name = "AddSite-{}".format(scope_data["name"])

        options = {
            'site_identify': False,
            'site_capture': False,
            'file_leak': False,
            'site_spider': False,
            'search_engines': False,
            'related_scope_id': scope_id
        }

        try:
            if policy_id and len(policy_id) == 24:
                policy_options = get_options_by_policy_id(policy_id=policy_id, task_tag=TaskTag.RISK_CRUISING)
                if policy_options:
                    policy_options["related_scope_id"] = scope_id
                    options.update(policy_options)

            task_data = submit_add_asset_site_task(task_name=name, target=sites, options=options)
        except Exception as e:
            logger.exception(e)
            return utils.build_ret(ErrorMsg.Error, {"error": str(e)})

        return utils.build_ret(ErrorMsg.Success, task_data)


@ns.route('/export/')
class HarrierSiteExport(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Export asset group sites
        """
        args = self.parser.parse_args()
        response = self.send_export_file(args=args, _type="asset_site")

        return response


def add_site_to_scope(site, scope_id):
    fetch_site_data = services.fetch_site([site])
    web_analyze_data = services.web_analyze([site])
    finger = web_analyze_data.get(site, [])
    curr_date = utils.curr_date_obj()
    if fetch_site_data:
        item = fetch_site_data[0]
        item["finger"] = finger
        item["screenshot"] = ""
        item["scope_id"] = scope_id
        item["save_date"] = curr_date
        item["update_date"] = curr_date

        utils.conn_db('asset_site').insert_one(item)


delete_asset_site_fields = ns.model('deleteAssetSite',  {
    '_id': fields.List(fields.String(required=True, description="Site _id"))
})


@ns.route('/delete/')
class DeleteHarrierAssetSite(HarrierResource):
    @auth
    @ns.expect(delete_asset_site_fields)
    def post(self):
        """
        Delete sites from an asset group
        """
        args = self.parse_args(delete_asset_site_fields)
        id_list = args.pop('_id', "")
        for _id in id_list:
            query = {'_id': ObjectId(_id)}
            utils.conn_db('asset_site').delete_one(query)

        return utils.build_ret(ErrorMsg.Success, {'_id': id_list})


@ns.route('/save_result_set/')
class HarrierSaveResultSet(HarrierResource):
    parser = get_harrier_parser(site_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Save asset sites to a result set
        """
        args = self.parser.parse_args()
        query = self.build_db_query(args)
        items = utils.conn_db('asset_site').distinct("site", query)

        items = list(set([utils.url.cut_filename(x) for x in items]))

        if len(items) == 0:
            return utils.build_ret(ErrorMsg.QueryResultIsEmpty, {})

        data = {
            "items": items,
            "type": "asset_site",
            "total": len(items)
        }
        result = utils.conn_db('result_set').insert_one(data)

        ret_data = {
            "result_set_id": str(result.inserted_id),
            "result_total": len(items),
            "type": "asset_site"
        }

        return utils.build_ret(ErrorMsg.Success, ret_data)


add_asset_site_tag_fields = ns.model('AddAssetSiteTagFields',  {
    "tag": fields.String(required=True, description="Site tag to add"),
    "_id": fields.String(description="Asset site ID", required=True)
})


@ns.route('/add_tag/')
class AddAssetSiteTagHarrier(HarrierResource):

    @auth
    @ns.expect(add_asset_site_tag_fields)
    def post(self):
        """
        Add a tag to an asset site
        """
        args = self.parse_args(add_asset_site_tag_fields)
        site_id = args.pop("_id")
        tag = args.pop("tag")

        query = {"_id": ObjectId(site_id)}
        data = utils.conn_db('asset_site').find_one(query)
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

        utils.conn_db('asset_site').update_one(query, {"$set": {"tag": tag_list}})

        return utils.build_ret(ErrorMsg.Success, {"tag": tag})


delete_asset_site_tag_fields = ns.model('delete_asset_site_tag_fields',  {
    "tag": fields.String(required=True, description="Asset site tag to delete"),
    "_id": fields.String(description="Asset site ID", required=True)
})


@ns.route('/delete_tag/')
class DeleteAssetSiteTagHarrier(HarrierResource):

    @auth
    @ns.expect(delete_asset_site_tag_fields)
    def post(self):
        """
        Delete a tag from an asset site
        """
        args = self.parse_args(delete_asset_site_tag_fields)
        site_id = args.pop("_id")
        tag = args.pop("tag")

        query = {"_id": ObjectId(site_id)}
        data = utils.conn_db('asset_site').find_one(query)
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

        utils.conn_db('asset_site').update_one(query, {"$set": {"tag": tag_list}})

        return utils.build_ret(ErrorMsg.Success, {"tag": tag})

