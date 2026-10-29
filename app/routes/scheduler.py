from bson import ObjectId
from flask_restx import Resource, Api, reqparse, fields, Namespace
from app.utils import get_logger, auth, truncate_string
from app.modules import ErrorMsg
from . import base_query_fields, HarrierResource, get_harrier_parser
from app import scheduler as app_scheduler, utils
from app.modules import SchedulerStatus, AssetScopeType, TaskTag
from app.helpers import (
    get_options_by_policy_id,
    have_same_site_update_monitor,
    have_same_wih_update_monitor
)

ns = Namespace('scheduler', description="Asset monitoring task information")

base_search_fields = {
    '_id': fields.String(description="Monitor task job_id"),
    'domain': fields.String(description="Domain to monitor"),
    'scope_id': fields.String(description="Asset group scope ID"),
    'interval': fields.String(description="Run interval in seconds"),
    'next_run_time': fields.String(description="Next run timestamp"),
    'next_run_date': fields.Integer(description="Next run date"),
    'last_run_time': fields.Integer(description="Last run timestamp"),
    'last_run_date': fields.String(description="Last run date"),
    'run_number': fields.String(description="Run count"),
    "name": fields.String(description="Name")
}

base_search_fields.update(base_query_fields)


@ns.route('/')
class HarrierScheduler(HarrierResource):
    parser = get_harrier_parser(base_search_fields, location='args')

    @auth
    @ns.expect(parser)
    def get(self):
        """
        Query monitor tasks
        """
        args = self.parser.parse_args()
        data = self.build_data(args=args, collection='scheduler')

        return data


add_scheduler_fields = ns.model('addScheduler', {
    "scope_id": fields.String(required=True, description="Asset scope to add"),
    "domain": fields.String(required=True, description="Domain"),  # multiple domains can be separated by commas
    "interval": fields.Integer(description="Interval in seconds"),  # unit: seconds
    "name": fields.String(description="Monitor task name"),  # auto-generated if empty
    "policy_id": fields.String(description="Policy ID")
})


@ns.route('/add/')
class AddHarrierScheduler(HarrierResource):

    @auth
    @ns.expect(add_scheduler_fields)
    def post(self):
        """
        Add a periodic monitor task
        """
        args = self.parse_args(add_scheduler_fields)
        scope_id = args.pop("scope_id")
        domain = args.pop("domain")
        interval = args.pop("interval")
        name = args.pop("name")
        policy_id = args.pop("policy_id", "")

        if interval < 3600 * 6:
            return utils.build_ret(ErrorMsg.IntervalLessThan3600, {"interval": interval})

        monitor_domain = utils.harrier.get_monitor_domain_by_id(scope_id)
        scope_data = utils.harrier.scope_data_by_id(scope_id)

        if not scope_data:
            return utils.build_ret(ErrorMsg.NotFoundScopeID, {"scope_id": scope_id})

        task_options = None
        if policy_id and len(policy_id) == 24:
            task_options = get_options_by_policy_id(policy_id, TaskTag.TASK)
            if task_options is None:
                return utils.build_ret(ErrorMsg.PolicyIDNotFound, {"policy_id": policy_id})

        # Asset scope type (domain or IP)
        scope_type = scope_data.get("scope_type")
        if not scope_type:
            scope_type = AssetScopeType.DOMAIN

        domains = domain.split(",")
        for x in domains:
            curr_domain = x.strip()
            if curr_domain not in scope_data["scope_array"]:
                return utils.build_ret(ErrorMsg.DomainNotFoundViaScope,
                                       {"domain": curr_domain, "scope_id": scope_id})

            if curr_domain in monitor_domain:
                return utils.build_ret(ErrorMsg.DomainViaJob,
                                       {"domain": curr_domain, "scope_id": scope_id})

        ret_data = []
        # Dispatch domain-type monitor tasks
        if scope_type == AssetScopeType.DOMAIN:
            for x in domains:
                curr_name = name
                if not name:
                    curr_name = "Monitor-{}-{}".format(scope_data["name"], x)

                curr_name = truncate_string(curr_name)

                job_id = app_scheduler.add_job(domain=x, scope_id=scope_id,
                                               options=task_options, interval=interval,
                                               name=curr_name, scope_type=scope_type)
                ret_data.append({"domain": x, "scope_id": scope_id, "job_id": job_id})

        # Dispatch IP-type monitor tasks
        if scope_type == AssetScopeType.IP:
            curr_name = name
            ip_target = " ".join(domains)
            if not name:
                curr_name = "Monitor-{}-{}".format(scope_data["name"], ip_target)

            curr_name = truncate_string(curr_name)

            job_id = app_scheduler.add_job(domain=ip_target, scope_id=scope_id,
                                           options=task_options, interval=interval,
                                           name=curr_name, scope_type=scope_type)
            ret_data.append({"domain": ip_target, "scope_id": scope_id, "job_id": job_id})

        return utils.build_ret(ErrorMsg.Success, ret_data)


