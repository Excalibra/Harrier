from typing import List
import subprocess
from app import utils
from app.config import Config
import os
import json
from app.modules import WihRecord

logger = utils.get_logger()


class InfoHunter(object):
    # Collect subdomains, AK/SK and other info from JS
    def __init__(self, sites: list):
        self.sites = set(sites)

        tmp_path = Config.TMP_PATH
        rand_str = utils.random_choices()

        # wih target file
        self.wih_target_path = os.path.join(tmp_path, "wih_target_{}.txt".format(rand_str))

        # wih result file
        self.wih_result_path = os.path.join(tmp_path, "wih_result_{}.json".format(rand_str))

        self.wih_bin_path = "wih"

    def _get_target_file(self):
        with open(self.wih_target_path, "w") as f:
            for site in self.sites:
                f.write(site + "\n")

    def _delete_file(self):
        try:
            os.unlink(self.wih_target_path)
            # delete the temporary result file
            if os.path.exists(self.wih_result_path):
                os.unlink(self.wih_result_path)
        except Exception as e:
            logger.warning(e)

    def exec_wih(self):
        command = [self.wih_bin_path,
                   "-r {}".format(Config.WIH_RULE_PATH),
                   "-J",
                   "-o {}".format(self.wih_result_path),
                   "--concurrency 3",  # number of concurrent workers
                   "--log-level zero",  # do not output logs
                   "--concurrency-per-site 1",  # concurrent workers per site
                   "--disable-ak-sk-output",  # do not save AK/SK separately
                   "-t {}".format(self.wih_target_path),
                   ]

        if Config.PROXY_URL:
            command.append("--proxy {}".format(Config.PROXY_URL))

        logger.info(" ".join(command))
        utils.exec_system(command, timeout=5 * 24 * 60 * 60)

    def check_have_wih(self) -> bool:
        command = [self.wih_bin_path, "--version"]
        try:
            output = utils.check_output(command, timeout=2 * 60)
            if "version:" in str(output):
                return True
        except Exception as e:
            logger.debug("{}".format(str(e)))

        return False

    def dump_result(self) -> list:
        results = []

        # check whether the result file exists
        if not os.path.exists(self.wih_result_path):
            return results

        with open(self.wih_result_path, "r") as f:
            while True:
                line = f.readline()
                if not line:
                    break

                data = json.loads(line)
                site = data["target"]
                records = data.get("records", [])
                for item in records:
                    content = item["content"]
                    if item["tag"]:
                        content = "{} ({})".format(content, item["tag"])

                    record_dict = {
                        "record_type": item["id"],
                        "content": content,
                        "source": item["source"],
                        "site": site,
                        "fnv_hash": item["hash"],
                    }

                    results.append(WihRecord(**record_dict))

        return results

    def run(self):
        if not self.check_have_wih():
            logger.warning("not found webInfoHunter binary")
            return []

        self._get_target_file()
        self.exec_wih()
        results = self.dump_result()
        self._delete_file()

        return results


def run_wih(sites: List[str]) -> List[WihRecord]:
    logger.info("run webInfoHunter, sites: {}".format(len(sites)))
    hunter = InfoHunter(sites)
    results = hunter.run()

    logger.info("webInfoHunter result: {}".format(len(results)))

    return results
