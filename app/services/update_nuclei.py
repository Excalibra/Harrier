"""
Nuclei engine + template updater, executed on the worker via Celery.

Downloads the latest nuclei release binary and the latest nuclei-templates
release, swaps them in atomically-ish (with rollback for the binary), and
records the outcome in the `system` collection so the web UI can show
version / last-updated.
"""
import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import zipfile

import requests

from app import utils

# Some environments sit behind TLS-intercepting proxies without the custom
# CA installed; the update sources are fixed projectdiscovery/GitHub URLs.
requests.packages.urllib3.disable_warnings()

NUCLEI_BIN = "/usr/bin/nuclei"
TEMPLATES_DIR = "/root/nuclei-templates"
CUSTOM_DIR = "/opt/nuclei-custom"
TEMPLATES_CONFIG = "/root/.config/nuclei/.templates-config.json"
API_NUCLEI = "https://api.github.com/repos/projectdiscovery/nuclei/releases/latest"
API_TEMPLATES = "https://api.github.com/repos/projectdiscovery/nuclei-templates/releases/latest"

logger = utils.get_logger()

STATUS_ID = "nuclei_update"


def write_status(**fields):
    fields["updated_at"] = utils.curr_date()
    utils.conn_db('system').update_one(
        {"_id": STATUS_ID}, {"$set": fields}, upsert=True)


def get_status():
    item = utils.conn_db('system').find_one({"_id": STATUS_ID}, {"log": 0})
    return item or {}


def _get_json(url):
    r = requests.get(url, timeout=30, verify=False)
    r.raise_for_status()
    return r.json()


def _download(url, max_size=600 * 1024 * 1024):
    logger.info("downloading {}".format(url))
    r = requests.get(url, timeout=600, stream=True, verify=False)
    r.raise_for_status()
    buf = io.BytesIO()
    size = 0
    for chunk in r.iter_content(chunk_size=1 << 20):
        size += len(chunk)
        if size > max_size:
            raise Exception("download too large: {}".format(url))
        buf.write(chunk)
    buf.seek(0)
    return buf


def _run_version(binary):
    out = subprocess.check_output([binary, "-version"], timeout=60,
                                  stderr=subprocess.STDOUT).decode(errors="replace")
    for token in out.split():
        if token.startswith("v") and token[1:2].isdigit():
            return token
    return "unknown"


def _count_templates():
    total = 0
    for _root, _dirs, files in os.walk(TEMPLATES_DIR):
        total += sum(1 for f in files if f.endswith(".yaml"))
    return total


def update_engine(log):
    meta = _get_json(API_NUCLEI)
    tag = meta["tag_name"]
    current = _run_version(NUCLEI_BIN) if os.path.exists(NUCLEI_BIN) else "none"
    if current == tag:
        log.append("engine already latest ({})".format(tag))
        return tag

    asset = next(a for a in meta["assets"]
                 if a["name"] == "nuclei_{}_linux_amd64.zip".format(tag.lstrip("v")))
    buf = _download(asset["browser_download_url"])
    zf = zipfile.ZipFile(buf)
    tmpdir = tempfile.mkdtemp()
    zf.extract("nuclei", tmpdir)
    new_bin = os.path.join(tmpdir, "nuclei")
    os.chmod(new_bin, 0o755)

    version = _run_version(new_bin)  # raises if the binary does not run
    backup = NUCLEI_BIN + ".bak"
    if os.path.exists(NUCLEI_BIN):
        shutil.copy2(NUCLEI_BIN, backup)
    shutil.copy2(new_bin, NUCLEI_BIN)
    try:
        _run_version(NUCLEI_BIN)
    except Exception:
        if os.path.exists(backup):
            shutil.copy2(backup, NUCLEI_BIN)
        raise
    shutil.rmtree(tmpdir, ignore_errors=True)
    log.append("engine {} -> {}".format(current, version))
    return version


def update_templates(log):
    meta = _get_json(API_TEMPLATES)
    tag = meta["tag_name"]
    url = "https://codeload.github.com/projectdiscovery/nuclei-templates/tar.gz/refs/tags/{}".format(tag)
    buf = _download(url)

    tmpdir = tempfile.mkdtemp()
    with tarfile.open(fileobj=buf, mode="r:gz") as tf:
        tf.extractall(tmpdir)
    extracted = os.path.join(tmpdir, os.listdir(tmpdir)[0])

    old = TEMPLATES_DIR + ".old"
    if os.path.exists(old):
        shutil.rmtree(old)
    if os.path.exists(TEMPLATES_DIR):
        os.rename(TEMPLATES_DIR, old)
    shutil.move(extracted, TEMPLATES_DIR)
    shutil.rmtree(old, ignore_errors=True)
    shutil.rmtree(tmpdir, ignore_errors=True)

    # re-apply harrier custom templates, they are not part of the release
    if os.path.isdir(CUSTOM_DIR):
        dst = os.path.join(TEMPLATES_DIR, "custom")
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(CUSTOM_DIR, dst)

    # keep the version marker honest so nuclei stops warning about updates
    try:
        with open(TEMPLATES_CONFIG) as f:
            cfg = json.load(f)
        cfg["nuclei-templates-version"] = tag
        cfg["nuclei-templates-latest-version"] = tag
        with open(TEMPLATES_CONFIG, "w") as f:
            json.dump(cfg, f)
    except Exception as e:
        logger.warning("templates-config update failed: {}".format(e))

    count = _count_templates()
    log.append("templates -> {} ({} templates)".format(tag, count))
    return tag, count


def run_update():
    log = []
    write_status(status="running", log="")
    try:
        engine_version = update_engine(log)
        templates_version, template_count = update_templates(log)
        write_status(status="done",
                     engine_version=engine_version,
                     templates_version=templates_version,
                     template_count=template_count,
                     log="\n".join(log))
        logger.info("nuclei update done: {}".format("; ".join(log)))
    except Exception as e:
        logger.exception(e)
        write_status(status="error", log="\n".join(log + ["error: {}".format(e)]))
