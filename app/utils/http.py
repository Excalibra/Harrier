import re


def get_title(body):
    """
    Return the title from the page source
    :param body: <title>sss</title>
    :return: sss
    """
    result = ''
    title_patten = re.compile(rb'<title>([^<]{1,200})</title>', re.I)
    title = title_patten.findall(body)
    if len(title) > 0:
        try:
            result = title[0].decode("utf-8")
        except Exception as e:
            result = title[0].decode("gbk", errors="replace")
    return result.strip()


def get_headers(conn):
    # The version field can currently only be 10 or 11

    raw = conn.raw
    version = "1.1"
    if raw.version == 10:
        version = "1.0"

    first_line = "HTTP/{} {} {}\n".format(version, raw.status, raw.reason)

    headers = str(raw._fp.headers)

    headers = headers.strip()
    if not conn.headers.get("Content-Length"):
        headers = "{}\nContent-Length: {}".format(headers, len(conn.content))

    return first_line + headers

