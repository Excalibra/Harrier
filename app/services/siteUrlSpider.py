import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from app import utils
from app.utils.url import urlsimilar
from .baseThread import BaseThread
from urllib.parse import urljoin, urlparse
from pyquery import PyQuery as pq

logger = utils.get_logger()

# repo app/tools/katana -> container /code/app/tools/katana
KATANA_BIN_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "katana")
KATANA_CRAWL_DURATION = "5m"
KATANA_PROC_TIMEOUT = 5 * 60 + 90


class URLTYPE:
    document = "document"
    js = "js"
    css = "css"


class URLInfo(object):
    def __init__(self, entry_url, crawl_url, url_type):
        self.entry_url = entry_url
        self.crawl_url = crawl_url
        self._similar_hash = urlsimilar(self.crawl_url)
        self.type = url_type or URLTYPE.document
        self.status_code = None
        self.forms = []

    def to_dict(self):
        obj = dict()
        obj["base_url"] = self.entry_url
        obj["crawl_url"] = self.crawl_url
        obj["type"] = self.type
        return obj

    def __eq__(self, other):
        if not isinstance(other, URLInfo):
            return False
        return self.crawl_url == self.crawl_url

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return str(self.to_dict())

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        return self._similar_hash

    def similar_hash(self):
        return self._similar_hash


class URLList(object):
    def __init__(self):
        self.result = []
        self.similar_hash_pool = []

    def __iter__(self):
        return self.result.__iter__()

    def __getitem__(self, item):
        return self.result[item]

    def __len__(self):
        return self.result.__len__()

    def add(self, element: URLInfo):
        """
        Plain add
        :param element: URLInfo
        :return:
        """
        if not isinstance(element, URLInfo):
            raise TypeError("need URLInfo")
        if element not in self.result:
            self.result.append(element)

    def __repr__(self):
        return str(self.result)

    def __str__(self):
        return self.__repr__()

    def __contains__(self, item):
        if not isinstance(item, URLInfo):
            return False

        return item.similar_hash() in self.similar_hash_pool


class URLSimilarList(URLList):
    def add(self, element: URLInfo):
        """
        Add only if no similar URL is present
        :param element: URLInfo
        :return:
        """
        if not isinstance(element, URLInfo):
            raise TypeError("need URLinfo")

        if element.similar_hash() not in self.similar_hash_pool:
            self.result.append(element)
            self.similar_hash_pool.append(element.similar_hash())


