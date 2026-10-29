from flask_restx import Resource, Api, reqparse, fields, Namespace
from app.utils import get_logger, auth
from . import base_query_fields, HarrierResource, get_harrier_parser
from app.modules import ErrorMsg
from app import utils
from bson import ObjectId
from flask_restx.fields import Nested, String, Boolean, List
from flask_restx.model import Model

ns = Namespace('policy', description="Policy information")

logger = get_logger()

base_search_fields = {
    'name': fields.String(required=False, description="Policy name"),
    "_id": fields.String(description="Policy ID")
}

base_search_fields.update(base_query_fields)


@ns.route('/')
class HarrierPolicy(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query policy information
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='policy')

        return data


'''Domain-related configuration options'''
domain_config_fields = ns.model('domainConfig', {
    "domain_brute": fields.Boolean(description="Domain brute-force", default=True),
    "domain_brute_type": fields.String(description="Domain brute-force type (big)", example="big"),
    "alt_dns": fields.Boolean(description="Smart DNS dictionary generation", default=True),
    "harrier_search": fields.Boolean(description="Harrier history search", default=True),
    "dns_query_plugin": fields.Boolean(description="Domain plugin query", default=False)
})

'''IP-related configuration options'''
ip_config_fields = ns.model('ipConfig', {
    "port_scan": fields.Boolean(description="Port scan", default=True),
    "port_scan_type": fields.String(description="Port scan type (test|top100|top1000|all|custom)", example="test"),
    "service_detection": fields.Boolean(description="Service detection", default=False),
    "os_detection": fields.Boolean(description="OS detection", default=False),
    "ssl_cert": fields.Boolean(description="SSL certificate retrieval", default=False),
    "skip_scan_cdn_ip": fields.Boolean(description="Skip CDN IP scan", default=True),  # this parameter is always enforced
    "port_custom": fields.String(description="Custom scan ports", default="80,443"),  # only effective when port scan type is custom
    "host_timeout_type": fields.String(description="Host timeout type (default|custom)", default="default"),
    "host_timeout": fields.Integer(description="Host timeout (s)", default=900),
    "port_parallelism": fields.Integer(description="Probe packet parallelism", default=32),
    "port_min_rate": fields.Integer(description="Minimum packet send rate", default=60),
    "exclude_ports": fields.String(description="Ports excluded from scanning", default=""),
})

'''Site-related configuration options'''
site_config_fields = ns.model('siteConfig', {
    "site_identify": fields.Boolean(description="Site identification", default=False),
    "site_capture": fields.Boolean(description="Site screenshot", default=False),
    "search_engines": fields.Boolean(description="Search engine queries", default=False),
    "site_spider": fields.Boolean(description="Site spider", default=False),
    "nuclei_scan": fields.Boolean(description="nuclei scan", default=False),
    "web_info_hunter": fields.Boolean(example=False, default=False, description="Information gathering from web JS"),
})

'''Asset group association configuration'''
scope_config_fields = ns.model('scopeConfig', {
    "scope_id": fields.String(description="Asset group ID", default=""),
})

add_policy_fields = ns.model('addPolicy', {
    "name": fields.String(required=True, description="Policy name"),
    "desc": fields.String(description="Policy description"),
    "policy": fields.Nested(ns.model("policy", {
        "domain_config": fields.Nested(domain_config_fields),
        "ip_config": fields.Nested(ip_config_fields),
        "site_config": fields.Nested(site_config_fields),
        "file_leak": fields.Boolean(description="File leak", default=False),
        "npoc_service_detection": fields.Boolean(description="Service detection (pure Python implementation)", default=False),
        "poc_config": fields.List(fields.Nested(ns.model('pocConfig', {
            "plugin_name": fields.String(description="poc plugin name ID", default=False),
            "enable": fields.Boolean(description="Whether to enable", default=True)
        }))),
        "brute_config": fields.List(fields.Nested(ns.model('bruteConfig', {
            "plugin_name": fields.String(description="poc plugin name ID", default=False),
            "enable": fields.Boolean(description="Whether to enable", default=True)
        }))),
        "scope_config": fields.Nested(scope_config_fields)
    }, required=True)
                            )
})


