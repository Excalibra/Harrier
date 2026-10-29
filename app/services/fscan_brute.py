import json
import os
import subprocess

from app.config import Config, basedir
from app import utils

logger = utils.get_logger()

FSCAN_BIN = os.path.join(basedir, "tools", "fscan")

# fscan's built-in plugins that do weak-password/unauthorized-access checks and
# fail fast on ports of the wrong protocol (see fscan -list-plugins)
FSCAN_FAST_PLUGINS = (
    "ssh,ftp,smb,vnc,mysql,mssql,"
    "redis,mongodb,memcached,elasticsearch,zookeeper,"
    "kafka,cassandra,neo4j,activemq,rabbitmq,mqtt,"
    "imap,pop3,smtp"
)

# Plugins that may hang for a long time on ports of the wrong protocol
# (measured: oracle 72s, rsync/ldap 55s, rdp/telnet over 120s without
# converging), so run them only against their default ports
FSCAN_SLOW_PLUGIN_PORTS = {
    "rdp": [3389],
    "oracle": [1521, 1522, 1525],
    "telnet": [23, 2323],
    "rsync": [873],
    "ldap": [389, 636, 3268, 3269],
    "postgresql": [5432, 5433, 5434],
}

FSCAN_SUBPROCESS_TIMEOUT = 20 * 60  # process-level hard timeout for the fast pass (seconds)
FSCAN_GLOBAL_TIMEOUT = 15 * 60  # fscan -gt global timeout for the fast pass (seconds), below the process timeout
FSCAN_SLOW_SUBPROCESS_TIMEOUT = 10 * 60  # process-level hard timeout per slow plugin run (seconds)
FSCAN_SLOW_GLOBAL_TIMEOUT = 8 * 60  # fscan -gt global timeout per slow plugin run (seconds)


