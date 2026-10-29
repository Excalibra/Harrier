#coding: utf-8

from flask import make_response, request
from flask_restx import Resource, Namespace
from openpyxl import Workbook
from bson import ObjectId
import re
import json
from collections import Counter
from openpyxl.writer.excel import save_virtual_workbook
from openpyxl.styles import Font, Color
from xml.sax.saxutils import escape
from app.utils import get_logger, auth
from app import utils
from urllib.parse import quote

ns = Namespace('export', description="Task report export API")

logger = get_logger()

REPORT_COLLECTIONS = [
    ("site", "Sites"),
    ("ip", "IPs"),
    ("domain", "Domains"),
    ("service", "Services"),
    ("cert", "Certificates"),
    ("url", "URLs"),
    ("vuln", "PoC Vulnerabilities"),
    ("nuclei_result", "Nuclei Findings"),
    ("fileleak", "File Leaks"),
    ("wih", "WIH"),
]

SKIP_KEYS = {"_id", "task_id", "save_date"}


@ns.route('/<string:task_id>')
class HarrierExport(Resource):
    @auth
    def get(self, task_id):
        """
        Export report, format: xlsx (default) / xml / html
        """
        task_data = get_task_data(task_id)
        if not task_data:
            return "not found"

        fmt = request.args.get("format", "xlsx").lower()
        target = task_data["target"].replace("/", "_")[:20]

        if fmt == "xml":
            payload = export_xml(task_id, task_data)
            response = make_response(payload)
            response.headers['Content-Type'] = 'application/xml; charset=utf-8'
            filename = "Harrier_Report_{}.xml".format(target)
        elif fmt == "html":
            payload = export_html(task_id, task_data)
            response = make_response(payload)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            filename = "Harrier_Report_{}.html".format(target)
        else:
            payload = export_harrier(task_id)
            response = make_response(payload)
            response.headers['Content-Type'] = 'application/octet-stream'
            filename = "Harrier_Asset_Report_{}.xlsx".format(target)

        response.headers["Content-Disposition"] = "attachment; filename={}".format(quote(filename))
        return response




def get_task_data(task_id):
    try:
        task_data = utils.conn_db('task').find_one({'_id': ObjectId(task_id)})
        return task_data
    except Exception as e:
        pass


def get_ip_data(task_id):
    data =  utils.conn_db('ip').find({'task_id': task_id})
    return data


def get_site_data(task_id):
    data = utils.conn_db('site').find({'task_id': task_id})
    return data


def get_domain_data(task_id):
    data = utils.conn_db('domain').find({'task_id': task_id})
    return data


def port_service_product_statist(task_id):
    ip_data = get_ip_data(task_id)
    total = 0
    port_info_list = []
    for item in ip_data:
        if not item["port_info"]:
            continue
        port_info_list.extend(item["port_info"])
        total += len(item["port_info"])

    counter = Counter([info["port_id"] for info in port_info_list])
    top_20 = counter.most_common(20)
    port_percent_list = []
    for port_info in top_20:
        port_id, amount = port_info
        item = {
            "port_id" : port_id,
            "amount" : amount,
            "percent" : "{:.2f}%".format((amount *100.0 ) / total)
        }
        port_percent_list.append(item)

    service_name_list = []
    for info in port_info_list:
        if  not  info.get("product"):
            continue
        if info["product"] or info["version"]:
            service_name = info["service_name"]
            if service_name == "https-alt":
                service_name = "https"

            service_name_list.append(service_name)

    service_top_20 = Counter(service_name_list).most_common(20)
    service_percent_list = []
    for port_info in service_top_20:
        service_name, amount = port_info
        item = {
            "service_name" : service_name,
            "amount" : amount,
            "percent" : "{:.2f}%".format((amount *100.0 ) / len(service_name_list))
        }
        service_percent_list.append(item)



    product_name_list = []
    for info in port_info_list:
        if not info.get("product"):
            continue
        product = info["product"]
        if product and "**" not in product:
            product = product.strip()
            product_name_list.append(product)

    product_top_20 = Counter(product_name_list).most_common(20)
    product_percent_list = []
    for info in product_top_20:
        product, amount = info
        item = {
            "product" : product,
            "amount" : amount,
            "percent" : "{:.2f}%".format((amount *100.0 ) / len(product_name_list))
        }
        product_percent_list.append(item)

    statist = {
        "port_total": total, #total number of open ports
        "port_percent_list": port_percent_list, #top 20 open ports with percentage details
        "service_total": len(service_name_list),  #total number of system service types
        "service_percent_list": service_percent_list, #top 20 system service types with percentage details
        "product_total": len(product_name_list), #total number of product types
        "product_percent_list": product_percent_list ##top 20 product types with percentage details
    }
    return statist



