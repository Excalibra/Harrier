from .ipInfo import PortInfo, IPInfo
from .baseInfo import BaseInfo
from .domainInfo import DomainInfo
from .pageInfo import PageInfo
from .wihRecord import WihRecord
from app.config import Config


class ScanPortType:
    TEST = Config.TOP_10
    TOP100 = Config.TOP_100
    TOP1000 = Config.TOP_1000
    ALL = "0-65535"


class DomainDictType:
    TEST = Config.DOMAIN_DICT_TEST
    BIG = Config.DOMAIN_DICT_2W


class CollectSource:
    DOMAIN_BRUTE = "domain_brute"
    BAIDU = "baidu"
    ALTDNS = "alt_dns"
    HARRIER = "harrier"
    SITESPIDER = "site_spider"
    SEARCHENGINE = "search_engine"
    MONITOR = "monitor"


class TaskStatus:
    WAITING = "waiting"
    DONE = "done"
    ERROR = "error"
    STOP = "stop"


class TaskScheduleStatus:
    DONE = "done"
    SCHEDULED = "scheduled"
    STOP = "stop"
    ERROR = "error"


class TaskTag:
    """Task tag"""

    """Task with asset discovery"""
    TASK = "task"

    """Domain monitor task"""
    MONITOR = "monitor"

    """Risk cruising task"""
    RISK_CRUISING = "risk_cruising"


class TaskType:
    """Task target type"""

    """IP task"""
    IP = "ip"

    """Domain task"""
    DOMAIN = "domain"

    """Site, risk cruising"""
    RISK_CRUISING = "risk_cruising"

    """Asset site update"""
    ASSET_SITE_UPDATE = "asset_site_update"

    """Fofa task"""
    FOFA = "fofa"

    """Asset site add"""
    ASSET_SITE_ADD = "asset_site_add"

    """Asset WIH update"""
    ASSET_WIH_UPDATE = "asset_wih_update"


class SiteAutoTag:
    ENTRY = "入口"
    INVALID = "无效"


class TaskSyncStatus:
    WAITING = "waiting"
    RUNNING = "running"
    ERROR = "error"
    DEFAULT = "default"


class SchedulerStatus:
    RUNNING = "running"
    STOP = "stop"


class AssetScopeType:
    DOMAIN = "domain"
    IP = "ip"


class PoCCategory:
    POC = "漏洞PoC"
    SNIFFER = "协议识别"
    SYSTEM_BRUTE = "服务弱口令"
    WEBB_RUTE = "应用弱口令"


class WebSiteFetchOption:
    # Optional feature options for WEB sites
    SITE_CAPTURE = "site_capture"
    SEARCH_ENGINES = "search_engines"
    SITE_SPIDER = "site_spider"
    FILE_LEAK = "file_leak"
    POC_RUN = "poc_config"
    SITE_IDENTIFY = "site_identify"
    NUCLEI_SCAN = "nuclei_scan"  # nuclei scan
    Info_Hunter = "web_info_hunter"  # call WebInfoHunter on JS


class WebSiteFetchStatus:
    # Possible statuses of a WEB site task
    FETCH_SITE = "fetch_site"
    SITE_CAPTURE = "site_capture"
    SEARCH_ENGINES = "search_engines"
    SITE_SPIDER = "site_spider"
    FILE_LEAK = "file_leak"
    SITE_IDENTIFY = "site_identify"
    POC_RUN = "poc_run"
    NUCLEI_SCAN = "nuclei_scan"
    Info_Hunter = "web_info_hunter"  # call WebInfoHunter on JS


class CeleryRoutingKey:
    ASSET_TASK = "harriertask"
    GITHUB_TASK = "harriergithub"


class CeleryAction:
    """celery_action field of a celery task"""

    """Regular IP task"""
    IP_TASK = "ip_task"

    """Regular domain task"""
    DOMAIN_TASK = "domain_task"

    """Domain monitor task"""
    DOMAIN_EXEC_TASK = "domain_exec_task"

    """IP type monitor task"""
    IP_EXEC_TASK = "ip_exec_task"

    """Sync existing task"""
    DOMAIN_TASK_SYNC_TASK = "domain_task_sync_task"

    """PoC run task"""
    RUN_RISK_CRUISING = "run_risk_cruising"

    """Fofa query task"""
    FOFA_TASK = "fofa_task"

    """Github leak task"""
    GITHUB_TASK_TASK = "github_task_task"

    """Github leak monitor task"""
    GITHUB_TASK_MONITOR = "github_task_monitor"

    """Asset site update task"""
    ASSET_SITE_UPDATE = "asset_site_update"

    """Asset site add site"""
    ADD_ASSET_SITE_TASK = "add_asset_site_task"

    """Asset WIH update task"""
    ASSET_WIH_UPDATE = "asset_wih_update"


