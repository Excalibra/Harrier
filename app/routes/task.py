import re
import bson
from flask_restx import Resource, Api, reqparse, fields, Namespace
from bson import ObjectId
from app import celerytask
from app.utils import get_logger, auth
from . import base_query_fields, HarrierResource, get_harrier_parser, conn
from app import utils
from app.modules import TaskStatus, ErrorMsg, TaskSyncStatus, CeleryAction, TaskTag, TaskType
from app.helpers import get_options_by_policy_id, submit_task_task,\
    submit_risk_cruising, get_scope_by_scope_id, check_target_in_scope
from app.helpers.task import get_task_data, restart_task

ns = Namespace('task', description="Asset discovery task information")

logger = get_logger()

base_search_task_fields = {
    'name': fields.String(required=False, description="Task name"),
    'target': fields.String(description="Task target"),
    'status': fields.String(description="Task status"),
    '_id': fields.String(description="Task ID"),
    'task_tag': fields.String(description="Tag for monitor tasks and recon tasks"),
    'options.domain_brute': fields.Boolean(description="Whether to enable domain brute-force"),
    'options.domain_brute_type': fields.String(description="Domain brute-force type"),
    'options.port_scan_type': fields.Boolean(description="Port scan type"),
    'options.port_scan': fields.Boolean(description="Whether to enable port scan"),
    'options.service_detection': fields.Boolean(description="Whether to enable service detection"),
    'options.service_brute': fields.Boolean(description="Whether to enable service weak-password brute-force"),
    'options.os_detection': fields.Boolean(description="Whether to enable OS detection"),
    'options.site_identify': fields.Boolean(description="Whether to enable site identification"),
    'options.file_leak': fields.Boolean(description="Whether to enable file leak scan"),
    'options.alt_dns': fields.Boolean(description="Whether to enable smart DNS dictionary generation"),
    'options.search_engines': fields.Boolean(description="Whether to enable search engine queries"),
    'options.site_spider': fields.Boolean(description="Whether to enable site spider"),
    'options.harrier_search': fields.Boolean(description="Whether to enable Harrier history search"),
    'options.dns_query_plugin': fields.Boolean(description="Whether to enable domain plugin query"),
    'options.skip_scan_cdn_ip': fields.Boolean(description="Whether to skip CDN IP port scan"),
    'options.nuclei_scan': fields.Boolean(description="Whether to enable nuclei scan"),
    'options.findvhost': fields.Boolean(description="Whether to enable Host collision detection"),
    'options.web_info_hunter': fields.Boolean(description="Whether to enable webInfoHunter"),
    'statistic.site_cnt': fields.Integer(description="Site count equals"),
    'statistic.site_cnt__gt': fields.Integer(description="Site count greater than"),
    'statistic.site_cnt__lt': fields.Integer(description="Site count less than"),
    'statistic.domain_cnt': fields.Integer(description="Domain count equals"),
    'statistic.domain_cnt__gt': fields.Integer(description="Domain count greater than"),
    'statistic.domain_cnt__lt': fields.Integer(description="Domain count less than"),
    'statistic.wih_cnt': fields.Integer(description="WIH count equals"),
    'statistic.wih_cnt__gt': fields.Integer(description="WIH count greater than"),
    'statistic.wih_cnt__lt': fields.Integer(description="WIH count less than"),
}

base_search_task_fields.update(base_query_fields)

search_task_fields = ns.model('SearchTask', base_search_task_fields)

add_task_fields = ns.model('AddTask', {
    'name': fields.String(required=True, example="task name", description="Task name"),
    'target': fields.String(required=True, example="www.freebuf.com", description="Target"),
    "domain_brute": fields.Boolean(example=True),
    'domain_brute_type': fields.String(example="test"),
    "port_scan_type": fields.String(example="test", description="Port scan type"),
    "port_scan": fields.Boolean(example=True),
    "service_detection": fields.Boolean(example=False),
    "service_brute": fields.Boolean(example=False),
    "os_detection": fields.Boolean(example=False),
    "site_identify": fields.Boolean(example=False),
    "site_capture": fields.Boolean(example=False),
    "file_leak": fields.Boolean(example=False),
    "search_engines": fields.Boolean(example=False),
    "site_spider": fields.Boolean(example=False),
    "harrier_search": fields.Boolean(example=False),
    "alt_dns": fields.Boolean(example=False),
    "ssl_cert": fields.Boolean(example=False),
    "dns_query_plugin": fields.Boolean(example=False, default=False),
    "skip_scan_cdn_ip": fields.Boolean(example=False, default=False),
    "nuclei_scan": fields.Boolean(description="nuclei scan", example=False, default=False),
    "findvhost": fields.Boolean(example=False, default=False),
    "web_info_hunter": fields.Boolean(example=False, default=False, description="Information gathering from web JS"),
})