class SaveTask(object):
    """docstring for ClassName"""

    def __init__(self, task_id):
        self.task_id = task_id
        self.wb = Workbook()
        self.is_ip_task = False

    def set_style(self, ws):
        font = Font(name="Consolas", color="111111")
        column = "ABCDEFGHIJKLMNO"
        for x in column:
            for y in range(1, 256):
                ws["{}{}".format(x,y)].font = font

    def build_service_xl(self):
        ws = self.wb.create_sheet(title="System Services")
        ws.column_dimensions['A'].width = 22.0
        ws.column_dimensions['B'].width = 10.0
        ws.column_dimensions['C'].width = 20.0
        ws.column_dimensions['D'].width = 40.0

        column_tilte = ["IP", "Port", "Service", "Product", "Version"]
        ws.append(column_tilte)
        for item in get_ip_data(self.task_id):
            for port_info in item["port_info"]:
                row = []
                row.append(item["ip"])
                row.append("{}".format(port_info["port_id"]))
                row.append(port_info["service_name"])
                row.append(port_info.get("product", ""))
                row.append(port_info.get("version", ""))
                ws.append(row)

        self.set_style(ws)

    def build_ip_xl(self):
        ws = self.wb.create_sheet(title="IP")
        ws.column_dimensions['A'].width = 22.0
        ws.column_dimensions['B'].width = 50.0
        ws.column_dimensions['C'].width = 10.0
        ws.column_dimensions['D'].width = 25.0
        ws.column_dimensions['E'].width = 55.0
        if self.is_ip_task:
            ws.column_dimensions['F'].width = 55.0
            column_tilte = ["IP", "Ports", "Open Port Count", "Geo", "AS Number", "OS"]
            ws.append(column_tilte)
            for item in get_ip_data(self.task_id):
                row = []
                row.append(item["ip"])

                port_ids = [str(x["port_id"]) for x in item["port_info"]]
                row.append(" \r\n".join(port_ids))
                row.append(len(item["port_info"]))
                if "country_name" in item["geo_city"]:
                    row.append("{}/{}".format(item["geo_city"]["country_name"],
                                              item["geo_city"]["region_name"]))
                    row.append(item["geo_asn"].get("organization", ""))
                else:
                    row.append("")
                    row.append("")

                osname = ""
                if item.get("os_info"):
                    osname = item["os_info"]["name"]
                row.append(osname)
                ws.append(row)
        else:
            ws.column_dimensions['F'].width = 60.0
            ws.column_dimensions['G'].width = 40.0
            ws.column_dimensions['H'].width = 40.0
            ws.column_dimensions['I'].width = 20.0
            column_tilte = ["IP", "Port Info", "Open Port Count", "Geo", "AS Number"]
            column_tilte.append("Domain")
            column_tilte.append("OS")
            column_tilte.append("CDN")
            column_tilte.append("Type")
            ws.append(column_tilte)
            for item in get_ip_data(self.task_id):
                row = []
                row.append(item["ip"])

                port_ids = [str(x["port_id"]) for x in item["port_info"]]
                row.append(" \r\n".join(port_ids))

                row.append(len(item["port_info"]))
                if "country_name" in item["geo_city"]:
                    row.append("{}/{}".format(item["geo_city"]["country_name"],
                                              item["geo_city"]["region_name"]))
                    row.append(item["geo_asn"].get("organization", ""))
                else:
                    row.append("")
                    row.append("")

                row.append(" \r\n".join(item.get("domain", [])))

                osname = ""
                if item.get("os_info"):
                    osname = item["os_info"]["name"]
                row.append(osname)
                row.append(item.get("cdn_name", ""))
                row.append(item.get("ip_type", ""))
                ws.append(row)

        self.set_style(ws)

    def ignore_illegal(self, content):
        ILLEGAL_CHARACTERS_RE = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]')
        content = ILLEGAL_CHARACTERS_RE.sub(r'', content)
        return content

    def build_site_xl(self):
        ws = self.wb.active
        ws.column_dimensions['A'].width = 35.0
        ws.column_dimensions['B'].width = 40.0
        ws.column_dimensions['C'].width = 60.0
        ws.column_dimensions['D'].width = 20.0
        ws.column_dimensions['E'].width = 30.0
        ws.title = "Sites"
        column_tilte = ["Site", "Title", "Fingerprint", "Status Code", "Favicon Hash"]
        ws.append(column_tilte)
        for item in get_site_data(self.task_id):
            row = []
            row.append(self.ignore_illegal(item["site"]))
            row.append(self.ignore_illegal(item["title"]))
            row.append(" \r\n".join([self.ignore_illegal(x["name"]) for x in item["finger"]]))
            row.append(item["status"])
            row.append(item["favicon"].get("hash", ""))
            ws.append(row)

        self.set_style(ws)

    def build_domain_xl(self):
        ws = self.wb.create_sheet(title="Domains")
        ws.column_dimensions['A'].width = 30.0
        ws.column_dimensions['B'].width = 20.0
        ws.column_dimensions['C'].width = 50.0
        ws.column_dimensions['D'].width = 50.0

        column_tilte = ["Domain", "Record Type", "Record Value", "Related IP"]

        ws.append(column_tilte)
        for item in get_domain_data(self.task_id):
            row = []
            row.append(item["domain"])
            row.append(item["type"])
            row.append(" \r\n".join(item["record"]))
            row.append(" \r\n".join(item["ips"]))
            ws.append(row)

        self.set_style(ws)

    def build_statist(self):
        statist = port_service_product_statist(self.task_id)
        ws = self.wb.create_sheet(title="Asset Statistics")
        ws.column_dimensions['A'].width = 20.0
        ws.column_dimensions['F'].width = 20.0
        ws.column_dimensions['K'].width = 40.0
        ws["A1"] = "Port Statistics"
        ws["F1"] = "Service Statistics"
        ws["K1"] = "Product Statistics"

        ports = ["Port", "Count", "Percent"]
        port_percent_list = statist["port_percent_list"]
        port_total = statist["port_total"]
        for port_info in port_percent_list:
            ports.append(port_info["port_id"])
            ports.append(port_info["amount"])
            ports.append(port_info["percent"])

        cnt = 0
        for row in range(5, 27):
            for col in range(1, 4):
                if cnt >= len(ports):
                    continue
                ws.cell(column=col, row=row, value=ports[cnt])
                cnt += 1

        ws["A27"] = "Total Open Ports"
        ws["A28"] = port_total

        services = ["Service", "Count", "Percent"]
        service_percent_list = statist["service_percent_list"]
        if len(service_percent_list) >= 0:
            service_total = statist["service_total"]
            for port_info in service_percent_list:
                services.append(port_info["service_name"])
                services.append(port_info["amount"])
                services.append(port_info["percent"])
            cnt = 0
            for row in range(5, 27):
                for col in range(6, 9):
                    if cnt >= len(services):
                        continue
                    ws.cell(column=col, row=row, value=services[cnt])
                    cnt += 1
            ws["F27"] = "Total Service Types"
            ws["F28"] = service_total

        product = ["Product", "Count", "Percent"]
        product_percent_list = statist["product_percent_list"]
        if len(product_percent_list) >= 0:
            product_total = statist["product_total"]
            for port_info in product_percent_list:
                product.append(port_info["product"])
                product.append(port_info["amount"])
                product.append(port_info["percent"])
            cnt = 0
            for row in range(5, 27):
                for col in range(11, 14):
                    if cnt >= len(product):
                        continue
                    ws.cell(column=col, row=row, value=product[cnt])
                    cnt += 1
            ws["K27"] = "Total Product Types"
            ws["K28"] = product_total

        self.set_style(ws)

    def build_generic_xl(self, title, docs, max_cell=30000):
        docs = list(docs)
        if not docs:
            return
        ws = self.wb.create_sheet(title=title[:31])
        fields = []
        for doc in docs[:200]:
            for key in doc:
                if key in SKIP_KEYS or key in fields:
                    continue
                fields.append(key)
        ws.append(fields)
        for doc in docs:
            row = []
            for field in fields:
                value = doc.get(field, "")
                if isinstance(value, (list, dict)):
                    value = json.dumps(value, ensure_ascii=False, default=str)
                value = self.ignore_illegal(str(value))[:max_cell]
                row.append(value)
            ws.append(row)
        self.set_style(ws)

    def build_risk_xl(self):
        self.build_generic_xl("PoC Vulnerabilities",
                              utils.conn_db('vuln').find({'task_id': self.task_id}))
        self.build_generic_xl("Nuclei Findings",
                              utils.conn_db('nuclei_result').find({'task_id': self.task_id}))
        self.build_generic_xl("File Leaks",
                              utils.conn_db('fileleak').find({'task_id': self.task_id}))
        self.build_generic_xl("WIH",
                              utils.conn_db('wih').find({'task_id': self.task_id}))

    def run(self):
        task_data = get_task_data(self.task_id)
        if not task_data:
            print("not found {}".format(self.task_id))
            return

        domain = task_data["target"].replace("/", "_")[:20]

        if re.findall(r"\b\d+\.\d+\.\d+\.\d+", domain):
            self.is_ip_task = True
        else:
            if task_data.get("type", "") == "ip":
                self.is_ip_task = True

        self.build_site_xl()
        self.build_ip_xl()
        self.build_service_xl()
        if not self.is_ip_task:
            self.build_domain_xl()

        self.build_statist()
        self.build_risk_xl()

        return save_virtual_workbook(self.wb)


