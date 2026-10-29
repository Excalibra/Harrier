import ipaddress
import json
import math
import os
import re
import shutil
import subprocess
import tempfile

from app import utils
from app.utils import nmap, is_valid_exclude_ports
from app.config import Config

logger = utils.get_logger()

# repo app/tools/gogo -> container /code/app/tools/gogo
GOGO_BIN_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "gogo")
GOGO_PORTS_PATTERN = re.compile(r"^[\d,\-]+$")
GOGO_MAX_FILL_HOSTS = 65536
GOGO_MAX_SCAN_TIMEOUT = 4 * 3600


class PortScan:
    def __init__(self, targets, ports=None, service_detect=False, os_detect=False,
                 port_parallelism=None, port_min_rate=None, custom_host_timeout=None,
                 exclude_ports=None,
                 ):
        self.target_list = list(targets)
        self.targets = " ".join(targets)
        self.ports = ports
        self.service_detect = service_detect
        self.os_detect = os_detect
        self.max_host_group = 32
        self.alive_port = "22,80,443,843,3389,8007-8011,8443,9090,8080-8091,8093,8099,5000-5004,2222,3306,1433,21,25"
        self.nmap_arguments = "-sT -n --open"
        self.max_retries = 3
        self.host_timeout = 60*5
        self.parallelism = port_parallelism  # default 32
        self.min_rate = port_min_rate  # default 64
        self.exclude_ports = exclude_ports

        if service_detect:
            self.host_timeout += 60 * 5
            self.nmap_arguments += " -sV"

        if os_detect:
            self.host_timeout += 60 * 4
            self.nmap_arguments += " -O"

        if len(self.ports.split(",")) > 60:
            self.nmap_arguments += " -PE -PS{}".format(self.alive_port)
            self.max_retries = 2
        else:
            if self.ports != "0-65535":
                self.nmap_arguments += " -Pn"

        if self.ports == "0-65535":
            self.max_host_group = 2
            self.min_rate = max(self.min_rate, 800)
            self.parallelism = max(self.parallelism, 128)

            self.nmap_arguments += " -PE -PS{}".format(self.alive_port)
            self.host_timeout += 60 * 5
            self.max_retries = 2

        self.nmap_arguments += " --max-rtt-timeout 800ms"
        self.nmap_arguments += " --min-rate {}".format(self.min_rate)
        self.nmap_arguments += " --script-timeout 6s"
        self.nmap_arguments += " --max-hostgroup {}".format(self.max_host_group)

        # honor the timeout passed in by the caller
        if custom_host_timeout is not None:
            if int(custom_host_timeout) > 0:
                self.host_timeout = custom_host_timeout
        self.nmap_arguments += " --host-timeout {}s".format(self.host_timeout)
        self.nmap_arguments += " --min-parallelism {}".format(self.parallelism)
        self.nmap_arguments += " --max-retries {}".format(self.max_retries)

        if self.exclude_ports is not None:
            if self.exclude_ports != "" and\
                    is_valid_exclude_ports(self.exclude_ports):
                self.nmap_arguments += " --exclude-ports {}".format(self.exclude_ports)

    def run(self):
        if self._use_gogo():
            try:
                return self._run_gogo()
            except Exception as e:
                logger.warning("gogo port scan failed: {}, fallback to nmap".format(e))
        return self._run_nmap()

    def _use_gogo(self):
        if os.environ.get("HARRIER_LEGACY_ENGINE") == "1":
            return False
        # gogo has no OS fingerprinting, so fall back to nmap when OS detection is requested
        if self.os_detect:
            return False
        if not (os.path.isfile(GOGO_BIN_PATH) and os.access(GOGO_BIN_PATH, os.X_OK)):
            logger.warning("gogo binary not available at {}, use nmap".format(GOGO_BIN_PATH))
            return False
        return True

    def _run_gogo(self):
        if not self.target_list:
            raise RuntimeError("empty target list")

        ports = self._gogo_port_arg()
        threads = self._gogo_threads()
        scan_timeout = self._gogo_scan_timeout(threads)

        args = [GOGO_BIN_PATH, "-L", "-p", ports, "-q", "-o", "jl",
                "-t", str(threads), "-d", "2"]
        if self.service_detect:
            # -v enables active service fingerprinting, matching nmap -sV
            args.append("-v")

        logger.info("gogo target {}  ports {}  threads {}  timeout {}".format(
            self.targets[:20], ports[:20], threads, scan_timeout))

        tmp_dir = tempfile.mkdtemp(prefix="gogo_scan_")
        try:
            proc = subprocess.Popen(args, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    cwd=tmp_dir)
            stdin_data = "\n".join(self.target_list).encode("utf-8")
            try:
                stdout_data, stderr_data = proc.communicate(
                    input=stdin_data, timeout=scan_timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                raise RuntimeError("gogo scan timeout {}s".format(scan_timeout))

            if proc.returncode != 0:
                raise RuntimeError("gogo exit code {}: {}".format(
                    proc.returncode, stderr_data.decode("utf-8", "ignore")[-200:]))
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        return self._build_gogo_result(stdout_data)

    def _gogo_port_arg(self):
        ports = self.ports.strip()
        if not GOGO_PORTS_PATTERN.match(ports):
            raise RuntimeError("ports {} cannot convert to gogo syntax".format(ports[:20]))
        # gogo silently succeeds on invalid port input, so validate strictly here
        for token in ports.split(","):
            if "-" in token:
                start, end = token.split("-", 1)
                if not start.isdigit() or not end.isdigit():
                    raise RuntimeError("invalid port range {}".format(token))
                if not (0 <= int(start) <= int(end) <= 65535):
                    raise RuntimeError("invalid port range {}".format(token))
            else:
                if not token.isdigit() or int(token) > 65535:
                    raise RuntimeError("invalid port {}".format(token))
        return ports

    def _gogo_threads(self):
        # gogo has no min-rate/parallelism concept; map them to a thread count
        threads = max(256, min(4000, int(self.parallelism) * 16))
        if self.min_rate >= 800:
            threads = max(threads, 2000)
        return threads

    def _gogo_scan_timeout(self, threads):
        # estimate the overall timeout from targets*ports; lower bound host_timeout, upper bound 4 hours
        port_count = self._ports_count(self.ports)
        work = port_count * len(self.target_list)
        est = int(math.ceil(work * 3.0 / threads)) + 120
        return max(self.host_timeout, min(est, GOGO_MAX_SCAN_TIMEOUT))

    @staticmethod
    def _ports_count(ports):
        total = 0
        for token in ports.split(","):
            if "-" in token:
                start, end = token.split("-", 1)
                total += int(end) - int(start) + 1
            elif token:
                total += 1
            if total > 65536:
                return 65536
        return max(total, 1)

    def _build_gogo_result(self, stdout_data):
        exclude_port_set = self._exclude_port_set()

        ip_port_map = {}
        seen = set()
        text = stdout_data.decode("utf-8", "ignore")
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                result = json.loads(line)
            except ValueError:
                raise RuntimeError("cannot parse gogo output line: {}".format(line[:100]))

            ip = result.get("ip")
            port = result.get("port")
            if not ip or port is None:
                continue
            port = int(port)
            if port in exclude_port_set:
                continue
            if (ip, port) in seen:
                continue
            seen.add((ip, port))
            ip_port_map.setdefault(ip, []).append(self._gogo_port_info(result))

        ip_info_list = []
        for ip, port_info_list in ip_port_map.items():
            # match nmap behavior: when a host has too many open ports, keep only 80/443
            if len(port_info_list) > 600:
                port_info_list = [x for x in port_info_list if x["port_id"] in [80, 443]]
            ip_info_list.append({
                "ip": ip,
                "port_info": port_info_list,
                "os_info": {}
            })

        # nmap in -Pn mode (<= 60 ports and not full port range) reports all
        # target hosts; mirror that behavior by adding empty records for
        # targets with no open ports
        if self._gogo_report_all_targets():
            found = set(ip_port_map.keys())
            for ip in self._expand_targets():
                if ip not in found:
                    ip_info_list.append({"ip": ip, "port_info": [], "os_info": {}})

        return ip_info_list

    @staticmethod
    def _gogo_port_info(result):
        frameworks = result.get("frameworks") or {}
        version_list = []
        for name in sorted(frameworks):
            fw = frameworks.get(name) or {}
            fw_version = fw.get("version") or ""
            version_list.append("{}/{}".format(name, fw_version) if fw_version else name)

        return {
            "port_id": int(result["port"]),
            "service_name": result.get("protocol") or "tcp",
            "version": ", ".join(version_list),
            "product": result.get("midware") or "",
            "protocol": "tcp",
            # fields below are extra in gogo compared to nmap
            "title": result.get("title") or "",
            "host": result.get("host") or "",
            "uri": result.get("uri") or "",
            "frameworks": sorted(frameworks.keys()),
        }

    def _gogo_report_all_targets(self):
        # same condition as nmap -Pn
        return len(self.ports.split(",")) <= 60 and self.ports != "0-65535"

    def _expand_targets(self):
        ips = []
        for target in self.target_list:
            try:
                if "/" in target:
                    network = ipaddress.ip_network(target, strict=False)
                    if network.num_addresses > GOGO_MAX_FILL_HOSTS - len(ips):
                        # target network too large; skip empty-host fill and only return hosts with results
                        logger.warning("gogo skip empty-host fill for large target {}".format(target))
                        continue
                    ips.extend(str(ip) for ip in network.hosts())
                else:
                    ips.append(str(ipaddress.ip_address(target)))
            except ValueError:
                continue
        return ips

    def _exclude_port_set(self):
        port_set = set()
        if self.exclude_ports and is_valid_exclude_ports(self.exclude_ports):
            for token in self.exclude_ports.split(","):
                if "-" in token:
                    start, end = token.split("-", 1)
                    port_set.update(range(int(start), int(end) + 1))
                elif token:
                    port_set.add(int(token))
        return port_set

    def _run_nmap(self):
        logger.info("nmap target {}  ports {}  arguments {}".format(
            self.targets[:20], self.ports[:20], self.nmap_arguments))
        nm = nmap.PortScanner()
        nm.scan(hosts=self.targets, ports=self.ports, arguments=self.nmap_arguments)
        ip_info_list = []
        for host in nm.all_hosts():
            port_info_list = []
            for proto in nm[host].all_protocols():
                port_len = len(nm[host][proto])

                for port in nm[host][proto]:
                    # drop hosts with too many open ports outright
                    if port_len > 600 and (port not in [80, 443]):
                        continue

                    port_info = nm[host][proto][port]
                    item = {
                        "port_id": port,
                        "service_name": port_info["name"],
                        "version": port_info["version"],
                        "product": port_info["product"],
                        "protocol": proto
                    }

                    port_info_list.append(item)

            osmatch_list = nm[host].get("osmatch", [])
            os_info = self.os_match_by_accuracy(osmatch_list)

            ip_info = {
                "ip": host,
                "port_info": port_info_list,
                "os_info": os_info
            }
            ip_info_list.append(ip_info)

        return ip_info_list

    def os_match_by_accuracy(self, os_match_list):
        for os_match in os_match_list:
            accuracy = os_match.get('accuracy', '0')
            if int(accuracy) > 90:
                return os_match

        return {}


def port_scan(targets, ports=Config.TOP_10, service_detect=False, os_detect=False,
              port_parallelism=32, port_min_rate=64, custom_host_timeout=None, exclude_ports=None):
    targets = list(set(targets))
    targets = list(filter(utils.not_in_black_ips, targets))
    ps = PortScan(targets=targets, ports=ports, service_detect=service_detect, os_detect=os_detect,
                  port_parallelism=port_parallelism, port_min_rate=port_min_rate,
                  custom_host_timeout=custom_host_timeout,
                  exclude_ports=exclude_ports,
                  )
    return ps.run()