delete_scheduler_fields = ns.model('deleteScheduler', {
    "job_id": fields.List(fields.String(description="Monitor task ID list"))
})


@ns.route('/delete/')
class DeleteHarrierScheduler(HarrierResource):

    @auth
    @ns.expect(delete_scheduler_fields)
    def post(self):
        """
        Delete periodic monitor tasks
        """
        args = self.parse_args(delete_scheduler_fields)
        job_id_list = args.get("job_id", [])

        ret_data = {"job_id": job_id_list}

        for job_id in job_id_list:
            item = app_scheduler.find_job(job_id)
            if not item:
                return utils.build_ret(ErrorMsg.JobNotFound, ret_data)

        for job_id in job_id_list:
            app_scheduler.delete_job(job_id)

        return utils.build_ret(ErrorMsg.Success, ret_data)


recover_scheduler_fields = ns.model('recoverScheduler', {
    "job_id": fields.String(required=True, description="Monitor task ID")
})


# There is a batch recover endpoint below; this endpoint will be removed later
@ns.route('/recover/')
class RecoverHarrierScheduler(HarrierResource):

    @auth
    @ns.expect(recover_scheduler_fields)
    def post(self):
        """
        Recover a periodic monitor task
        """
        args = self.parse_args(recover_scheduler_fields)
        job_id = args.get("job_id")

        item = app_scheduler.find_job(job_id)
        if not item:
            return utils.build_ret(ErrorMsg.JobNotFound, {"job_id": job_id})

        status = item.get("status", SchedulerStatus.RUNNING)
        if status != SchedulerStatus.STOP:
            return utils.build_ret(ErrorMsg.SchedulerStatusNotStop, {"job_id": job_id})

        app_scheduler.recover_job(job_id)

        return utils.build_ret(ErrorMsg.Success, {"job_id": job_id})


batch_recover_scheduler_fields = ns.model('batchRecoverScheduler', {
    "job_id": fields.List(fields.String(required=True, description="Monitor task ID list"))
})


@ns.route('/recover/batch')
class BatchRecoverHarrierScheduler(HarrierResource):

    @auth
    @ns.expect(batch_recover_scheduler_fields)
    def post(self):
        """
        Batch recover periodic monitor tasks
        """
        args = self.parse_args(batch_recover_scheduler_fields)
        job_id_list = args.get("job_id", [])
        for job_id in job_id_list:
            item = app_scheduler.find_job(job_id)
            if not item:
                return utils.build_ret(ErrorMsg.JobNotFound, {"job_id": job_id})

            status = item.get("status", SchedulerStatus.RUNNING)
            if status != SchedulerStatus.STOP:
                return utils.build_ret(ErrorMsg.SchedulerStatusNotStop, {"job_id": job_id})

            app_scheduler.recover_job(job_id)

        return utils.build_ret(ErrorMsg.Success, {"job_id": job_id_list})


stop_scheduler_fields = ns.model('stopScheduler', {
    "job_id": fields.String(required=True, description="Monitor task ID")
})


# There is a batch stop endpoint below; this endpoint will be removed later
@ns.route('/stop/')
class StopHarrierScheduler(HarrierResource):

    @auth
    @ns.expect(stop_scheduler_fields)
    def post(self):
        """
        Stop periodic monitor tasks
        """
        args = self.parse_args(stop_scheduler_fields)
        job_id = args.get("job_id")

        item = app_scheduler.find_job(job_id)
        if not item:
            return utils.build_ret(ErrorMsg.JobNotFound, {"job_id": job_id})

        status = item.get("status", SchedulerStatus.RUNNING)
        if status != SchedulerStatus.RUNNING:
            return utils.build_ret(ErrorMsg.SchedulerStatusNotRunning, {"job_id": job_id})

        app_scheduler.stop_job(job_id)

        return utils.build_ret(ErrorMsg.Success, {"job_id": job_id})