def export_harrier(task_id):
    task_id = task_id.strip()
    save = SaveTask(task_id)
    return save.run()


def get_collection_docs(task_id):
    """Return [(collection, english_title, [docs])] for a task report."""
    sections = []
    for coll, title in REPORT_COLLECTIONS:
        docs = list(utils.conn_db(coll).find({'task_id': task_id}))
        sections.append((coll, title, docs))
    return sections


def xml_value(tag, value, indent):
    pad = " " * indent
    if isinstance(value, dict):
        inner = "".join(xml_value(k, v, indent + 2) for k, v in value.items())
        return "{}<{}>\n{}{}</{}>\n".format(pad, tag, inner, pad, tag)
    if isinstance(value, list):
        inner = "".join(xml_value("item", v, indent + 2) for v in value)
        return "{}<{}>\n{}{}</{}>\n".format(pad, tag, inner, pad, tag)
    return "{}<{}>{}</{}>\n".format(pad, tag, escape(str(value)), tag)


def export_xml(task_id, task_data):
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<harrier_report>']
    out.append(xml_value("task", {k: v for k, v in task_data.items() if k != "_id"}, 2))
    for coll, title, docs in get_collection_docs(task_id):
        out.append('  <section name="{}">\n'.format(escape(title)))
        for doc in docs:
            out.append(xml_value(coll, {k: v for k, v in doc.items() if k != "_id"}, 4))
        out.append('  </section>\n')
    out.append('</harrier_report>')
    return "".join(out)