class SiteURLSpider(object):
    def __init__(self, entry_urls=None, deep_num=3):
        entry_url_list = URLSimilarList()
        for url in entry_urls:
            entry_url_list.add(URLInfo(url, url, URLTYPE.document))

        self.entry_url_list = entry_url_list
        self.done_url_list = URLSimilarList()
        self.deep_num = deep_num
        self.all_url_list = URLSimilarList()
        self.max_url = max(60, len(entry_urls)*6)
        self.scope_url = entry_urls[0]

        self.tagMap = [{'name': 'a', 'attr': 'href', 'type': URLTYPE.document},
                       {'name': 'form', 'attr': 'action', 'type': URLTYPE.document},
                       {'name': 'iframe', 'attr': 'src', 'type': URLTYPE.document},
                       #{'name': 'script', 'attr': 'src', 'type': URLTYPE.js},
                       #{'name': 'link', 'attr': 'href', 'type': URLTYPE.css}
                       ]

        self.ignore_ext = [".pdf", ".xls", ".xlsx", ".doc", ".docx", ".ppt", ".pptx", ".zip", ".rar"]
        self.ignore_ext.extend([".png", ".jpg", ".gif", ".js", ".css", ".ico"])

    def get_urls(self, entry_url):
        return self._work(entry_url)

    def _work(self, entry_url):
        try:
            logger.debug("[{}] req = > {}".format(len(self.done_url_list), entry_url))
            if utils.url_ext(entry_url) in self.ignore_ext:
                return URLSimilarList()

            conn = utils.http_req(entry_url)
            if conn.status_code in [301, 302, 307]:
                _url = urljoin(entry_url, conn.headers.get("Location", "")).strip()
                _url = utils.normal_url(_url)
                if _url is None:
                    return URLSimilarList()

                url_info = URLInfo(entry_url, _url, URLTYPE.document)
                if utils.same_netloc(entry_url, _url) and (url_info not in self.done_url_list):
                    entry_url = _url
                    logger.info("[{}] req 302 = > {}".format(len(self.done_url_list), entry_url))
                    conn = utils.http_req(_url)
                    self.done_url_list.add(url_info)
                    self.all_url_list.add(url_info)

            html = conn.content
            if "html" not in conn.headers.get("Content-Type", "").lower():
                return URLSimilarList()

            dom = pq(html)
            ret_url = URLSimilarList()
            for tag in self.tagMap:
                items = dom(tag['name']).items()
                for i in items:
                    _url = urljoin(entry_url, i.attr(tag['attr'])).strip()
                    _url = utils.normal_url(_url)
                    if _url is None:
                        continue

                    if utils.url_ext(_url) in self.ignore_ext:
                        continue

                    _type = tag["type"]
                    if utils.same_netloc(_url, entry_url):
                        url_info = URLInfo(entry_url, _url, _type)
                        ret_url.add(url_info)
                        self.all_url_list.add(url_info)
            return ret_url
        except Exception as e:
            logger.error("error on {} {}".format(entry_url, e))
            return URLSimilarList()

    def _use_katana(self):
        if os.environ.get("HARRIER_LEGACY_ENGINE") == "1":
            return False
        if not (os.path.isfile(KATANA_BIN_PATH) and os.access(KATANA_BIN_PATH, os.X_OK)):
            logger.warning("katana binary not available at {}, use builtin spider".format(KATANA_BIN_PATH))
            return False
        return True

    def run(self):
        if self._use_katana():
            try:
                return self._run_katana()
            except Exception as e:
                logger.warning("katana spider failed on {}: {}, fallback to builtin spider".format(
                    self.scope_url, e))
        return self._run_legacy()

    def _run_katana(self):
        targets = [x.crawl_url for x in self.entry_url_list]
        # -kf needs a depth of at least 3 to reach robots.txt / sitemap.xml
        depth = max(3, min(self.deep_num, 5))
        # do not pass -fsu: it treats all /a/b-shaped paths as similar and keeps
        # only one; similar-URL dedup is handled by URLSimilarList(urlsimilar) below
        # do not pass -ob: with this katana version an empty body breaks -jc's
        # parsing of JS endpoints
        # -duf disables dedup by response body md5 (otherwise multiple endpoints
        # with identical content would be collapsed into one)
        args = [KATANA_BIN_PATH, "-silent", "-nc", "-duc", "-jsonl", "-or", "-fx", "-duf",
                "-d", str(depth), "-c", "10", "-rl", "150",
                "-kf", "all", "-jc",
                "-timeout", "10", "-ct", KATANA_CRAWL_DURATION]

        # katana's built-in domain scope check misjudges the requests produced by
        # -kf (RootHostname is empty) as out-of-scope and drops them, so use -ns
        # to disable DNS scope and -cs with a regex to only crawl the seed sites'
        # domains; the same_netloc filter on parsed results is a final fallback
        hosts = []
        for t in targets:
            host = urlparse(t).hostname
            if host and host not in hosts:
                hosts.append(host)
        if hosts:
            scope_regex = "^https?://({})(:[0-9]+)?(/|$)".format(
                "|".join(re.escape(h) for h in hosts))
            args.extend(["-ns", "-cs", scope_regex])

        tmp_dir = tempfile.mkdtemp(prefix="katana_spider_")
        try:
            proc = subprocess.Popen(args, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    cwd=tmp_dir)
            stdin_data = "\n".join(targets).encode("utf-8")
            try:
                stdout_data, stderr_data = proc.communicate(
                    input=stdin_data, timeout=KATANA_PROC_TIMEOUT)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                raise RuntimeError("katana crawl timeout {}s".format(KATANA_PROC_TIMEOUT))

            if proc.returncode != 0 and not stdout_data:
                raise RuntimeError("katana exit code {}: {}".format(
                    proc.returncode, stderr_data.decode("utf-8", "ignore")[-200:]))
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        return self._parse_katana_output(stdout_data, targets)

    def _parse_katana_output(self, stdout_data, targets):
        for line in stdout_data.decode("utf-8", "ignore").splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue

            try:
                item = json.loads(line)
            except ValueError:
                continue

            request = item.get("request") or {}
            endpoint = request.get("endpoint")
            if not endpoint:
                continue

            crawl_url = utils.normal_url(endpoint.strip())
            if crawl_url is None:
                continue

            if utils.url_ext(crawl_url) in self.ignore_ext:
                continue

            if not any(utils.same_netloc(crawl_url, t) for t in targets):
                continue

            url_type = URLTYPE.document
            if request.get("tag") == "script":
                url_type = URLTYPE.js
            elif request.get("tag") == "link":
                url_type = URLTYPE.css

            url_info = URLInfo(request.get("source") or self.scope_url, crawl_url, url_type)
            response = item.get("response") or {}
            url_info.status_code = response.get("status_code")
            url_info.forms = response.get("forms") or []
            self.all_url_list.add(url_info)
            self.done_url_list.add(url_info)

            if len(self.all_url_list) > self.max_url:
                logger.warning("katana exit on request max url {}".format(self.scope_url))
                break

        return self.all_url_list

    def _run_legacy(self):
        tmp_urls = self.entry_url_list
        for num in range(0, self.deep_num):
            if len(tmp_urls) > 0:
                logger.info("{} deep num {}, len {}".format(self.scope_url, num + 1, len(tmp_urls)))

            new_url = URLSimilarList()
            for info in tmp_urls:
                self.all_url_list.add(info)
                if len(self.done_url_list) > self.max_url:
                    logger.warning("exit on request max url {}".format(self.scope_url))
                    return self.all_url_list

                if info not in self.done_url_list:
                    ret_urls = self.get_urls(info.crawl_url)
                    self.done_url_list.add(info)
                    for x in ret_urls:
                        new_url.add(x)

            tmp_urls = new_url

        return self.all_url_list


