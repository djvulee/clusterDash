# coding=utf-8


"""
This is the basic defined services
"""


from rpyc import Service


from net import NetIOCounters, get_interface_addresses

import psutil
import datetime
import socket
import os
import platform


class DashService(Service):
    def exposed_get_disk(self, all_partitions=False):
        disk = [ (dp, psutil.disk_usage(dp.mountpoint)) for dp in psutil.disk_partitions(all_partitions)]
        disk.sort(key=lambda d: d[1].total, reverse=True)

        return disk

    def exposed_get_cpu(self):
        pass

    def exposed_get_network(self):
        pass

    def exposed_get_mem(self):
        pass

    def exposed_get_user(self):
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

    def exposed_get_network_interface(self):
        net_io_counters = NetIOCounters()
        io_counters = net_io_counters.get()
        addresses = get_interface_addresses()

        for inf in addresses:
            inf.update(io_counters.get(inf["name"], {}))

        return addresses

    def exposed_get_overview(self):
        load_avg = os.getloadavg()
        uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        disks = self.exposed_get_disk()
        users = self.exposed_get_user()

        #netifs = self.get_network_interfaces()
        #netifs.sort(key=lambda x: x.get("bytes_sent"), reverse=True)

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
                #"net_interfaces": netifs,
                "page": "overview",
        }

        return data