error_map = {
    'CeleryIdNotFound': {
        "message": "Celery id not found",
        "code": 102,
    },
    'NotFoundTask': {
        "message": "Task not found",
        "code": 103,
    },
    "TaskIsRunning": {
        "message": "Task is running",
        "code": 104,
    },
    "TaskIsDone": {
        "message": "Task is already done",
        "code": 105,
    },
    "Success": {
        "message": "success",
        "code": 200,
    },
    "NotLogin": {
        "message": "Not logged in",
        "code": 401,
    },
    "NotFoundScopeID": {
        "message": "Asset scope ID not found",
        "code": 601,
    },
    "NotFoundScope": {
        "message": "Corresponding asset scope not found",
        "code": 602,
    },
    "ExistScope": {
        "message": "Corresponding asset scope already exists",
        "code": 603,
    },
    "IntervalLessThan3600": {
        "message": "Monitor task interval cannot be less than 6 hours (21600s)",
        "code": 700,
    },
    "DomainNotFoundViaScope": {
        "message": "Domain is not in the given asset scope",
        "code": 701,
    },
    "DomainViaJob": {
        "message": "A monitor task already exists for the domain in the given asset scope",
        "code": 699,
    },
    "DomainNotViaJob": {
        "message": "No monitor task exists for the domain in the given asset scope",
        "code": 698,
    },
    "JobNotFound": {
        "message": "Monitor task not found",
        "code": 702,
    },
    "DomainInvalid": {
        "message": "Invalid domain",
        "code": 703,
    },
    "TargetInvalid": {
        "message": "Invalid task target",
        "code": 704,
    },
    "IPInBlackIps": {
        "message": "Target IP is not allowed to be issued",
        "code": 705,
    },
    "TaskTargetIsEmpty": {
        "message": "Task target is empty",
        "code": 706,
    },
    "TaskSyncDealing": {
        "message": "Task asset sync in progress",
        "code": 801,
    },
    "TaskTypeIsNotDomain": {
        "message": "Not a domain discovery task",
        "code": 802,
    },
    "TaskTargetNotInScope": {
        "message": "Task target is not in the asset group",
        "code": 802,
    },
    "DomainInScope": {
        "message": "Domain already exists in the specified asset group",
        "code": 803,
    },
    "URLInvalid": {
        "message": "Invalid URL",
        "code": 804,
    },
    "SiteURLNotDomain": {
        "message": "URL is not of domain type",
        "code": 805,
    },
    "SiteInScope": {
        "message": "Site already exists in the specified asset",
        "code": 806,
    },
    "DomainNotFoundNotInScope": {
            "message": "No domain available to add was found",
            "code": 807,
    },
    "SchedulerStatusNotRunning": {
        "message": "Monitor task is not in running status",
        "code": 901,
    },
    "SchedulerStatusNotStop": {
        "message": "Monitor task is not in stopped status",
        "code": 902,
    },
    "ResultSetIDNotFound": {
        "message": "Result set ID not found",
        "code": 1001,
    },
    "ResultSetIsEmpty": {
        "message": "Result set target is empty",
        "code": 1002,
    },
    "PoCTargetIsEmpty": {
        "message": "PoC task target is empty",
        "code": 1003,
    },
    "QueryResultIsEmpty": {
        "message": "Query result is empty",
        "code": 1004,
    },
    "PolicyIDNotFound": {
        "message": "Policy does not exist",
        "code": 1100,
    },
    "RiskCruisingPoCConfigIsEmpty": {
        "message": "The policy PoC config field selected for the risk cruising task cannot be empty",
        "code": 1101,
    },
    "BruteTaskBruteConfigIsEmpty": {
        "message": "The policy brute config field selected for the brute task cannot be empty",
        "code": 1102,
    },
    "PolicyDataIsEmpty": {
        "message": "Policy data is empty",
        "code": 1103,
    },
    "FofaConnectError": {
        "message": "Failed to connect to Fofa API",
        "code": 1201,
    },
    "FofaKeyError": {
        "message": "Fofa authentication info error",
        "code": 1202,
    },
    "FofaResultEmpty": {
        "message": "Fofa query result is empty",
        "code": 1203,
    },
    "SiteIdNotFound": {
        "message": "Site not found",
        "code": 1300,
    },
    "SiteTagIsExist": {
        "message": "Site tag already exists",
        "code": 1301,
    },
    "SiteTagNotExist": {
        "message": "Site tag not found",
        "code": 1302,
    },
    "ScopeTypeIsNotIP": {
        "message": "Asset group IP scope is invalid",
        "code": 1303,
    },
    "IsForbiddenDomain": {
        "message": "Contained in forbidden domains",
        "code": 1401,
    },
    "RuleInvalid": {
        "message": "Invalid rule",
        "code": 1402,
    },
    "GithubKeywordEmpty": {
        "message": "Keyword is empty",
        "code": 1501,
    },
    "Error": {
        "message": "System error",
        "code": 500,
    },
    "CronError": {
        "message": "Cron expression error",
        "code": 1502,
    },
    "IPInvalid": {
        "message": "Invalid IP",
        "code": 1503,
    },
    "IPNotFoundViaScope": {
        "message": "Not in the given asset scope",
        "code": 1504,
    },
    "PortCustomInvalid": {
        "message": "Custom port info error",
        "code": 1506,
    },
    "TaskScheduleTypeInvalid": {
        "message": "Scheduled task type error",
        "code": 1601,
    },
    "DateInvalid": {
        "message": "Time error",
        "code": 1602,
    },
    "TaskTagInvalid": {
        "message": "Task type error",
        "code": 1603,
    },
    "FutureDateInvalid": {
        "message": "The time has already passed",
        "code": 1604,
    },
    "TaskScheduleNotFound": {
        "message": "Scheduled task not found",
        "code": 1605,
    },
    "DomainSiteViaJob": {
        "message": "Asset site update task already exists",
        "code": 1607,
    },
    "AddAssetSiteNotSupportIP": {
        "message": "Adding sites to an IP asset group is not supported",
        "code": 1608,
    },
    "RuleAlreadyExists": {
        "message": "Rule already exists",
        "code": 1609,
    },
    "ExcludePortsInvalid": {
        "message": "nmap exclude ports error",
        "code": 1610,
    },
}