class SiteURLSpiderThread(BaseThread):
    def __init__(self, entry_urls_list, concurrency=6, deep_num=5):
        super().__init__(entry_urls_list, concurrency=concurrency)
        self.site_url_map = {}
        self.deep_num = deep_num

    def work(self, entry_urls):
        # entry_urls is an array whose first element is the current site
        site = entry_urls[0]
        self.site_url_map[site] = site_spider(entry_urls, self.deep_num)

    def run(self):
        t1 = time.time()
        logger.info("start site url spider entry_urls_list:{}".format(len(self.targets)))
        self._run()
        elapse = time.time() - t1
        logger.info("end site url spider ({:.2f}s)".format(elapse))
        return self.site_url_map


def site_spider_thread(entry_urls_list, deep_num=5):
    s = SiteURLSpiderThread(entry_urls_list, concurrency=6, deep_num=deep_num)
    return s.run()


def site_spider(entry_url, deep_num=3):
    if isinstance(entry_url, str):
        entry_url = [entry_url]

    ret = []
    s = SiteURLSpider(entry_url, deep_num)
    for x in s.run():
        if urlparse(x.crawl_url).path == "/" or (not urlparse(x.crawl_url).path):
            continue

        if x.type == URLTYPE.document:
            ret.append(x.crawl_url)

    return ret