@ns.route('/')
class HarrierTask(HarrierResource):
    parser = get_harrier_parser(search_task_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query task information
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='task')

        return data

    @auth
    @ns.expect(add_task_fields)
    def post(self):
        """
        Submit task
        """
        args = self.parse_args(add_task_fields)

        name = args.pop('name')
        target = args.pop('target')

        try:
            task_data_list = submit_task_task(target=target, name=name, options=args)
        except Exception as e:
            logger.exception(e)
            return utils.build_ret(ErrorMsg.Error, {"error": str(e)})

        if not task_data_list:
            return utils.build_ret(ErrorMsg.TaskTargetIsEmpty, {"target": target})

        ret = {
            "code": 200,
            "message": "success",
            "items": task_data_list
        }
        return ret

        # return utils.build_ret(ErrorMsg.Success, {"items": task_data_list})


batch_stop_fields = ns.model('BatchStop',  {
    "task_id": fields.List(fields.String(description="Task ID"), required=True),
})


@ns.route('/batch_stop/')
class BatchStopTask(HarrierResource):

    @auth
    @ns.expect(batch_stop_fields)
    def post(self):
        """
        Batch stop tasks
        """
        args = self.parse_args(batch_stop_fields)
        task_id_list = args.pop("task_id", [])

        for task_id in task_id_list:
            if not task_id:
                continue
            stop_task(task_id)

        """Return success directly here"""
        return utils.build_ret(ErrorMsg.Success, {})


@ns.route('/stop/<string:task_id>')
class StopTask(HarrierResource):
    @auth
    def get(self, task_id=None):
        """
        Stop task
        """
        return stop_task(task_id=task_id)


def stop_task(task_id):
    """Stop task"""
    done_status = [TaskStatus.DONE, TaskStatus.STOP, TaskStatus.ERROR]

    task_data = utils.conn_db('task').find_one({'_id': ObjectId(task_id)})
    if not task_data:
        return utils.build_ret(ErrorMsg.NotFoundTask, {"task_id": task_id})

    if task_data["status"] in done_status:
        return utils.build_ret(ErrorMsg.TaskIsDone, {"task_id": task_id})

    celery_id = task_data.get("celery_id")
    if not celery_id:
        return utils.build_ret(ErrorMsg.CeleryIdNotFound, {"task_id": task_id})

    control = celerytask.celery.control

    control.revoke(celery_id, signal='SIGTERM', terminate=True)

    # Force-update the status here anyway
    update_data = {"$set": {"status": TaskStatus.STOP, "end_time": utils.curr_date()}}
    utils.conn_db('task').update_one({'_id': ObjectId(task_id)}, update_data)

    return utils.build_ret(ErrorMsg.Success, {"task_id": task_id})


delete_task_fields = ns.model('DeleteTask',  {
    'del_task_data': fields.Boolean(required=False, default=False, description="Whether to delete task data"),
    'task_id': fields.List(fields.String(required=True, description="Task ID"))
})


