import bson
from app import utils
from app.modules import TaskScheduleStatus, TaskTag
from crontab import CronTab
import time

from .policy import get_options_by_policy_id


logger = utils.get_logger()


# Scheduled task scheduling
def task_scheduler():
    items = list(utils.conn_db('task_schedule').find())
    for item in items:
        try:
            if item["status"] != TaskScheduleStatus.SCHEDULED:
                continue

            task_tag = item["task_tag"]
            should_scheduler_tag = [TaskTag.TASK, TaskTag.RISK_CRUISING]
            if task_tag not in should_scheduler_tag:
                logger.warning("not an asset discovery or risk cruising task: {} {}", item["task_tag"], str(item["_id"]))
                continue

            if item["schedule_type"] == "recurrent_scan":
                entry = CronTab(item["cron"])
                next_sec = entry.next(default_utc=False)
                if next_sec < 60 and abs(time.time() - item.get("last_run_time", 0)) > 60*3:
                    logger.info("run_recurrent_scan {} {}".format(item["target"], str(item["_id"])))
                    run_recurrent_scan(item)

            elif item["schedule_type"] == "future_scan":
                start_time = item["start_time"]
                if 0 < start_time <= time.time():
                    logger.info("run_future_scan {} {}".format(item["target"], str(item["_id"])))
                    run_future_scan(item)

        except Exception as e:
            logger.exception(e)


# Submit a scheduled task
def submit_task_schedule(item):
    from .task import submit_risk_cruising
    from .task import submit_task_task
    target = item["target"]
    task_tag = item["task_tag"]
    task_schedule_name = item["name"]
    policy_id = item["policy_id"]
    options = get_options_by_policy_id(policy_id, task_tag=task_tag)

    if not options:
        change_task_schedule_status(item["_id"], TaskScheduleStatus.ERROR)
        raise Exception("not found policy_id {}".format(policy_id))

    name = "scheduled-task-{}".format(task_schedule_name[:15])

    if item["schedule_type"] == "recurrent_scan":
        run_number = item.get("run_number", 0) + 1
        name = "periodic-task-{}-{}".format(task_schedule_name[:15], run_number)

    if task_tag == TaskTag.TASK:
        submit_task_task(target=target, name=name, options=options)
    if task_tag == TaskTag.RISK_CRUISING:
        task_data_list = submit_risk_cruising(target=target, name=name, options=options)
        if not task_data_list:
            raise Exception("not found task_data {}".format(target))


# Generate the next run time from the cron expression
def get_next_run_date(cron):
    entry = CronTab(cron)
    now_time = time.time() + 61
    next_sec = entry.next(now=now_time, default_utc=False)
    return utils.time2date(now_time + next_sec - 60)


# Trigger a recurrent scan task
def run_recurrent_scan(item):

    # Record the run time and run count
    item["next_run_date"] = get_next_run_date(item["cron"])
    item["run_number"] = item.get("run_number", 0) + 1
    item["last_run_time"] = int(time.time())
    item["last_run_date"] = utils.curr_date()

    query = {
        "_id": item["_id"]
    }
    utils.conn_db('task_schedule').find_one_and_replace(query, item)

    # Submit the task afterwards to prevent multiple runs
    submit_task_schedule(item)


# Trigger a one-time scheduled task
def run_future_scan(item):
    query = {
        "_id": item["_id"]
    }
    item["run_number"] = item.get("run_number", 0) + 1
    item["status"] = TaskScheduleStatus.DONE
    utils.conn_db('task_schedule').find_one_and_replace(query, item)

    # Submit the task afterwards to prevent multiple runs
    submit_task_schedule(item)


# Find a scheduled task
def find_task_schedule(_id):
    query = {'_id': bson.ObjectId(_id)}
    item = utils.conn_db('task_schedule').find_one(query)
    return item


# Delete a scheduled task
def remove_task_schedule(_id):
    query = {'_id': bson.ObjectId(_id)}
    result = utils.conn_db('task_schedule').delete_one(query)
    return result.deleted_count


# Change the status of a scheduled task
def change_task_schedule_status(_id, status):
    query = {'_id': bson.ObjectId(_id)}
    item = find_task_schedule(_id)
    if not item:
        return

    old_status = item["status"]

    if old_status == TaskScheduleStatus.ERROR:
        return "{} cannot change state".format(item["name"])

    if old_status == status:
        return "{} is already {} ".format(item["name"], status)

    item["status"] = status

    done_status_list = [TaskScheduleStatus.DONE,
                        TaskScheduleStatus.ERROR,
                        TaskScheduleStatus.STOP]

    if status in done_status_list:
        item["next_run_date"] = "-"

    elif status == TaskScheduleStatus.SCHEDULED:
        if item["schedule_type"] == "recurrent_scan":
            item["next_run_date"] = get_next_run_date(item["cron"])

        else:
            item["next_run_date"] = item["start_date"]

    utils.conn_db('task_schedule').find_one_and_replace(query, item)

    return item
