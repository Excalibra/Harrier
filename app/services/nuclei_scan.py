import json
import os.path
import subprocess

from app.config import Config
from app import utils


logger = utils.get_logger()


class NucleiScan(object):
    def __init__(self, targets: list):
        self.targets = targets

        tmp_path = Config.TMP_PATH
        rand_str = utils.random_choices()

        self.nuclei_target_path = os.path.join(tmp_path,
                                               "nuclei_target_{}.txt".format(rand_str))

        self.nuclei_result_path = os.path.join(tmp_path,
                                               "nuclei_result_{}.json".format(rand_str))

        self.nuclei_bin_path = "nuclei"

        # nuclei 2.9.1 renamed the -json flag to -jsonl
        self.nuclei_json_flag = None

    def _check_json_flag(self):
        json_flag = ["-json", "-jsonl"]
        for x in json_flag:
            command = [self.nuclei_bin_path, "-duc", x, "-version"]
            pro = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if pro.returncode == 0:
                self.nuclei_json_flag = x
                return

        assert self.nuclei_json_flag

    def _delete_file(self):
        try:
            os.unlink(self.nuclei_target_path)
            # delete the temporary result file
            if os.path.exists(self.nuclei_result_path):
                os.unlink(self.nuclei_result_path)
        except Exception as e:
            logger.warning(e)

    def check_have_nuclei(self) -> bool:
        command = [self.nuclei_bin_path, "-version"]
        try:
            pro = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if pro.returncode == 0:
                return True
        except Exception as e:
            logger.debug("{}".format(str(e)))

        return False

    def _gen_target_file(self):
        with open(self.nuclei_target_path, "w") as f:
            for domain in self.targets:
                domain = domain.strip()
                if not domain:
                    continue
                f.write(domain + "\n")

    def dump_result(self) -> list:
        results = []
        with open(self.nuclei_result_path, "r") as f:
            while True:
                line = f.readline()
                if not line:
                    break

                data = json.loads(line)
                item = {
                    "template_url": data.get("template-url", ""),
                    "template_id": data.get("template-id", ""),
                    "vuln_name": data.get("info", {}).get("name", ""),
                    "vuln_severity": data.get("info", {}).get("severity", ""),
                    "vuln_url": data.get("matched-at", ""),
                    "curl_command": data.get("curl-command", ""),
                    "target": data.get("host", "")
                }
                results.append(item)

        return results

    def exec_nuclei(self, types="http", tags="cve,exposure,misconfiguration"):
        self._gen_target_file()

        command = [self.nuclei_bin_path, "-duc",
                   "-tags {}".format(tags),
                   "-severity low,medium,high,critical",
                   "-type {}".format(types),
                   "-timeout 15",
                   "-retries 2",
                   "-l {}".format(self.nuclei_target_path),
                   self.nuclei_json_flag,  # nuclei 2.9.1 renamed the -json flag to -jsonl
                   "-stats",
                   "-stats-interval 60",
                   "-o {}".format(self.nuclei_result_path),
                   ]

        logger.info(" ".join(command))
        utils.exec_system(command, timeout=96*60*60)

    def run(self):
        if not self.check_have_nuclei():
            logger.warning("not found nuclei")
            return []

        self._check_json_flag()

        self.exec_nuclei()

        results = self.dump_result()

        # delete temporary files
        self._delete_file()

        return results

    def run_network(self):
        """network/javascript/ssl templates against ip:port service targets"""
        if not self.check_have_nuclei():
            logger.warning("not found nuclei")
            return []

        self._check_json_flag()

        self.exec_nuclei(types="tcp,ssl,javascript,dns",
                         tags="cve,misconfiguration,network,dns")

        results = self.dump_result()

        self._delete_file()

        return results


def nuclei_scan(targets: list, service_targets: list = None):
    """HTTP templates against web sites, plus network-level templates
    (SMB/RDP/FTP/VNC/SSL checks) against raw ip:port service targets."""
    results = []

    if targets:
        results.extend(NucleiScan(targets=targets).run())

    if service_targets:
        results.extend(NucleiScan(targets=service_targets).run_network())

    return results

