# coding=utf-8

import rpyc


class Client():
    def __init__(self, server_params=None):
        if server_params:
            self.server_params = server_params
        else:
            self.server_params = [["localhost", "5050"]]

        self.conns = []
        for server in self.server_params:
            c = rpyc.connect(server[0], server[1])
            self.conns.append(c)

    def get_processes(self):
        processes = []
        for con in self.conns:
            process = con.root.get_processes()
            processes.append(process)

        return processes

    def get_process_limits(self):
        process_limits = []
        for con in self.conns:
            process_limit = con.root.get_process_limits()
            process_limits.append(process_limit)

        return process_limits

    def get_process(self, pid, section):
        sec_processes = []
        for con in self.conns:
            sec_process = con.root.get_processes(pid, section)
            sec_processes.append(sec_process)

        return sec_processes

    def get_disks(self):
        disks = []
        for con in self.conns:
            disk = con.root.get_disk()
            disks.append(disk)

        return disks

    def get_cpus(self):
        cpus = []
        for con in self.conns:
            cpu = con.root.get_cpu()
            cpus.append(cpu)

        return cpus

    def get_networks(self):
        nets = []
        for con in self.conns:
            net = con.root.get_network()
            nets.append(net)

        return nets

    def get_mems(self):
        mems = []
        for con in self.conns:
            mem = con.root.get_mem()
            mems.append(mem)

        return mems

    def get_overviews(self):
        overviews = []

        for con in self.conns:
            overview = con.root.get_overview()
            overviews.append(overview)

        return overviews

    def get_logs(self):
        logs = []

        for con in self.conns:
            log = con.root.get_logs()
            logs.append(log)

        return logs

    def get_log(self):
        single_logs = []

        for con in self.conns:
            log = con.root.get_log()
            single_logs.append(log)

        return single_logs

    def get_read_log(self):
        read_logs = []

        for con in self.conns:
            log = con.root.get_read_log()
            read_logs.append(log)

        return read_logs

    def get_read_log_tail(self):
        read_log_tails = []

        for con in self.conns:
            log = con.root.get_read_log_tail()
            read_log_tails.append(log)

        return read_log_tails

    def get_search_log(self):
        search_logs = []

        for con in self.conns:
            log = con.root.get_search_log()
            search_logs.append(log)

        return search_logs

    def stop(self):
        for con in self.conns:
            con.close()


if __name__ == "__main__":
    c = Client([["husky003", 5050]])
