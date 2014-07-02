# coding=utf-8
import argparse
from flask import Flask, render_template, request, session, jsonify, Response, Blueprint
import logging
import psutil
import platform
import socket
import os
from datetime import datetime
import time
import threading
import uuid
import locale
from log import Logs
from net import NetIOCounters, get_interface_addresses

from client import Client

import collections

logs = Logs()

net_io_counters = NetIOCounters()
logger = logging.getLogger("psdash.web")

def socket_constants(prefix):
    return dict((getattr(socket, n), n) for n in dir(socket) if n.startswith(prefix))

socket_families = socket_constants('AF_')
socket_types = socket_constants('SOCK_')


dash_client = Client([["husky003", 5050]])


app = Flask(__name__)
app.config.from_envvar("PSDASH_CONFIG", silent=True)

app_url_prefix = app.config.get("PSDASH_URL_PREFIX")
if app_url_prefix:
    app_url_prefix = "/" + app_url_prefix.strip("/")

psdashapp = Blueprint(
    "psdash",
    __name__,
    url_prefix=app_url_prefix,
    static_folder="static"
)

# If the secret key is not read from the config just set it to something.
if not app.secret_key:
    app.secret_key = "whatisthissourcery"


allowed_remote_addrs = []


# Patch the built-in, but not working, filesizeformat filter for now.
# See https://github.com/mitsuhiko/jinja2/pull/59 for more info.
@app.template_filter()
def filesizeformat(value, binary=False):
    """Format the value like a 'human-readable' file size (i.e. 13 kB,
    4.1 MB, 102 Bytes, etc).  Per default decimal prefixes are used (Mega,
    Giga, etc.), if the second parameter is set to `True` the binary
    prefixes are used (Mebi, Gibi).
    """
    bytes = float(value)
    base = binary and 1024 or 1000
    prefixes = [
        (binary and 'KiB' or 'kB'),
        (binary and 'MiB' or 'MB'),
        (binary and 'GiB' or 'GB'),
        (binary and 'TiB' or 'TB'),
        (binary and 'PiB' or 'PB'),
        (binary and 'EiB' or 'EB'),
        (binary and 'ZiB' or 'ZB'),
        (binary and 'YiB' or 'YB')
    ]
    if bytes == 1:
        return '1 Byte'
    elif bytes < base:
        return '%d Bytes' % bytes
    else:
        for i, prefix in enumerate(prefixes):
            unit = base ** (i + 2)
            if bytes < unit:
                return '%.1f %s' % ((base * bytes / unit), prefix)
        return '%.1f %s' % ((base * bytes / unit), prefix)


@app.before_first_request
def load_allowed_remote_addrs():
    addrs = app.config.get("PSDASH_ALLOWED_REMOTE_ADDRESSES")
    if addrs:
        app.logger.info("Setting up allowed remote addresses list.")
        for addr in addrs.split(","):
            allowed_remote_addrs.append(addr.strip())


@app.before_request
def check_access():
    if allowed_remote_addrs:
        if request.remote_addr not in allowed_remote_addrs:
            app.logger.info(
                "Returning 401 for client %s as address is not in allowed addresses.",
                request.remote_addr
            )
            app.logger.debug("Allowed addresses: %s", allowed_remote_addrs)
            return "Access denied", 401

    username = app.config.get("PSDASH_AUTH_USERNAME")
    password = app.config.get("PSDASH_AUTH_PASSWORD")
    if username and password:
        auth = request.authorization
        if not auth or auth.username != username or auth.password != password:
            return Response(
                "Access deined",
                401,
                {'WWW-Authenticate': 'Basic realm="psDash login required"'}
            )


@app.before_request
def setup_client_id():
    if "client_id" not in session:
        client_id = uuid.uuid4()
        app.logger.debug("Creating id for client: %s", client_id)
        session["client_id"] = client_id


@psdashapp.errorhandler(404)
def page_not_found(e):
    app.logger.debug("Client tried to load an unknown route: %s", e)
    return render_template("error.html", error="Page not found."), 404


@psdashapp.errorhandler(psutil.AccessDenied)
def access_denied(e):
    errmsg = "Access denied to %s (pid %d)." % (e.name, e.pid)
    return render_template("error.html", error=errmsg), 401


@psdashapp.errorhandler(psutil.NoSuchProcess)
def access_denied(e):
    errmsg = "No process with pid %d was found." % e.pid
    return render_template("error.html", error=errmsg), 401


@psdashapp.route("/<string:hostname>")
def index(hostname):
    tmp = dash_client.get_hostname_overview(hostname)

    data = {
        "os": tmp["os"],
        "hostname": tmp["hostname"],
        "uptime": tmp["uptime"],
        "load_avg": tmp["load_avg"],
        "cpus": tmp["cpus"],
        "vmem": tmp["vmem"],
        "swap": tmp["swap"],
        "disks": tmp["disks"],
        "cpu_percent": tmp["cpu_percent"],
        "users": tmp["users"],
        "net_interfaces": tmp["net_interfaces"],
        "page": "overview",
        "is_xhr": request.is_xhr
    }

    return render_template("index.html", **data)

