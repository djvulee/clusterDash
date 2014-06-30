# coding=utf-8

"""
This is the server who worker on a lot of machine, it will get a remote call from the client
"""


from rpyc.utils.server import ThreadedServer
from dash_service import WrapService

from net import NetIOCounters
from log import Logs
import threading
import time

logs = Logs()
net_io_counters = NetIOCounters()

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


def start_background_worker(args, sleep_time=3):
    def work():
        update_logs_interval = 60
        i = update_logs_interval
        while True:
            net_io_counters.update()

            # update the list of available logs every minute
            if update_logs_interval <= 0:
                logs.add_patterns(args.logs)
                i = update_logs_interval
            i -= sleep_time

            time.sleep(sleep_time)

    t = threading.Thread(target=work)
    t.daemon = True
    t.start()

def main():
    setup_logging()

    logger.info("Starting server ...")
    locale.setlocale(locale.LC_ALL, "")

    start_background_worker(args)
    wrapService = WrapService(net_io_counters)
    s = ThreadedServer(wrapService, port=5050,  protocol_config={"allow_public_attrs":True})
    s.start()

main()