@ns.route('/delete/')
class DeleteTask(HarrierResource):
    @auth
    @ns.expect(delete_task_fields)
    def post(self):
        """
        Delete task
        """
        done_status = [TaskStatus.DONE, TaskStatus.STOP, TaskStatus.ERROR]
        args = self.parse_args(delete_task_fields)
        task_id_list = args.pop('task_id')
        del_task_data_flag = args.pop('del_task_data')

        for task_id in task_id_list:
            task_data = utils.conn_db('task').find_one({'_id': ObjectId(task_id)})
            if not task_data:
                return utils.build_ret(ErrorMsg.NotFoundTask, {"task_id": task_id})

            if task_data["status"] not in done_status:
                return utils.build_ret(ErrorMsg.TaskIsRunning, {"task_id": task_id})

        for task_id in task_id_list:
            utils.conn_db('task').delete_many({'_id': ObjectId(task_id)})
            table_list = ["cert", "domain", "fileleak","ip", "service",
                          "site", "url", "vuln", "cip", "npoc_service", "wih", "nuclei_result", "stat_finger"]

            if del_task_data_flag:
                for name in table_list:
                    utils.conn_db(name).delete_many({'task_id': task_id})

        return utils.build_ret(ErrorMsg.Success, {"task_id": task_id_list})


sync_task_fields = ns.model('SyncTask',  {
    'task_id': fields.String(required=True, description="Task ID"),
    'scope_id': fields.String(required=True, description="Asset scope ID"),
})


@ns.route('/sync/')
class SyncTask(HarrierResource):
    @auth
    @ns.expect(sync_task_fields)
    def post(self):
        """
        Sync task results to an asset group
        """
        done_status = [TaskStatus.DONE, TaskStatus.STOP, TaskStatus.ERROR]
        args = self.parse_args(sync_task_fields)
        task_id = args.pop('task_id')
        scope_id = args.pop('scope_id')

        query = {'_id': ObjectId(task_id)}
        task_data = utils.conn_db('task').find_one(query)
        if not task_data:
            return utils.build_ret(ErrorMsg.NotFoundTask, {"task_id": task_id})

        asset_scope_data = utils.conn_db('asset_scope').find_one({'_id': ObjectId(scope_id)})
        if not asset_scope_data:
            return utils.build_ret(ErrorMsg.NotFoundScopeID, {"task_id": task_id})

        if task_data.get("type") != "domain":
            return utils.build_ret(ErrorMsg.TaskTypeIsNotDomain, {"task_id": task_id})

        if not utils.is_in_scopes(task_data["target"], asset_scope_data["scope_array"]):
            return utils.build_ret(ErrorMsg.TaskTargetNotInScope, {"task_id": task_id})

        if task_data["status"] not in done_status:
            return utils.build_ret(ErrorMsg.TaskIsRunning, {"task_id": task_id})

        task_sync_status = task_data.get("sync_status", TaskSyncStatus.DEFAULT)

        if task_sync_status not in [TaskSyncStatus.DEFAULT, TaskSyncStatus.ERROR]:
            return utils.build_ret(ErrorMsg.TaskSyncDealing, {"task_id": task_id})

        task_data["sync_status"] = TaskSyncStatus.WAITING

        options = {
            "celery_action": CeleryAction.DOMAIN_TASK_SYNC_TASK,
            "data": {
                "task_id": task_id,
                "scope_id": scope_id
            }
        }
        celerytask.harrier_task.delay(options=options)

        conn('task').find_one_and_replace(query, task_data)

        return utils.build_ret(ErrorMsg.Success, {"task_id": task_id})


sync_scope_fields = ns.model('SyncScope',  {
    'target': fields.String(required=True, description="Target to sync"),
})


