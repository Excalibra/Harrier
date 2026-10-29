import time
import json
import math
import os
import subprocess
from http.client import responses as http_responses
from pyquery import PyQuery as pq
import binascii
from urllib.parse import urljoin, urlparse
from urllib3.util.url import parse_url, get_host
import mmh3
from app import utils
from .baseThread import BaseThread, thread_map

logger = utils.get_logger()
from .autoTag import auto_tag
from app.utils import http_req, normal_url
from app.utils.fingerprint import load_fingerprint, fetch_fingerprint

# path to the httpx engine binary (/code/app/tools/httpx inside the container)
HTTPX_BIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "tools", "httpx")
# set this env var to force the legacy Python requests engine
HTTPX_LEGACY_ENV = "HARRIER_LEGACY_ENGINE"


def use_httpx_engine():
    """Return True when the httpx binary is available and legacy mode is not forced"""
    if os.environ.get(HTTPX_LEGACY_ENV, "").strip().lower() in ("1", "true", "yes"):
        return False

    if not os.path.isfile(HTTPX_BIN) or not os.access(HTTPX_BIN, os.X_OK):
        return False

    return True


class FetchSite(BaseThread):
    def __init__(self, sites, concurrency=6, http_timeout=None):
        super().__init__(sites, concurrency)
        self.site_info_list = []
        self.fingerprint_list = load_fingerprint()
        self.http_timeout = http_timeout
        if http_timeout is None:
            self.http_timeout = (10.1, 30.1)

    def fetch_fingerprint(self, item, content):
        favicon_hash = item["favicon"].get("hash", 0)
        result = fetch_fingerprint(content=content, headers=item["headers"],
                                   title=item["title"], favicon_hash=favicon_hash,
                                   finger_list=self.fingerprint_list)

        result_db = finger_identify(content=content, header=item["headers"],
                                    title=item["title"], favicon_hash=str(favicon_hash))

        result = set(result + result_db)

        finger = []
        for name in result:
            finger_item = {
                "icon": "default.png",
                "name": name,
                "confidence": "80",
                "version": "",
                "website": "https://www.riskivy.com",
                "categories": []
            }
            finger.append(finger_item)

        if finger:
            item["finger"] = finger

    def work(self, site, max_redirect=5):
        if max_redirect <= 0:
            return

        _, hostname, _ = get_host(site)

        conn = utils.http_req(site, timeout=self.http_timeout)
        item = {
            "site": site[:200],
            "hostname": hostname,
            "ip": "",
            "title": utils.get_title(conn.content),
            "status": conn.status_code,
            "headers": utils.get_headers(conn),
            "http_server": conn.headers.get("Server", ""),
            "body_length": len(conn.content),
            "finger": [],
            "favicon": fetch_favicon(site)
        }

        self.fetch_fingerprint(item, content=conn.content)
        domain_parsed = utils.domain_parsed(hostname)
        if domain_parsed:
            item["fld"] = domain_parsed["fld"]
            ips = utils.get_ip(hostname)
            if ips:
                item["ip"] = ips[0]
        else:
            item["ip"] = hostname

        # save the site info
        if max_redirect == 5 or max_redirect == 1 \
                or (conn.status_code != 301 and conn.status_code != 302):
            self.site_info_list.append(item)

        if conn.status_code == 301 or conn.status_code == 302:
            url_302 = urljoin(site, conn.headers.get("Location", ""))
            url_302 = normal_url(url_302)

            # defensive check against overly long URLs
            if len(url_302) > 260:
                return

            if url_302 != site and same_netloc_and_scheme(url_302, site):
                self.work(url_302, max_redirect=max_redirect - 1)

    def _run_httpx(self):
        """Fetch site info in batches with the httpx binary; follow 302/301 in rounds like the legacy logic"""
        targets = []
        for target in self.targets:
            if isinstance(target, str):
                target = target.strip()
            if not target:
                continue
            targets.append(target)

        current = targets
        # legacy semantics: work(site, max_redirect=5), 5 rounds total; rounds 1 and 5 always record
        for redirect_round in range(5):
            if not current:
                break

            result_map = self._httpx_batch(current)
            next_round = []
            for site in current:
                data = result_map.get(site)
                if not data or data.get("failed"):
                    continue

                item = self.build_httpx_item(site, data)
                status = item["status"]

                if redirect_round == 0 or redirect_round == 4 \
                        or (status != 301 and status != 302):
                    self.site_info_list.append(item)

                if status not in (301, 302) or redirect_round >= 4:
                    continue

                url_302 = urljoin(site, data.get("location") or "")
                url_302 = normal_url(url_302)

                # defensive check against overly long URLs
                if len(url_302) > 260:
                    continue

                if url_302 != site and same_netloc_and_scheme(url_302, site):
                    next_round.append(url_302)

            current = next_round

        self._fill_favicon_data()

    def _fill_favicon_data(self):
        """Backfill favicon.data using the legacy FetchFavicon validation logic (hash/url already provided by httpx)"""
        try:
            urls = set()
            for item in self.site_info_list:
                favicon = item.get("favicon") or {}
                if favicon.get("hash") and not favicon.get("data") and favicon.get("url"):
                    urls.add(favicon["url"])

            if not urls:
                return

            def _fetch(favicon_url):
                return FetchFavicon(favicon_url).get_favicon_data(favicon_url)

            data_map = thread_map(_fetch, list(urls), concurrency=self.concurrency)

            for item in self.site_info_list:
                favicon = item.get("favicon") or {}
                favicon_url = favicon.get("url")
                if favicon_url and data_map.get(favicon_url):
                    favicon["data"] = data_map[favicon_url]
        except Exception as e:
            logger.warning("httpx fill favicon data error: {}".format(e))

    def _httpx_batch(self, sites):
        """Run one httpx process over a batch of sites; return {input site: parsed json dict}"""
        try:
            per_req_timeout = int(math.ceil(max(self.http_timeout)))
        except Exception:
            per_req_timeout = 10
        per_req_timeout = min(max(per_req_timeout, 5), 120)

        threads = min(50, max(1, len(sites)))
        command = [HTTPX_BIN,
                   "-silent", "-nc", "-json", "-irh", "-irr",
                   "-td", "-title", "-sc", "-cl", "-rt", "-server",
                   "-favicon", "-cname", "-ip", "-cdn", "-location",
                   "-t", str(threads), "-rl", "150",
                   "-timeout", str(per_req_timeout), "-retries", "1",
                   "-max-host-error", "30"]

        # overall subprocess timeout: estimated from the batch count, with a bounded cap
        batches = int(math.ceil(len(sites) / float(threads)))
        proc_timeout = 30 + per_req_timeout * 2 * max(1, batches)
        proc_timeout = min(proc_timeout, 4 * 60 * 60)

        logger.info("httpx engine fetch {} sites, per-req timeout {}s, proc timeout {}s".format(
            len(sites), per_req_timeout, proc_timeout))
        logger.debug("httpx cmd: {}".format(" ".join(command)))

        input_data = ("\n".join(sites) + "\n").encode("utf-8", "ignore")
        proc = subprocess.run(command, input=input_data,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=proc_timeout, close_fds=True)

        if proc.stderr:
            err_out = proc.stderr.decode("utf-8", "replace").strip()
            if err_out:
                logger.debug("httpx stderr: {}".format(err_out[:500]))

        if proc.returncode != 0 and not proc.stdout:
            raise RuntimeError("httpx exit code {}".format(proc.returncode))

        result_map = {}
        for line in proc.stdout.decode("utf-8", "replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except ValueError:
                logger.warning("httpx invalid json line: {}".format(line[:200]))
                continue

            orig_input = data.get("input")
            if orig_input:
                result_map[orig_input] = data

        return result_map

    def build_httpx_item(self, site, data):
        """httpx json result -> site structure identical to legacy (adds tech/cdn/response_time)"""
        _, hostname, _ = get_host(site)

        content = (data.get("body") or "").encode("utf-8", "replace")
        status = data.get("status_code") or 0

        item = {
            "site": site[:200],
            "hostname": hostname,
            "ip": "",
            "title": data.get("title") or utils.get_title(content),
            "status": status,
            "headers": self.build_httpx_headers(data, status, len(content)),
            "http_server": data.get("webserver") or "",
            "body_length": len(content),
            "finger": [],
            "favicon": self.build_httpx_favicon(data),
            "tech": data.get("tech") or [],
            "cdn": data.get("cdn_name") or "",
            "response_time": data.get("time") or ""
        }

        self.fetch_fingerprint(item, content=content)
        domain_parsed = utils.domain_parsed(hostname)
        if domain_parsed:
            item["fld"] = domain_parsed["fld"]
            ips = data.get("a") or []
            if not ips:
                ips = utils.get_ip(hostname)
            if ips:
                item["ip"] = ips[0]
        else:
            item["ip"] = hostname

        return item

    @staticmethod
    def build_httpx_headers(data, status, body_length):
        """Replicate the output of utils.get_headers: status line + raw header text"""
        raw = (data.get("raw_header") or "").strip()
        if not raw:
            header_map = data.get("header") or {}
            lines = []
            for key in header_map:
                value = header_map[key]
                if isinstance(value, list):
                    for v in value:
                        lines.append("{}: {}".format(key, v))
                else:
                    lines.append("{}: {}".format(key, value))
            raw = "\n".join(lines)

        raw = raw.replace("\r\n", "\n").replace("\r", "\n")

        # httpx's raw_header usually already contains the status line; if not, prepend one in legacy format
        if raw.startswith("HTTP/"):
            headers = raw
        else:
            version = "2" if data.get("http2") else "1.1"
            reason = http_responses.get(status, "")
            first_line = "HTTP/{} {} {}".format(version, status, reason).rstrip()
            headers = first_line + "\n" + raw

        if "content-length:" not in raw.lower():
            headers = "{}\nContent-Length: {}".format(headers, body_length)

        return headers

    @staticmethod
    def build_httpx_favicon(data):
        """httpx's favicon mmh3 -> legacy favicon structure (no source for the data field, leave it empty)"""
        hash_str = data.get("favicon")
        if not hash_str:
            return {}

        try:
            hash_int = int(hash_str)
        except (TypeError, ValueError):
            return {}

        return {
            "data": "",
            "url": data.get("favicon_url") or "",
            "hash": hash_int
        }

    def run(self):
        t1 = time.time()
        logger.info("start fetch site {}".format(len(self.targets)))
        if use_httpx_engine():
            try:
                self._run_httpx()
            except Exception as e:
                logger.warning("httpx engine error, fallback to legacy engine: {}".format(e))
                logger.exception(e)
                self.site_info_list = []
                self._run()
        else:
            self._run()
        elapse = time.time() - t1
        logger.info("end fetch site elapse {}".format(elapse))

        # auto-tag the site info
        auto_tag(self.site_info_list)

        return self.site_info_list


def finger_identify(content: bytes, header: str, title: str, favicon_hash: str):
    from app.services import finger_db_identify

    try:
        content = content.decode("utf-8")
    except UnicodeDecodeError:
        content = content.decode("gbk", "ignore")

    variables = {
        "body": content,
        "header": header,
        "title": title,
        "icon_hash": favicon_hash
    }

    return finger_db_identify(variables)


def same_netloc_and_scheme(u1, u2):
    u1 = normal_url(u1)
    u2 = normal_url(u2)
    parsed1 = parse_url(u1)
    parsed2 = parse_url(u2)

    if parsed1.scheme == parsed2.scheme and parsed1.netloc == parsed2.netloc:
        return True

    return False


def fetch_favicon(url):
    f = FetchFavicon(url)
    return f.run()


def fetch_site(sites, concurrency=15, http_timeout=None):
    # refresh the database cache
    from app.services import finger_db_cache
    finger_db_cache.update_cache()

    f = FetchSite(sites, concurrency=concurrency, http_timeout=http_timeout)
    return f.run()


class FetchFavicon(object):
    def __init__(self, url):
        self.url = url
        self.favicon_url = None
        pass

    def build_result(self, data):
        result = {
            "data": data,
            "url": self.favicon_url,
            "hash": mmh3.hash(data)
        }
        return result

    def run(self):
        result = {}
        try:
            favicon_url = urljoin(self.url, "/favicon.ico")
            data = self.get_favicon_data(favicon_url)
            if data:
                self.favicon_url = favicon_url
                return self.build_result(data)

            favicon_url = self.find_icon_url_from_html()
            if not favicon_url:
                return result
            data = self.get_favicon_data(favicon_url)
            if data:
                self.favicon_url = favicon_url
                return self.build_result(data)

        except Exception as e:
            logger.warning("error on {} {}".format(self.url, e))

        return result

    def get_favicon_data(self, favicon_url):
        conn = http_req(favicon_url)
        if conn.status_code != 200:
            return

        if len(conn.content) <= 80:
            logger.debug("favicon content len lt 100")
            return

        if "image" in conn.headers.get("Content-Type", ""):
            data = self.encode_bas64_lines(conn.content)
            return data

    def encode_bas64_lines(self, s):
        """Encode a string into multiple lines of base-64 data."""
        MAXLINESIZE = 76  # Excluding the CRLF
        MAXBINSIZE = (MAXLINESIZE // 4) * 3
        pieces = []
        for i in range(0, len(s), MAXBINSIZE):
            chunk = s[i: i + MAXBINSIZE]
            pieces.append(bytes.decode(binascii.b2a_base64(chunk)))
        return "".join(pieces)

    def find_icon_url_from_html(self):
        conn = http_req(self.url)
        if b"<link" not in conn.content:
            return
        d = pq(conn.content)
        links = d('link').items()
        icon_link_list = []
        for link in links:
            if link.attr("href") and 'icon' in link.attr("rel"):
                icon_link_list.append(link)

        for link in icon_link_list:
            if "shortcut" in link:
                return urljoin(self.url, link.attr('href'))

        if icon_link_list:
            return urljoin(self.url, icon_link_list[0].attr('href'))