@psdashapp.route("/<string:hostname>/processes", defaults={"sort": "cpu", "order": "desc"})
@psdashapp.route("/<string:hostname>/processes/<string:sort>")
@psdashapp.route("/<string:hostname>/processes/<string:sort>/<string:order>")
def processes(hostname, sort="pid", order="asc"):
    processes  = dash_client.get_hostname_processes(hostname)

    return render_template(
        "processes.html",
        processes=procs,
        sort=sort,
        order=order,
        page="processes",
        is_xhr=request.is_xhr
    )


@psdashapp.route("/<string:hostname>/process/<int:pid>/limits")
def process_limits(hostname, pid):
    (limits, p) = dash_client.get_process_limits(hostname)

    return render_template(
        "process/limits.html",
        limits=limits,
        process=p,
        section="limits",
        page="processes",
        is_xhr=request.is_xhr
    )

@psdashapp.route("/<string:hostname>/process/<int:pid>", defaults={"section": "overview"})
@psdashapp.route("/<string:hostname>/process/<int:pid>/<string:section>")
def process(hostname, pid, section):
    tmp_context = dash_client.get_hostname_process(hostname, pid, section)

    if tmp_context == "error":
        errmsg = "Invalid subsection when trying to view process %d" % pid
        return render_template("error.html", error=errmsg), 404
    else:
        context = {
            "process": tmp_context["process"],
            "section": tmp_context["section"],
            "page": "processes",
            "is_xhr": request.is_xhr
        }
        if section == "environment":
            context["process_environ"] = tmp_context["process_environ"]
        return render_template("process/%s.html" % section, **context)

@psdashapp.route("/<string:hostname>/network")
def view_networks(hostname):
    (netifs, conns) = dash_client.get_hostname_network(hostname)

    return render_template(
        "network.html",
        page="network",
        network_interfaces=netifs,
        net_connections=conns,
        socket_families=socket_families,
        socket_types=socket_types,
        is_xhr=request.is_xhr
    )


@psdashapp.route("/<string:hostname>/disks")
def view_disks():
    (disks, io_counters) = dash_client.get_hostname_disk(hostname)

    return render_template(
        "disks.html",
        page="disks",
        disks=disks,
        io_counters=io_counters,
        is_xhr=request.is_xhr
    )

@psdashapp.route("/logs")
def view_logs():
    available_logs = dash_client.get_logs()[0]

    return render_template(
        "logs.html",
        page="logs",
        logs=available_logs,
        is_xhr=request.is_xhr
    )

@psdashapp.route("/log")
def view_log():
    (content, filename) = dash_client.get_log()[0]

    if content == "error":
        return render_template("error.html", error="Only files passed through args are allowed."), 401
    else:
        return render_template("log.html", content=content, filename=filename)

@psdashapp.route("/log/read")
def read_log():
    read_log = dash_client.get_read_log()[0]

    return read_log

@psdashapp.route("/log/read_tail")
def read_log_tail():
    read_log_tail = dash_client.get_read_log_tail[0]

    return read_log_tail

@psdashapp.route("/log/search")
def search_log():
    search_log = dash_client.get_search_log[0]

    return search_log


def parse_args():
    parser = argparse.ArgumentParser(
        description="psdash %s - system information web dashboard" % "0.3.0"
    )
    parser.add_argument(
        "-l", "--log",
        action="append",
        dest="logs",
        default=[],
        metavar="path",
        help="log files to make available for psdash. Patterns (e.g. /var/log/**/*.log) are supported. "
             "This option can be used multiple times."
    )
    parser.add_argument(
        "-b", "--bind",
        action="store",
        dest="bind_host",
        default="0.0.0.0",
        metavar="host",
        help="host to bind to. Defaults to 0.0.0.0 (all interfaces)."
    )
    parser.add_argument(
        "-p", "--port",
        action="store",
        type=int,
        dest="port",
        default=5000,
        metavar="port",
        help="port to listen on. Defaults to 5000."
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        dest="debug",
        help="enables debug mode."
    )

    return parser.parse_args()


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s"
    )

    logging.getLogger("werkzeug").setLevel(logging.WARNING)


def enable_verbose_logging():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("werkzeug").setLevel(logging.INFO)
    logger.setLevel(logging.DEBUG)


def main():
    setup_logging()

    locale.setlocale(locale.LC_ALL, "")

    args = parse_args()
    if args.debug:
        enable_verbose_logging()

    logs.add_patterns(args.logs)

    logger.info("Listening on %s:%s", args.bind_host, args.port)

    app.register_blueprint(psdashapp)

    app.run(
        host=args.bind_host,
        port=args.port,
        debug=args.debug,
        threaded=True
    )


if __name__ == '__main__':
    main()