@ns.route('/add/')
class AddHarrierPolicy(HarrierResource):

    @auth
    @ns.expect(add_policy_fields)
    def post(self):
        """
        Add policy
        """
        args = self.parse_args(add_policy_fields)
        name = args.pop("name")
        policy = args.pop("policy", {})
        if policy is None:
            return utils.build_ret("Missing policy parameter", {})

        domain_config = policy.pop("domain_config", {})
        domain_config = self._update_arg(domain_config, domain_config_fields)
        ip_config = policy.pop("ip_config", {})
        port_scan_type = ip_config.get("port_scan_type", "test")
        if port_scan_type == "custom":
            port_custom = ip_config.get("port_custom", "80,443")
            port_list = utils.harrier.build_port_custom(port_custom)
            if isinstance(port_list, str):
                return utils.build_ret(ErrorMsg.PortCustomInvalid, {"port_custom": port_list})

            ip_config["port_custom"] = ",".join(port_list)

        exclude_ports = ip_config.get("exclude_ports", "")
        if exclude_ports:
            if not utils.is_valid_exclude_ports(exclude_ports):
                return utils.build_ret(ErrorMsg.ExcludePortsInvalid, {"exclude_ports": exclude_ports})

        ip_config = self._update_arg(ip_config, ip_config_fields)

        site_config = policy.pop("site_config", {})
        site_config = self._update_arg(site_config, site_config_fields)

        poc_config = policy.pop("poc_config", [])
        if poc_config is None:
            poc_config = []

        poc_config = _update_plugin_config(poc_config)
        if isinstance(poc_config, str):
            return utils.build_ret(poc_config, {})

        brute_config = policy.pop("brute_config", [])
        if brute_config is None:
            brute_config = []
        brute_config = _update_plugin_config(brute_config)
        if isinstance(brute_config, str):
            return utils.build_ret(brute_config, {})

        file_leak = fields.boolean(policy.pop("file_leak", False))
        npoc_service_detection = fields.boolean(policy.pop("npoc_service_detection", False))
        desc = args.pop("desc", "")

        # Only get the linked asset group config
        scope_config = policy.pop("scope_config", {})
        scope_config = self._update_arg(scope_config, scope_config_fields)

        item = {
            "name": name,
            "policy": {
                "domain_config": domain_config,
                "ip_config": ip_config,
                "site_config": site_config,
                "poc_config": poc_config,
                "brute_config": brute_config,
                "file_leak": file_leak,
                "npoc_service_detection": npoc_service_detection,
                "scope_config": scope_config
            },
            "desc": desc,
            "update_date": utils.curr_date()
        }
        utils.conn_db("policy").insert_one(item)

        return utils.build_ret(ErrorMsg.Success, {"policy_id": str(item["_id"])})

    def _update_arg(self, arg_dict, default_module):
        default_dict = get_dict_default_from_module(default_module)
        if arg_dict is None:
            return default_dict

        default_dict.update(arg_dict)

        for x in default_dict:
            if x not in default_module:
                continue

            default_dict[x] = default_module[x].format(default_dict[x])

        return default_dict


def plugin_name_in_harrier(name):
    query = {
        "plugin_name": name
    }
    item = utils.conn_db('poc').find_one(query)
    return item


def get_dict_default_from_module(module):
    ret = {}
    for x in module:
        v = module[x]
        ret[x] = None
        if v.default is not None:
            ret[x] = v.default

        if v.example is not None:
            ret[x] = v.example

    return ret


delete_policy_fields = ns.model('DeletePolicy', {
    'policy_id': fields.List(fields.String(required=True, description="Policy ID", example="603c65316591e73dd717d176"))
})


