import bson
import re
from app import utils
from app.modules import TaskStatus, TaskTag, TaskType, CeleryAction

logger = utils.get_logger()


def target2list(target):
    target = target.strip().lower()
    target_lists = re.split(r",|\s", target)
    # Remove empty strings
    target_lists = list(filter(None, target_lists))
    target_lists = list(set(target_lists))

    return target_lists


def get_ip_domain_list(target):
    target_lists = target2list(target)
    ip_list = set()
    domain_list = set()
    for item in target_lists:
        if not item:
            continue

        if utils.is_vaild_ip_target(item):
            if not utils.not_in_black_ips(item):
                raise Exception("{} is in the IP blacklist".format(item))
            ip_list.add(item)

        elif utils.domain.is_forbidden_domain(item):
            raise Exception("{} is in the forbidden domain list".format(item))

        elif utils.is_valid_domain(item):
            if utils.check_domain_black(item):
                raise Exception("{} is in the system blacklist".format(item))

            domain_list.add(item)

        elif utils.is_valid_fuzz_domain(item):
            domain_list.add(item)
        else:
            raise Exception("{} invalid target".format(item))

    return ip_list, domain_list


def build_task_data(task_name, task_target, task_type, task_tag, options):

    # Check whether it is an IP task, domain task, etc.
    avail_task_type = [TaskType.IP, TaskType.DOMAIN, TaskType.RISK_CRUISING]
    if task_type not in avail_task_type:
        raise Exception("{} invalid task_type".format(task_type))

    # Check whether it is a risk cruising task, etc.
    avail_task_tag = [TaskTag.RISK_CRUISING, TaskTag.MONITOR, TaskTag.TASK]
    if task_tag not in avail_task_tag:
        raise Exception("{} invalid task_tag".format(task_type))

    if not isinstance(options, dict):
        raise Exception("{} is not a dict".format(options))

    options_cp = options.copy()

    # Disable the following options for IP tasks
    if task_type == TaskType.IP:
        disable_options = {
            "domain_brute": False,
            "alt_dns": False,
            "dns_query_plugin": False,
            "harrier_search": False
        }
        options_cp.update(disable_options)

    task_data = {
        'name': task_name,
        'target': task_target,
        'start_time': '-',
        'status': TaskStatus.WAITING,
        'type': task_type,
        "task_tag": task_tag,
        'options': options_cp,
        "end_time": "-",
        "service": [],
        "celery_id": ""
    }

    # Handle risk cruising tasks separately
    if task_tag == TaskType.RISK_CRUISING:
        poc_config = options.get("poc_config", [])

        if options.get("result_set_id"):
            result_set_id = options.pop("result_set_id")
            result_set_len = options.pop("result_set_len")
            target_field = "目标：{}， PoC：{}".format(result_set_len, len(poc_config))
            task_data["result_set_id"] = result_set_id
        else:
            target_field = "目标：{}， PoC：{}".format(len(task_target), len(poc_config))
            task_data["cruising_target"] = task_target

        task_data["target"] = target_field

    return task_data


def submit_task(task_data):
    from app import celerytask

    target = task_data["target"]
    utils.conn_db('task').insert_one(task_data)
    task_id = str(task_data.pop("_id"))
    task_data["task_id"] = task_id

    celery_action = ""
    type_map_action = {
        TaskType.DOMAIN: CeleryAction.DOMAIN_TASK,
        TaskType.IP: CeleryAction.IP_TASK,
        TaskType.RISK_CRUISING: CeleryAction.RUN_RISK_CRUISING,
        TaskType.ASSET_SITE_UPDATE: CeleryAction.ASSET_SITE_UPDATE,
        TaskType.FOFA: CeleryAction.FOFA_TASK,
        TaskType.ASSET_SITE_ADD: CeleryAction.ADD_ASSET_SITE_TASK,
        TaskType.ASSET_WIH_UPDATE: CeleryAction.ASSET_WIH_UPDATE,
    }

    task_type = task_data["type"]
    if task_type in type_map_action:
        celery_action = type_map_action[task_type]

    assert celery_action

    task_options = {
        "celery_action": celery_action,
        "data": task_data
    }

    try:
        celery_id = celerytask.harrier_task.delay(options=task_options)
        logger.info("target:{} task_id:{} celery_id:{}".format(target, task_id, celery_id))

        values = {"$set": {"celery_id": str(celery_id)}}
        task_data["celery_id"] = str(celery_id)
        utils.conn_db('task').update_one({"_id": bson.ObjectId(task_id)}, values)

    except Exception as e:
        utils.conn_db('task').delete_one({"_id": bson.ObjectId(task_id), "status": TaskStatus.WAITING})
        logger.info("dispatch failed {}".format(target))
        raise e

    return task_data