# ******* Find the asset group ID to sync to by target *********
@ns.route('/sync_scope/')
class Target2Scope(HarrierResource):
    parser = get_harrier_parser(sync_scope_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Reverse lookup of asset groups from a target
        """
        args = self.parser.parse_args()
        target = args.pop("target")
        if not utils.is_valid_domain(target):
            return utils.build_ret(ErrorMsg.DomainInvalid, {"target": target})

        args["scope_array"] = utils.get_fld(target)
        args["size"] = 100
        args["order"] = "_id"

        data = self.build_data(args=args, collection='asset_scope')
        ret = []
        for item in data["items"]:
            if utils.is_in_scopes(target, item["scope_array"]):
                ret.append(item)

        data["items"] = ret
        data["total"] = len(ret)
        return data


'''Fields for dispatching a task via policy'''
task_by_policy_fields = ns.model('TaskByPolicy', {
    "name": fields.String(description="Task name", default=True, required=True),
    "task_tag": fields.String(description="Task type tag", enum=["task", "risk_cruising"], required=True),
    "target": fields.String(description="Task target", example="", required=False),
    "policy_id": fields.String(description="Policy ID", example="603c65316591e73dd717d176", required=True),
    "result_set_id": fields.String(description="Result set ID", example="603c65316591e73dd717d176", required=False)
})


# ******* Dispatch a task with the specified policy ID *********
@ns.route('/policy/')
class TaskByPolicy(HarrierResource):
    @auth
    @ns.expect(task_by_policy_fields)
    def post(self):
        """
        Dispatch task via policy
        """
        args = self.parse_args(task_by_policy_fields)
        name = args.pop("name")
        policy_id = args.pop("policy_id")
        target = args.pop("target")
        task_tag = args.pop("task_tag")
        result_set_id = args.pop("result_set_id")
        task_tag_enum = task_by_policy_fields["task_tag"].enum

        if task_tag not in task_tag_enum:
            return utils.build_ret("task_tag must be one of {}".format(",".join(task_tag_enum)), {})

        options = get_options_by_policy_id(policy_id, task_tag)

        if not options:
            return utils.build_ret(ErrorMsg.PolicyIDNotFound, {"policy_id": policy_id})

        task_data_list = []
        try:
            if task_tag == TaskTag.TASK:
                # For asset discovery tasks, validate the asset group linked via the policy
                related_scope_id = options.get("related_scope_id", "")
                if related_scope_id:
                    scope_data = get_scope_by_scope_id(scope_id=related_scope_id)
                    if not scope_data:
                        return utils.build_ret(ErrorMsg.NotFoundScopeID, {"scope_id": related_scope_id})
                    
                    check_target_in_scope(target=target, scope_list=scope_data["scope_array"])

                task_data_list = submit_task_task(target=target, name=name, options=options)
                if not task_data_list:
                    return utils.build_ret(ErrorMsg.TaskTargetIsEmpty, {"target": target})

            if task_tag == TaskTag.RISK_CRUISING:
                if result_set_id:
                    query = {"_id": ObjectId(result_set_id)}
                    item = utils.conn_db('result_set').find_one(query, {"total": 1})
                    if not item:
                        return utils.build_ret(ErrorMsg.ResultSetIDNotFound, {"result_set_id": result_set_id})

                    target_len = item["total"]

                    if target_len == 0:
                        return utils.build_ret(ErrorMsg.ResultSetIsEmpty, {"result_set_id": result_set_id})

                    options["result_set_id"] = result_set_id
                    options["result_set_len"] = target_len

                    task_data_list = submit_risk_cruising(target=target, name=name, options=options)
                    if not task_data_list:
                        return utils.build_ret(ErrorMsg.Error, {"result_set_id": result_set_id})

                else:
                    task_data_list = submit_risk_cruising(target=target, name=name, options=options)
                    if not task_data_list:
                        return utils.build_ret(ErrorMsg.TaskTargetIsEmpty, {"target": target})
        except Exception as e:
            logger.exception(e)
            return utils.build_ret(ErrorMsg.Error, {"error": str(e)})

        return utils.build_ret(ErrorMsg.Success, {"items": task_data_list})


restart_task_fields = ns.model('DeleteTask',  {
    'task_id': fields.List(fields.String(required=True, description="Task ID"))
})


# ******* Re-dispatch task feature *********
@ns.route('/restart/')
class TaskRestart(HarrierResource):
    @auth
    @ns.expect(restart_task_fields)
    def post(self):
        """
        Restart task
        """
        done_status = [TaskStatus.DONE, TaskStatus.STOP, TaskStatus.ERROR]
        args = self.parse_args(restart_task_fields)
        task_id_list = args.pop('task_id')

        try:
            for task_id in task_id_list:
                task_data = get_task_data(task_id)
                if not task_data:
                    return utils.build_ret(ErrorMsg.NotFoundTask, {"task_id": task_id})

                if task_data["status"] not in done_status:
                    return utils.build_ret(ErrorMsg.TaskIsRunning, {"task_id": task_id})

                restart_task(task_id)

        except Exception as e:
            return utils.build_ret(ErrorMsg.Error, {"error": str(e)})

        return utils.build_ret(ErrorMsg.Success, {"task_id": task_id_list})


