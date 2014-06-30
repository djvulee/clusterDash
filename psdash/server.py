# coding=utf-8

"""
This is the server who worker on a lot of machine, it will get a remote call from the client
"""


from rpyc.utils.server import ThreadedServer
from dash_service import WrapService

from net import NetIOCounters
import threading
import time

net_io_counters = NetIOCounters()

def start_background_worker(sleep_time=3):
    def work():
        update_logs_interval = 60
        i = update_logs_interval
        while True:
            net_io_counters.update()

            # update the list of available logs every minute
            if update_logs_interval <= 0:
                #logs.add_patterns(args.logs)
                i = update_logs_interval
            i -= sleep_time

            time.sleep(sleep_time)

    t = threading.Thread(target=work)
    t.daemon = True
    t.start()

def main():
    #setup_logging()

    #logger.info("Starting clusterdash v0.1.0")
    #locale.setlocale(locale.LC_ALL, "")

    start_background_worker()
    wrapService = WrapService(net_io_counters)
    s = ThreadedServer(wrapService)
    s.start()

main()