# Issue tasks directly from the targets
def submit_task_task(target, name, options):
    task_data_list = []

    ip_list, domain_list = get_ip_domain_list(target)

    if ip_list:
        ip_target = " ".join(ip_list)
        task_data = build_task_data(task_name=name, task_target=ip_target,
                                    task_type=TaskType.IP, task_tag=TaskTag.TASK,
                                    options=options)

        task_data = submit_task(task_data)
        task_data_list.append(task_data)

    if domain_list:
        for domain_target in domain_list:
            task_data = build_task_data(task_name=name, task_target=domain_target,
                                        task_type=TaskType.DOMAIN, task_tag=TaskTag.TASK,
                                        options=options)
            task_data = submit_task(task_data)
            task_data_list.append(task_data)

    return task_data_list


# Issue a risk cruising task
def submit_risk_cruising(target, name, options):
    target_lists = target2list(target)
    task_data_list = []
    task_data = build_task_data(task_name=name, task_target=target_lists,
                                task_type=TaskType.RISK_CRUISING, task_tag=TaskTag.RISK_CRUISING,
                                options=options)

    task_data = submit_task(task_data)
    task_data_list.append(task_data)

    return task_data_list


def submit_add_asset_site_task(task_name: str, target: list, options: dict) -> dict:
    task_data = {
        'name': task_name,
        'target': "站点：{}".format(len(target)),
        'start_time': '-',
        'status': TaskStatus.WAITING,
        'type': TaskType.ASSET_SITE_ADD,
        "task_tag": TaskTag.RISK_CRUISING,
        'options': options,
        "end_time": "-",
        "service": [],
        "cruising_target": target,
        "celery_id": ""
    }
    task_data = submit_task(task_data)
    return task_data


def get_task_data(task_id):
    task_data = utils.conn_db('task').find_one({'_id': bson.ObjectId(task_id)})
    return task_data


def restart_task(task_id):
    name_pre = "rerun-"
    task_data = get_task_data(task_id)
    if not task_data:
        raise Exception("task_id not found: {}".format(task_id))

    # Initialize some basic fields
    task_data.pop("_id")
    task_data["start_time"] = "-"
    task_data["status"] = TaskStatus.WAITING
    task_data["end_time"] = "-"
    task_data["service"] = []
    task_data["celery_id"] = ""
    if "statistic" in task_data:
        task_data.pop("statistic")

    name = task_data["name"]
    if name_pre not in name:
        task_data["name"] = name_pre + name

    task_type = task_data["type"]
    task_tag = task_data.get("task_tag", "")

    # Handle special cases separately
    if task_type == TaskType.RISK_CRUISING and task_tag == TaskTag.RISK_CRUISING:
        if task_data.get("result_set_id"):
            raise Exception("task_id: {}, this task type cannot be re-run".format(task_id))

    # Re-issuing a monitor task is tricky
    if task_type == TaskType.DOMAIN and task_tag == TaskTag.MONITOR:
        raise Exception("task_id: {}, this task type cannot be re-run".format(task_id))

    elif task_type == TaskType.IP and task_data["options"].get("scope_id"):
        raise Exception("task_id: {}, this task type cannot be re-run".format(task_id))

    submit_task(task_data)

    return task_data
