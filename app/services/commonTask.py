import time
from urllib.parse import urlparse
from bson import ObjectId
from app import utils
from app import services
from app.config import Config
from app.modules import CollectSource, WebSiteFetchStatus, WebSiteFetchOption
from app.services.nuclei_scan import nuclei_scan
from app.services import run_risk_cruising, BaseUpdateTask
logger = utils.get_logger()


# Common classes used by the task classes
class CommonTask(object):
    def __init__(self, task_id):
        self.task_id = task_id

    def insert_task_stat(self):
        query = {
            "_id": ObjectId(self.task_id)
        }

        stat = utils.harrier.task_statistic(self.task_id)

        logger.info("insert task stat")

        update = {"$set": {"statistic": stat}}

        utils.conn_db('task').update_one(query, update)

    def insert_finger_stat(self):
        finger_stat_map = utils.harrier.gen_stat_finger_map(self.task_id)
        logger.info("insert finger stat {}".format(len(finger_stat_map)))

        for key in finger_stat_map:
            data = finger_stat_map[key].copy()
            data["task_id"] = self.task_id
            utils.conn_db('stat_finger').insert_one(data)

    def insert_cip_stat(self):
        cip_map = utils.harrier.gen_cip_map(self.task_id)
        logger.info("insert cip stat {}".format(len(cip_map)))

        for cidr_ip in cip_map:
            item = cip_map[cidr_ip]
            ip_list = list(item["ip_set"])
            domain_list = list(item["domain_set"])

            data = {
                "cidr_ip": cidr_ip,
                "ip_count": len(ip_list),
                "ip_list": ip_list,
                "domain_count": len(domain_list),
                "domain_list": domain_list,
                "task_id": self.task_id
            }

            utils.conn_db('cip').insert_one(data)

    # asset sync
    def sync_asset(self):
        options = getattr(self, 'options', {})
        if not options:
            logger.warning("not found options {}".format(self.task_id))
            return

        related_scope_id = options.get("related_scope_id", "")
        if not related_scope_id:
            return

        if len(related_scope_id) != 24:
            logger.warning("related_scope_id len not eq 24 {}".format(self.task_id, related_scope_id))
            return

        services.sync_asset(task_id=self.task_id, scope_id=related_scope_id)

    def common_run(self):
        self.insert_finger_stat()
        self.insert_cip_stat()
        self.insert_task_stat()
        self.sync_asset()