class ErrorMsg:
    CeleryIdNotFound = error_map["CeleryIdNotFound"]
    NotFoundTask = error_map["NotFoundTask"]
    TaskIsRunning = error_map["TaskIsRunning"]
    TaskIsDone = error_map["TaskIsDone"]
    Success = error_map["Success"]
    NotLogin = error_map["NotLogin"]
    NotFoundScopeID = error_map["NotFoundScopeID"]
    NotFoundScope = error_map["NotFoundScope"]
    ExistScope = error_map["ExistScope"]
    IntervalLessThan3600 = error_map["IntervalLessThan3600"]
    DomainNotFoundViaScope = error_map["DomainNotFoundViaScope"]
    DomainViaJob = error_map["DomainViaJob"]
    DomainNotViaJob = error_map["DomainNotViaJob"]
    JobNotFound = error_map["JobNotFound"]
    DomainInvalid = error_map["DomainInvalid"]
    TargetInvalid = error_map["TargetInvalid"]
    IPInBlackIps = error_map["IPInBlackIps"]
    TaskSyncDealing = error_map["TaskSyncDealing"]
    TaskTypeIsNotDomain = error_map["TaskTypeIsNotDomain"]
    TaskTargetNotInScope = error_map["TaskTargetNotInScope"]
    DomainInScope = error_map["DomainInScope"]
    SiteInScope = error_map["SiteInScope"]
    URLInvalid = error_map["URLInvalid"]
    SiteURLNotDomain = error_map["SiteURLNotDomain"]
    SchedulerStatusNotRunning = error_map["SchedulerStatusNotRunning"]
    SchedulerStatusNotStop = error_map["SchedulerStatusNotStop"]
    DomainNotFoundNotInScope = error_map["DomainNotFoundNotInScope"]
    ResultSetIDNotFound = error_map["ResultSetIDNotFound"]
    ResultSetIsEmpty = error_map["ResultSetIsEmpty"]
    PoCTargetIsEmpty = error_map["PoCTargetIsEmpty"]
    QueryResultIsEmpty = error_map["QueryResultIsEmpty"]
    TaskTargetIsEmpty = error_map["TaskTargetIsEmpty"]
    PolicyIDNotFound = error_map["PolicyIDNotFound"]
    PolicyDataIsEmpty = error_map["PolicyDataIsEmpty"]
    RiskCruisingPoCConfigIsEmpty = error_map["RiskCruisingPoCConfigIsEmpty"]
    BruteTaskBruteConfigIsEmpty = error_map["BruteTaskBruteConfigIsEmpty"]
    FofaConnectError = error_map["FofaConnectError"]
    FofaKeyError = error_map["FofaKeyError"]
    FofaResultEmpty = error_map["FofaResultEmpty"]
    SiteIdNotFound = error_map["SiteIdNotFound"]
    SiteTagIsExist = error_map["SiteTagIsExist"]
    SiteTagNotExist = error_map["SiteTagNotExist"]
    ScopeTypeIsNotIP = error_map["ScopeTypeIsNotIP"]
    IsForbiddenDomain = error_map["IsForbiddenDomain"]
    RuleInvalid = error_map["RuleInvalid"]
    GithubKeywordEmpty = error_map["GithubKeywordEmpty"]
    Error = error_map["Error"]
    CronError = error_map["CronError"]
    IPInvalid = error_map["IPInvalid"]
    IPNotFoundViaScope = error_map["IPNotFoundViaScope"]
    PortCustomInvalid = error_map["PortCustomInvalid"]
    TaskScheduleTypeInvalid = error_map["TaskScheduleTypeInvalid"]
    DateInvalid = error_map["DateInvalid"]
    TaskTagInvalid = error_map["TaskTagInvalid"]
    FutureDateInvalid = error_map["FutureDateInvalid"]
    TaskScheduleNotFound = error_map["TaskScheduleNotFound"]
    DomainSiteViaJob = error_map["DomainSiteViaJob"]
    AddAssetSiteNotSupportIP = error_map["AddAssetSiteNotSupportIP"]
    RuleAlreadyExists = error_map["RuleAlreadyExists"]
    ExcludePortsInvalid = error_map["ExcludePortsInvalid"]
