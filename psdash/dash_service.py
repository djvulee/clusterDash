# coding=utf-8


"""
This is the basic defined services
"""


from rpyc import Service

from datetime import datetime

from net import NetIOCounters, get_interface_addresses

import psutil
import socket
import os
import platform

import copy
import pickle



def WrapService(net_io_counters, logs):
    class DashService(Service):
        def get_disk(self, all_partitions=False):
            disks = [ (dp, psutil.disk_usage(dp.mountpoint)) for dp in psutil.disk_partitions(all_partitions) ]
            disks.sort(key=lambda d: d[1].total, reverse=True)

            return disks

        def get_process_environ(self, pid):
            with open("/proc/%d/environ" % pid) as f:
                contents = f.read()
                env_vars = dict(row.split("=") for row in contents.split("\0") if "=" in row)

            return env_vars

        def exposed_get_disk(self):
            disk = self.get_disk(True)

            io_counters = psutil.disk_io_counters(perdisk=True).items()
            io_counters.sort(key=lambda x: x[1].read_count, reverse=True)

            return pickle.dumps((disk, io_counters))

        def exposed_get_network(self):
            netifs = self.get_network_interface()
            netifs.sort(key=lambda x: x.get("bytes_sent"), reverse=True)

            conns = psutil.net_connections()
            conns.sort(key=lambda x: x.status)

            return pickle.dumps((netifs, conns))

        def exposed_get_processes(self, sort, order):
            procs = []
            for p in psutil.process_iter():
                rss, vms = p.memory_info()

                # format created date from unix-timestamp
                dt = datetime.fromtimestamp(p.create_time())
                created = dt.strftime("%Y-%m-%d %H:%M:%S")

                proc = {
                    "pid": p.pid,
                    "name": p.name().decode("utf-8"),
                    "cmdline": u" ".join(arg.decode("utf-8") for arg in p.cmdline()),
                    "username": p.username().decode("utf-8"),
                    "status": p.status(),
                    "created": created,
                    "rss": rss,
                    "vms": vms,
                    "memory": p.memory_percent(),
                    "cpu": p.cpu_percent(0)
                }

                procs.append(proc)

            procs.sort(
                key=lambda x: x.get(sort),
                reverse=True if order != "asc" else False
            )

            return pickle.dumps(procs)


        def exposed_get_process_limits(self):
            p = psutil.Process(pid)

            limits = {
                "RLIMIT_AS": p.rlimit(psutil.RLIMIT_AS),
                "RLIMIT_CORE": p.rlimit(psutil.RLIMIT_CORE),
                "RLIMIT_CPU": p.rlimit(psutil.RLIMIT_CPU),
                "RLIMIT_DATA": p.rlimit(psutil.RLIMIT_DATA),
                "RLIMIT_FSIZE": p.rlimit(psutil.RLIMIT_FSIZE),
                "RLIMIT_LOCKS": p.rlimit(psutil.RLIMIT_LOCKS),
                "RLIMIT_MEMLOCK": p.rlimit(psutil.RLIMIT_MEMLOCK),
                "RLIMIT_MSGQUEUE": p.rlimit(psutil.RLIMIT_MSGQUEUE),
                "RLIMIT_NICE": p.rlimit(psutil.RLIMIT_NICE),
                "RLIMIT_NOFILE": p.rlimit(psutil.RLIMIT_NOFILE),
                "RLIMIT_NPROC": p.rlimit(psutil.RLIMIT_NPROC),
                "RLIMIT_RSS": p.rlimit(psutil.RLIMIT_RSS),
                "RLIMIT_RTPRIO": p.rlimit(psutil.RLIMIT_RTPRIO),
                "RLIMIT_RTTIME": p.rlimit(psutil.RLIMIT_RTTIME),
                "RLIMIT_SIGPENDING": p.rlimit(psutil.RLIMIT_SIGPENDING),
                "RLIMIT_STACK": p.rlimit(psutil.RLIMIT_STACK)
            }

            return pickle.dumps((limits, p))

        def exposed_get_process(self, pid, section):
            valid_sections = [
                "overview",
                "threads",
                "files",
                "connections",
                "memory",
                "environment",
                "children"
            ]

            if section not in valid_sections:
                return "error"

            context = {
                "process": psutil.Process(pid),
                "section": section,
            }

            if section == "environment":
                context["process_environ"] = self.get_process_environ(pid)

            return  context

        def get_user(self):
            users = []
            for u in psutil.users():
                dt = datetime.fromtimestamp(u.started)
                user = {
                        "name": u.name.decode("utf-8"),
                        "terminal": u.terminal,
                        "started": dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "host": u.host.decode("utf-8")
                }

                users.append(user)

            return users


        def get_network_interface(self):
            io_counters = net_io_counters.get()
            addresses = get_interface_addresses()

            for inf in addresses:
                inf.update(io_counters.get(inf["name"], {}))

            return addresses

        def exposed_get_overview(self):
            load_avg = os.getloadavg()
            uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
            disks = self.get_disk()
            users = self.get_user()

            netifs = self.get_network_interface()
            netifs.sort(key=lambda x: x.get("bytes_sent"), reverse=True)

            data = {
                    "os": platform.platform().decode("utf-8"),
                    "hostname": socket.gethostname().decode("utf-8"),
                    "uptime": str(uptime).split(".")[0],
                    "load_avg": load_avg,
                    "cpus": psutil.cpu_count(),
                    "vmem": psutil.virtual_memory(),
                    "swap": psutil.swap_memory(),
                    "disks": disks,
                    "cpu_percent": psutil.cpu_times_percent(0),
                    "users": users,
                    "net_interfaces": netifs,
                    "page": "overview",
            }

            return pickle.dumps(data)


        def exposed_get_logs(self):
            available_logs = []
            for log in logs.get_available():
                try:
                    stat = os.stat(log.filename)
                except OSError:
                    logger.warning("Could not stat %s, removing from available logs", log.filename)
                    logs.remove_available(log.filename)
                    continue

                dt = datetime.fromtimestamp(stat.st_atime)
                last_access = dt.strftime("%Y-%m-%d %H:%M:%S")

                dt = datetime.fromtimestamp(stat.st_mtime)
                last_modification = dt.strftime("%Y-%m-%d %H:%M:%S")

                available_logs.append({
                    "filename": log.filename,
                    "size": stat.st_size,
                    "last_access": last_access,
                    "last_modification": last_modification
                })

            available_logs.sort(cmp=lambda x1, x2: locale.strcoll(x1["filename"], x2["filename"]))


            return available_logs

        def exposed_get_log(self):
            filename = request.args["filename"]

            try:
                log = logs.get(filename, key=session.get("client_id"))
                log.set_tail_position()
                content = log.read()
            except KeyError:
                return ("error", "no such file")

            return (content, filename)

        def exposed_get_read_log(self):
            filename = request.args["filename"]

            try:
                log = logs.get(filename, key=session.get("client_id"))
                return log.read()
            except KeyError:
                return "Could not find log file with given filename", 404

    return DashService