class FscanBrute(object):
    """Run fscan weak-password/unauthorized-access checks against the task's own open ports"""

    def __init__(self, targets):
        # targets: ["ip:port", ...], must come from the task's own port scan results
        self.targets = targets
        self.rand_str = utils.random_choices()
        self.output_files = []

    def _split_targets(self, targets):
        """fscan's -hf/-h do not accept multiple ip:port targets, so split them
        into -h hosts + -p ports. Hosts and ports both come from the task's port
        scan results, so the scan never goes beyond the task targets."""
        host_set = set()
        port_set = set()
        for target in targets:
            if ":" not in target:
                continue
            host, _, port = target.rpartition(":")
            host = host.strip()
            port = port.strip()
            if not host or not port.isdigit():
                continue
            host_set.add(host)
            port_set.add(int(port))

        return sorted(host_set), sorted(port_set)

    def _build_command(self, hosts, ports, plugins, output_path, global_timeout):
        return [FSCAN_BIN,
                "-h", ",".join(hosts),
                "-p", ",".join([str(p) for p in ports]),
                "-m", plugins,
                "-np",  # disable ping liveness probing, only check the given targets
                "-nopoc",  # weak passwords only, no POCs
                "-noredis",  # disable redis exploitation such as writing files
                "-silent", "-nopg", "-nocolor", "-lang", "en",
                "-f", "json", "-o", output_path,
                "-t", "200", "-time", "3",
                "-gt", str(global_timeout)]

    def _exec_fscan(self, targets, plugins, tag, global_timeout, subprocess_timeout):
        hosts, ports = self._split_targets(targets)
        if not hosts or not ports:
            return

        output_path = os.path.join(
            Config.TMP_PATH, "fscan_brute_{}_{}.json".format(self.rand_str, tag))
        self.output_files.append(output_path)

        command = self._build_command(hosts, ports, plugins, output_path, global_timeout)
        logger.info("fscan brute [{}]: {} hosts {} ports".format(tag, len(hosts), len(ports)))
        logger.info(" ".join(command))
        try:
            utils.exec_system(command, timeout=subprocess_timeout,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            # even when killed by a timeout, still try to parse the realtime backup file
            logger.warning("fscan brute [{}] exec error: {}".format(tag, e))

    def exec_fscan(self):
        if not os.path.exists(FSCAN_BIN):
            logger.warning("not found fscan binary: {}".format(FSCAN_BIN))
            return

        # run the fast plugins against all open ports
        self._exec_fscan(self.targets, FSCAN_FAST_PLUGINS, "fast",
                         FSCAN_GLOBAL_TIMEOUT, FSCAN_SUBPROCESS_TIMEOUT)

        # run the slow plugins only against their default ports
        for plugin, plugin_ports in FSCAN_SLOW_PLUGIN_PORTS.items():
            slow_targets = []
            for target in self.targets:
                _, _, port = target.rpartition(":")
                if port.isdigit() and int(port) in plugin_ports:
                    slow_targets.append(target)
            if not slow_targets:
                continue
            self._exec_fscan(slow_targets, plugin, plugin,
                             FSCAN_SLOW_GLOBAL_TIMEOUT, FSCAN_SLOW_SUBPROCESS_TIMEOUT)

    def _load_vuln_entries(self):
        """Prefer the complete JSON output (only written on a clean exit);
        fall back to the realtime NDJSON backup file (output.realtime.tmp) on failure"""
        entries = []
        for output_path in self.output_files:
            loaded = False
            if os.path.exists(output_path):
                try:
                    with open(output_path, "r") as f:
                        data = json.load(f)
                    entries.extend(data.get("vulns") or [])
                    loaded = True
                except Exception as e:
                    logger.warning("parse fscan output {} error: {}".format(output_path, e))

            if loaded:
                continue

            realtime_path = output_path + ".realtime.tmp"
            if not os.path.exists(realtime_path):
                continue
            try:
                with open(realtime_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        item = json.loads(line)
                        if item.get("type") == "VULN":
                            entries.append(item)
            except Exception as e:
                logger.warning("parse fscan realtime {} error: {}".format(realtime_path, e))

        return entries

    def _to_vuln_items(self, entries):
        """Convert entries into vuln documents with the same structure as xing brute plugins"""
        items = []
        seen = set()
        for entry in entries:
            details = entry.get("details") or {}
            service = details.get("service") or details.get("plugin") or ""
            target = entry.get("target") or ""
            detail_type = details.get("type")

            if detail_type == "weak_credential":
                verify_data = {
                    "username": details.get("username", ""),
                    "password": details.get("password", "")
                }
                vul_name = "{} weak password (fscan)".format(service.upper())
            elif detail_type == "vulnerability":
                vulnerability = details.get("vulnerability") or entry.get("status") or ""
                verify_data = {"vulnerability": vulnerability}
                vul_name = "{} {} (fscan)".format(service.upper(), vulnerability)
            else:
                continue

            if not target:
                continue

            key = (target, service, json.dumps(verify_data, sort_keys=True))
            if key in seen:
                continue
            seen.add(key)

            item = {
                "plg_name": "fscan_{}".format(service or "unknown"),
                "plg_type": "brute",
                "vul_name": vul_name.strip(),
                "app_name": service,
                "target": target,
                "verify_data": verify_data
            }
            items.append(item)

        return items

    def _delete_file(self):
        try:
            for output_path in self.output_files:
                for path in (output_path, output_path + ".realtime.tmp"):
                    if os.path.exists(path):
                        os.unlink(path)
        except Exception as e:
            logger.warning(e)

    def run(self):
        if not self.targets:
            return []

        self.exec_fscan()
        items = self._to_vuln_items(self._load_vuln_entries())
        self._delete_file()

        logger.info("fscan brute found {} vulns".format(len(items)))
        return items


def run_fscan_brute(targets):
    """Entry point for the fscan weak-password scan; any failure is logged and an empty list is returned"""
    try:
        return FscanBrute(targets).run()
    except Exception as e:
        logger.warning("run_fscan_brute error: {}".format(e))

    return []