batch_stop_scheduler_fields = ns.model('batchStopScheduler', {
    "job_id": fields.List(fields.String(required=True, description="Monitor task ID list"))
})


@ns.route('/stop/batch')
class BatchStopHarrierScheduler(HarrierResource):

    @auth
    @ns.expect(batch_stop_scheduler_fields)
    def post(self):
        """
        Stop periodic monitor tasks
        """
        args = self.parse_args(batch_stop_scheduler_fields)
        job_id_list = args.get("job_id", [])
        for job_id in job_id_list:
            item = app_scheduler.find_job(job_id)
            if not item:
                return utils.build_ret(ErrorMsg.JobNotFound, {"job_id": job_id})

            status = item.get("status", SchedulerStatus.RUNNING)
            if status != SchedulerStatus.RUNNING:
                return utils.build_ret(ErrorMsg.SchedulerStatusNotRunning, {"job_id": job_id})

            app_scheduler.stop_job(job_id)

        return utils.build_ret(ErrorMsg.Success, {"job_id": job_id_list})


add_scheduler_site_fields = ns.model('addSchedulerSite', {
    "scope_id": fields.String(required=True, description="Asset scope id"),
    "interval": fields.Integer(description="Interval in seconds", example=3600 * 23),  # unit: seconds
    "name": fields.String(description="Monitor task name"),  # auto-generated if empty
})


@ns.route('/add/site_monitor/')
class AddSiteScheduler(HarrierResource):

    @auth
    @ns.expect(add_scheduler_site_fields)
    def post(self):
        """
        Add a site update monitor periodic task
        """
        args = self.parse_args(add_scheduler_site_fields)
        scope_id = args.pop("scope_id")
        interval = args.pop("interval")
        name = args.pop("name")

        if interval < 3600 * 6:
            return utils.build_ret(ErrorMsg.IntervalLessThan3600, {"interval": interval})

        scope_data = utils.harrier.scope_data_by_id(scope_id)

        if not scope_data:
            return utils.build_ret(ErrorMsg.NotFoundScopeID, {"scope_id": scope_id})

        if have_same_site_update_monitor(scope_id=scope_id):
            return utils.build_ret(ErrorMsg.DomainSiteViaJob, {"scope_id": scope_id,
                                                               "scope_name": scope_data['name']})

        if not name:
            name = "SiteMonitor-{}".format(scope_data["name"])

        _id = app_scheduler.add_asset_site_monitor_job(scope_id=scope_id,
                                                       name=name,
                                                       interval=interval)

        return utils.build_ret(ErrorMsg.Success, {"schedule_id": _id})


add_scheduler_wih_fields = ns.model('addSchedulerWih', {
    "scope_id": fields.String(required=True, description="Asset scope id"),
    "interval": fields.Integer(description="Interval in seconds", example=3600 * 23),  # unit: seconds
    "name": fields.String(description="Monitor task name", example=""),  # auto-generated if empty
})


@ns.route('/add/wih_monitor/')
class AddWihScheduler(HarrierResource):

    @auth
    @ns.expect(add_scheduler_wih_fields)
    def post(self):
        """
        Add a WIH update monitor periodic task
        """
        args = self.parse_args(add_scheduler_wih_fields)
        scope_id = args.pop("scope_id")
        interval = args.pop("interval")
        name = args.pop("name")

        if interval < 3600 * 6:
            return utils.build_ret(ErrorMsg.IntervalLessThan3600, {"interval": interval})

        scope_data = utils.harrier.scope_data_by_id(scope_id)

        if not scope_data:
            return utils.build_ret(ErrorMsg.NotFoundScopeID, {"scope_id": scope_id})

        if have_same_wih_update_monitor(scope_id=scope_id):
            return utils.build_ret(ErrorMsg.DomainSiteViaJob, {"scope_id": scope_id,
                                                               "scope_name": scope_data['name']})

        if not name:
            name = "WIH Monitor-{}".format(scope_data["name"])

        _id = app_scheduler.add_asset_wih_monitor_job(scope_id=scope_id,
                                                      name=name,
                                                      interval=interval)

        return utils.build_ret(ErrorMsg.Success, {"schedule_id": _id})
