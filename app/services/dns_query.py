import logging
import time
import concurrent.futures
from app import utils
from app.config import Config


class DNSQueryBase(object):
    def __init__(self):
        self.source_name = None
        self.logger = utils.get_logger()

    def init_key(self, **kwargs):
        """
        Initialize the various API keys
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def sub_domains(self, target):
        """
        Query subdomains for the target
        :param target:
        :return:
        """
        raise NotImplementedError()

    def query(self, target):
        t1 = time.time()
        self.logger.info("start query {} on {}".format(target, self.source_name))
        try:
            domains = self.sub_domains(target)
        except Exception as e:
            self.logger.error("{} error: {}".format(self.source_name, e))
            return []

        if not isinstance(domains, list):
            self.logger.warning("{} is not list".format(domains))
            return []

        """Filter out invalid data below"""
        subdomains = []

        for domain in domains:
            domain = domain.strip("*.")
            domain = domain.lower()
            if not domain:
                continue

            if not domain.endswith(".{}".format(target)):
                continue

            # drop overly long domains
            if len(domain) - len(target) >= Config.DOMAIN_MAX_LEN:
                continue

            if not utils.is_valid_domain(domain):
                continue

            # block censored and blacklisted domains
            if utils.check_domain_black(domain):
                continue

            if utils.domain_parsed(domain):
                subdomains.append(domain)

        subdomains = list(set(subdomains))

        t2 = time.time()
        self.logger.info("end query {} on {}, source result:{}, real result:{} ({:.2f}s)".format(
            target, self.source_name, len(domains), len(subdomains), t2 - t1))

        return subdomains


def run_plugin(p, target) -> (str, list):
    """
    Run a single plugin
    """
    logger = utils.get_logger()
    try:
        query_key = Config.QUERY_PLUGIN_CONFIG
        source_name = p.source_name
        source_kwargs = query_key.get(source_name, {})
        if source_kwargs:
            if not isinstance(source_kwargs, dict):
                logger.warning(f"{source_name} config {source_kwargs} is not dict")
                return source_name, []

            plugin_enable_flag = source_kwargs.pop("enable", True)
            if not plugin_enable_flag:
                logger.debug(f"skip {source_name}, enable is set false")
                return source_name, []

            if source_kwargs:
                if all(source_kwargs.values()):
                    p.init_key(**source_kwargs)
                else:
                    logger.debug(f"skip {source_name}, config is not set")
                    return source_name, []

        results = p.query(target)
        logger.debug(f"run {source_name} target:{target}, result:{len(results)}")
        return source_name, results

    except Exception as e:
        error_str = str(e)
        if "please set fofa key" in error_str:
            logger.debug(error_str)
        else:
            logger.error(f"{p.source_name} error {type(e)} {error_str}")
        return []


# *****  Run the domain query plugins
"""
Returns: [{
    "domain": "www.baidu.com",
    "source": "crtsh"
}]
"""


def run_query_plugin(target, sources=None):
    """
    Run subdomain query plugins in batch
    :param sources:
    :param target:
    :return:
    """
    if sources is None:
        sources = []

    plugins = utils.load_query_plugins(Config.dns_query_plugin_path)
    logger = utils.get_logger()
    ret = []
    subdomains = set()
    t1 = time.time()

    if sources:
        plugins = [p for p in plugins if p.source_name in sources]

    logger.debug(f"load plugins len:{len(plugins)} sources: {sources}")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(run_plugin, p, target): p for p in plugins}
        for future in concurrent.futures.as_completed(futures):
            source_name, results = future.result()
            for result in results:
                if result in subdomains:
                    continue

                item = {
                    "domain": result,
                    "source": source_name
                }
                ret.append(item)
                subdomains.add(result)

    t2 = time.time()
    logger.info("{} subdomains result {} ({:.2f}s)".format(target, len(subdomains), t2 - t1))
    return ret
