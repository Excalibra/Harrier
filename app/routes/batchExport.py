import time
from flask_restx import Resource, Api, reqparse, fields, Namespace
from app.utils import auth
from app import utils
from . import HarrierResource

ns = Namespace('batch_export', description="Batch export")


batch_export_fields = ns.model('BatchExport',  {
    "task_id": fields.List(fields.String(description="Task ID"), required=True),
})


@ns.route('/site/')
class BatchExportSite(HarrierResource):

    @auth
    @ns.expect(batch_export_fields)
    def post(self):
        """
        Batch export sites
        """
        args = self.parse_args(batch_export_fields)
        task_id_list = args.pop("task_id", [])
        response = self.send_batch_export_file(task_id_list, "site")

        return response


@ns.route('/domain/')
class BatchExportDomain(HarrierResource):

    @auth
    @ns.expect(batch_export_fields)
    def post(self):
        """
        Batch export domains
        """
        args = self.parse_args(batch_export_fields)
        task_id_list = args.get("task_id", [])

        response = self.send_batch_export_file(task_id_list, "domain")

        return response


@ns.route('/ip/')
class BatchExportIP(HarrierResource):

    @auth
    @ns.expect(batch_export_fields)
    def post(self):
        """
        Batch export IPs
        """
        args = self.parse_args(batch_export_fields)
        task_id_list = args.get("task_id", [])

        response = self.send_batch_export_file(task_id_list, "ip")

        return response


@ns.route('/url/')
class BatchExportURL(HarrierResource):

    @auth
    @ns.expect(batch_export_fields)
    def post(self):
        """
        Batch export URLs
        """
        args = self.parse_args(batch_export_fields)
        task_id_list = args.get("task_id", [])

        response = self.send_batch_export_file(task_id_list, "url")

        return response


@ns.route('/ip_port/')
class BatchExportIpPort(HarrierResource):

    @auth
    @ns.expect(batch_export_fields)
    def post(self):
        """
        Batch export IP:port pairs
        """
        args = self.parse_args(batch_export_fields)
        task_id_list = args.get("task_id", [])

        items_set = set()
        for task_id in task_id_list:
            if not task_id:
                continue

            query = {"task_id": task_id}
            items = list(utils.conn_db('ip').find(query, {"ip": 1, "port_info": 1}))

            for item in items:
                curr_ip = item["ip"]
                for port_info in item.get("port_info", []):
                    items_set.add("{}:{}".format(curr_ip, port_info["port_id"]))

        response = self.send_file(items_set, "ip_port")

        return response


@ns.route('/cip/')
class BatchExportCIP(HarrierResource):

    @auth
    @ns.expect(batch_export_fields)
    def post(self):
        """
        Batch export C-class segments
        """
        args = self.parse_args(batch_export_fields)
        task_id_list = args.get("task_id", [])

        response = self.send_batch_export_file(task_id_list, "cip")

        return response


@ns.route('/wih/')
class BatchExportWIH(HarrierResource):

    @auth
    @ns.expect(batch_export_fields)
    def post(self):
        """
        Batch export WIH
        """
        args = self.parse_args(batch_export_fields)
        task_id_list = args.get("task_id", [])

        response = self.send_batch_export_file(task_id_list, "wih")

        return response


scope_batch_export_fields = ns.model('ScopeBatchExport',  {
    "scope_id": fields.List(fields.String(description="Asset group ID"), required=True),
})


@ns.route('/asset_ip/')
class BatchExportAssetIP(HarrierResource):

    @auth
    @ns.expect(scope_batch_export_fields)
    def post(self):
        """
        Batch export IPs from asset groups
        """
        args = self.parse_args(scope_batch_export_fields)
        scope_id_list = args.get("scope_id", [])

        response = self.send_scope_batch_export_file(scope_id_list, "asset_ip")

        return response


@ns.route('/asset_domain/')
class BatchExportAssetIP(HarrierResource):

    @auth
    @ns.expect(scope_batch_export_fields)
    def post(self):
        """
        Batch export domains from asset groups
        """
        args = self.parse_args(scope_batch_export_fields)
        scope_id_list = args.get("scope_id", [])

        response = self.send_scope_batch_export_file(scope_id_list, "asset_domain")

        return response


@ns.route('/asset_site/')
class BatchExportAssetIP(HarrierResource):

    @auth
    @ns.expect(scope_batch_export_fields)
    def post(self):
        """
        Batch export sites from asset groups
        """
        args = self.parse_args(scope_batch_export_fields)
        scope_id_list = args.get("scope_id", [])

        response = self.send_scope_batch_export_file(scope_id_list, "asset_site")

        return response


@ns.route('/asset_wih/')
class BatchExportAssetWIH(HarrierResource):

    @auth
    @ns.expect(scope_batch_export_fields)
    def post(self):
        """
        Batch export WIH from asset groups
        """
        args = self.parse_args(scope_batch_export_fields)
        scope_id_list = args.get("scope_id", [])

        response = self.send_scope_batch_export_file(scope_id_list, "asset_wih")

        return response