def export_html(task_id, task_data):
    parts = ["""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Harrier Report - {}</title>
<style>
body {{ font-family: Helvetica, Arial, sans-serif; margin: 32px; color: #222; }}
h1 {{ border-bottom: 3px solid #c0392b; padding-bottom: 8px; }}
h2 {{ margin-top: 32px; color: #c0392b; }}
table {{ border-collapse: collapse; width: 100%; font-size: 12px; }}
th, td {{ border: 1px solid #bbb; padding: 4px 8px; text-align: left; vertical-align: top; word-break: break-all; }}
th {{ background: #f2f2f2; }}
.meta td:first-child {{ font-weight: bold; width: 200px; }}
@media print {{ body {{ margin: 8mm; }} }}
</style></head><body>""".format(escape(str(task_data.get("target", ""))))]

    parts.append("<h1>Harrier Scan Report</h1><table class=\"meta\">")
    for key in ("name", "target", "status", "type", "start_time", "end_time"):
        parts.append("<tr><td>{}</td><td>{}</td></tr>".format(
            escape(key), escape(str(task_data.get(key, "")))))
    parts.append("</table>")

    for coll, title, docs in get_collection_docs(task_id):
        parts.append("<h2>{} ({})</h2>".format(escape(title), len(docs)))
        if not docs:
            continue
        fields = []
        for doc in docs[:200]:
            for key in doc:
                if key in SKIP_KEYS or key in fields:
                    continue
                fields.append(key)
        parts.append("<table><tr>")
        for field in fields:
            parts.append("<th>{}</th>".format(escape(field)))
        parts.append("</tr>")
        for doc in docs:
            parts.append("<tr>")
            for field in fields:
                value = doc.get(field, "")
                if isinstance(value, (list, dict)):
                    value = json.dumps(value, ensure_ascii=False, default=str)
                parts.append("<td>{}</td>".format(escape(str(value))[:2000]))
            parts.append("</tr>")
        parts.append("</table>")

    parts.append("</body></html>")
    return "".join(parts)