@ns.route('/delete/')
class DeletePolicy(HarrierResource):
    @auth
    @ns.expect(delete_policy_fields)
    def post(self):
        """
        Delete policy
        """
        args = self.parse_args(delete_policy_fields)
        policy_id_list = args.pop('policy_id')
        for policy_id in policy_id_list:
            if not policy_id:
                continue
            utils.conn_db('policy').delete_one({'_id': ObjectId(policy_id)})

        """Return success directly here"""
        return utils.build_ret(ErrorMsg.Success, {})


edit_policy_fields = ns.model('editPolicy', {
    'policy_id': fields.String(required=True, description="Policy ID", example="603c65316591e73dd717d176"),
    'policy_data': fields.Nested(ns.model("policyData", {}))
})


@ns.route('/edit/')
class EditPolicy(HarrierResource):
    @auth
    @ns.expect(edit_policy_fields)
    def post(self):
        """
        Edit policy
        """
        args = self.parse_args(edit_policy_fields)
        policy_id = args.pop('policy_id')
        policy_data = args.pop('policy_data', {})
        query = {'_id': ObjectId(policy_id)}
        item = utils.conn_db('policy').find_one(query)

        if not item:
            return utils.build_ret(ErrorMsg.PolicyIDNotFound, {})

        if not policy_data:
            return utils.build_ret(ErrorMsg.PolicyDataIsEmpty, {})

        allow_keys = gen_model_policy_keys(add_policy_fields["policy"])
        allow_keys.extend(["name", "desc", "policy"])

        item = change_policy_dict(item, policy_data, allow_keys)

        poc_config = item["policy"].pop("poc_config", [])
        poc_config = _update_plugin_config(poc_config)
        if isinstance(poc_config, str):
            return utils.build_ret(poc_config, {})
        item["policy"]["poc_config"] = poc_config

        brute_config = item["policy"].pop("brute_config", [])
        brute_config = _update_plugin_config(brute_config)
        if isinstance(brute_config, str):
            return utils.build_ret(brute_config, {})
        item["policy"]["brute_config"] = brute_config

        item["update_date"] = utils.curr_date()
        utils.conn_db('policy').find_one_and_replace(query, item)
        item.pop('_id')

        return utils.build_ret(ErrorMsg.Success, {"data": item})


def _update_plugin_config(config):
    plugin_name_set = set()
    ret = []
    for item in config:
        plugin_name = str(item.get("plugin_name", ""))
        enable = item.get("enable", False)
        if plugin_name is None or enable is None:
            continue
        if plugin_name in plugin_name_set:
            continue

        plugin_info = plugin_name_in_harrier(plugin_name)
        if not plugin_info:
            return "plugin not found: {}".format(plugin_name)

        config_item = {
            "plugin_name": plugin_name,
            "vul_name": plugin_info["vul_name"],
            "enable": bool(enable)
        }
        plugin_name_set.add(plugin_name)
        ret.append(config_item)

    return ret


# change_policy_dict: modify a policy, allowing new fields to be changed
def change_policy_dict(old_data, new_data, allow_keys):
    if not isinstance(new_data, dict):
        return

    for key in new_data:
        if key not in allow_keys:
            continue

        next_old_data = old_data.get(key)
        next_new_data = new_data[key]
        if next_old_data is None:
            old_data[key] = next_new_data
            continue

        next_new_data_type = type(next_new_data)
        next_old_data_type = type(next_old_data)

        if isinstance(next_old_data, dict):
            change_policy_dict(next_old_data, next_new_data, allow_keys)

        elif isinstance(next_old_data, list) and isinstance(next_new_data, list):
            old_data[key] = next_new_data

        elif next_new_data_type == next_old_data_type:
            old_data[key] = next_new_data

    return old_data  # return data


# gen_model_policy_keys: recursively generate policy keys (for validity checking)
def gen_model_policy_keys(model):
    if isinstance(model, Model):
        keys = []
        for name in model:
            keys.append(name)
            keys.extend(gen_model_policy_keys(model[name]))

        return keys

    elif isinstance(model, Nested):
        return gen_model_policy_keys(model.model)
    else:
        return []