# *** Follow-up processing for user-submitted or discovered sites
class WebSiteFetch(object):
    def __init__(self, task_id: str, sites: list, options: dict, scope_domain: list = None):
        self.task_id = task_id
        self.sites = sites  # ** targets submitted by the user
        self.options = options
        self.base_update_task = BaseUpdateTask(self.task_id)
        self.site_info_list = []  # *** results from services.fetch_site
        self.available_sites = []  # *** alive sites
        self.web_analyze_map = dict()
        self.wih_domain_set = set()  # domains from wih; already-added domains are skipped
        self.wih_record_set = set()  # records from wih; already-added records are skipped

        # used to decide which subdomains should be collected
        if not scope_domain:
            scope_domain = []

        self.scope_domain = scope_domain
        self.page_url_set = set()
        self.search_engines_result = dict()
        self._poc_sites = None  # targets for PoC execution and file/directory brute-forcing
        self._task_domain_set = None  # domains in the task

    @property
    def task_domain_set(self):
        if self._task_domain_set is None:
            self._task_domain_set = set(utils.harrier.get_domain_by_id(self.task_id))

        return self._task_domain_set

    def site_identify(self):
        # ** run fingerprint identification
        self.web_analyze_map = services.web_analyze(self.available_sites)

    def __str__(self):
        return "<WebSiteFetch> task_id:{}, sites: {}, available_sites:{}".format(
            self.task_id, len(self.sites), len(self.available_sites))

    def save_site_info(self):
        for site_info in self.site_info_list:
            curr_site = site_info["site"]
            site_path = "/image/" + self.task_id
            file_name = '{}/{}.jpg'.format(site_path, utils.gen_filename(curr_site))
            site_info["task_id"] = self.task_id
            site_info["screenshot"] = file_name

            # merge the site identification results, deduplicated
            if self.web_analyze_map:
                finger_list = self.web_analyze_map.get(curr_site, [])
                known_finger_set = set()
                for finger_item in site_info["finger"]:
                    known_finger_set.add(finger_item["name"].lower())

                for analyze_finger in finger_list:
                    analyze_name = analyze_finger["name"].lower()
                    if analyze_name not in known_finger_set:
                        site_info["finger"].append(analyze_finger)

        logger.info("save_site_info site:{}, {}".format(len(self.site_info_list), self.__str__()))
        if self.site_info_list:
            utils.conn_db('site').insert_many(self.site_info_list)

    def site_screenshot(self):
        # *** site screenshots ***
        capture_save_dir = Config.SCREENSHOT_DIR + "/" + self.task_id
        services.site_screenshot(self.available_sites, concurrency=6, capture_dir=capture_save_dir)

    def site_spider(self):
        # *** run the static crawler
        entry_urls_list = []  # a two-dimensional array
        for site in self.available_sites:
            o = urlparse(site)
            if o.path != "":
                continue

            entry_urls = [site]
            entry_urls.extend(self.search_engines_result.get(site, []))
            entry_urls_list.append(entry_urls)

        site_spider_result = services.site_spider_thread(entry_urls_list)
        spider_urls = []
        for site in site_spider_result:
            target_urls = site_spider_result[site]
            new_target_urls = []
            for url in target_urls:
                if url in self.page_url_set:
                    continue
                new_target_urls.append(url)

                self.page_url_set.add(url)

            if not new_target_urls:
                continue

            spider_urls.extend(new_target_urls)

        if len(spider_urls) > 0:
            logger.info("spider_urls {} task_id:{}".format( len(spider_urls), self.task_id))
            page_map = services.page_fetch(spider_urls)
            for url in page_map:
                item = build_url_item(url, self.task_id, source=CollectSource.SITESPIDER)
                item.update(page_map[url])
                utils.conn_db('url').insert_one(item)

    def fetch_site(self):
        # *** fetch site info ***
        self.site_info_list = services.fetch_site(self.sites)
        for site_info in self.site_info_list:
            curr_site = site_info["site"]
            self.available_sites.append(curr_site)

    def file_leak(self):
        for site in self.poc_sites:
            pages = services.file_leak([site], utils.load_file(Config.FILE_LEAK_TOP_2k))
            for page in pages:
                item = page.dump_json()
                item["task_id"] = self.task_id
                item["site"] = site
                utils.conn_db('fileleak').insert_one(item)

    @property
    def poc_sites(self):
        if self._poc_sites is None:
            self._poc_sites = set()
            for x in self.available_sites:
                cut_target = utils.url.cut_filename(x)
                if cut_target:
                    self._poc_sites.add(cut_target)

        return self._poc_sites

    def risk_cruising(self, npoc_service_target_set: set):
        # *** run the PoC task; must be invoked manually by the outer caller
        poc_config = self.options.get("poc_config", [])
        plugins = []
        for info in poc_config:
            if not info.get("enable"):
                continue
            plugins.append(info["plugin_name"])

        poc_targets = self.poc_sites

        if npoc_service_target_set is not None:
            poc_targets = self.poc_sites | npoc_service_target_set

        result = run_risk_cruising(plugins=plugins, targets=poc_targets)
        for item in result:
            item["task_id"] = self.task_id
            item["save_date"] = utils.curr_date()
            utils.conn_db('vuln').insert_one(item)

    def nuclei_scan(self):
        logger.info("start nuclei_scan, poc_sites:{}".format(len(self.poc_sites)))
        service_targets = []
        for ip_info in utils.conn_db('ip').find({"task_id": self.task_id}, {"ip": 1, "port_info": 1}):
            for port_info in ip_info.get("port_info", []):
                port_id = port_info.get("port_id")
                if port_id in (80, 443, 843, "80", "443", "843"):
                    continue
                service_targets.append("{}:{}".format(ip_info["ip"], port_id))
        logger.info("nuclei service targets:{}".format(len(service_targets)))
        scan_results = nuclei_scan(list(self.poc_sites), service_targets)
        for item in scan_results:
            item["task_id"] = self.task_id
            item["save_date"] = utils.curr_date()
            utils.conn_db('nuclei_result').insert_one(item)

        logger.info("end nuclei_scan, result:{}".format(len(scan_results)))

    def run_func(self, name: str, func: callable):
        logger.info("start run {}, {}".format(name, self.__str__()))
        self.base_update_task.update_task_field("status", name)
        t1 = time.time()
        func()
        elapse = time.time() - t1
        self.base_update_task.update_services(name, elapse)

        logger.info("end run {} ({:.2f}s), {}".format(name, elapse, self.__str__()))

    def update_page_url_set(self):
        from app.helpers import get_url_by_task_id
        # page_url_set: load the URLs collected by the search engines from the database
        urls = get_url_by_task_id(self.task_id)
        self.page_url_set |= set(urls)

        for u in self.page_url_set:
            o = urlparse(u)
            ret_url = "{}://{}".format(o.scheme, o.netloc)
            entry_urls = self.search_engines_result.get(ret_url, [])
            entry_urls.append(u)
            self.search_engines_result[ret_url] = entry_urls

    def add_wih_domain_set(self, record):
        if self.scope_domain:
            if record.recordType == "domain":
                # for domain records, check whether the domain is in scope
                if not domain_in_scope_domain(record.content, self.scope_domain):
                    return

                if utils.check_domain_black(record.content):
                    return

                # in scope; check whether it was already added
                if record.content in self.wih_domain_set:
                    return

                # skip domains that have already been saved
                if record.content in self.wih_domain_set:
                    return

                self.wih_domain_set.add(record.content)

    def run_web_info_hunter(self):
        records = set(services.run_wih(self.sites))
        for record in records:
            # check whether the record already exists first
            if record.fnv_hash in self.wih_record_set:
                continue

            self.add_wih_domain_set(record)

            item = record.dump_json()
            item["task_id"] = self.task_id
            utils.conn_db('wih').insert_one(item)
            self.wih_record_set.add(record.fnv_hash)

    def run(self):
        # *** fetch basic site info
        self.run_func(WebSiteFetchStatus.FETCH_SITE, self.fetch_site)

        """ *** run site identification """
        if self.options.get(WebSiteFetchOption.SITE_IDENTIFY):
            self.run_func(WebSiteFetchStatus.SITE_IDENTIFY, self.site_identify)

        """ *** save site info to the database """
        self.save_site_info()

        # clear it to save memory
        self.site_info_list = []

        """ *** site screenshots """
        if self.options.get(WebSiteFetchOption.SITE_CAPTURE):
            self.run_func(WebSiteFetchStatus.SITE_CAPTURE, self.site_screenshot)

        """ *** crawl sites to discover URLs """
        if self.options.get(WebSiteFetchOption.SITE_SPIDER):
            self.update_page_url_set()
            self.run_func(WebSiteFetchStatus.SITE_SPIDER, self.site_spider)

        """ *** brute-force files/directories on the sites """
        if self.options.get(WebSiteFetchOption.FILE_LEAK):
            self.run_func(WebSiteFetchStatus.FILE_LEAK, self.file_leak)

        """ *** run nuclei on the sites """
        if self.options.get(WebSiteFetchOption.NUCLEI_SCAN):
            self.run_func(WebSiteFetchStatus.NUCLEI_SCAN, self.nuclei_scan)

        """ *** run WebInfoHunter on the sites """
        if self.options.get(WebSiteFetchOption.Info_Hunter):
            self.run_func(WebSiteFetchStatus.Info_Hunter, self.run_web_info_hunter)


def domain_in_scope_domain(domain: str, scope_domain: list):
    for scope in scope_domain:
        if domain.endswith("." + scope):
            return True
    return False


def build_url_item(site, task_id, source):
    item = {
        "site": site,
        "task_id": task_id,
        "source": source
    }
    domain_parsed = utils.domain_parsed(site)
    if domain_parsed:
        item["fld"] = domain_parsed["fld"]

    return item
