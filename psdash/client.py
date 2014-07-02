# coding=utf-8

import rpyc
import pickle


class Client():
    def __init__(self, server_params=None):
        if server_params:
            self.server_params = server_params
        else:
            self.server_params = [["localhost", "5050"]]

        self.conns = {}
        for server in self.server_params:
            c = rpyc.connect(server[0], server[1])
            if server[0] not in self.conns.keys():
                self.conns[server[0]]= c

    def get_hostname_processes(self, hostname, sort, order):
        if hostname not in self.conns.keys():
            return "error"

        con = self.conns[hostname]
        processes = pickle.loads(con.root.get_processes(sort, order))

        return processes

    def get_hostname_process_limits(self, hostname, pid):
        if hostname not in self.conns.keys():
            return "error"

        con = self.conns[hostname]
        process_limits = pickle.loads(con.root.get_process_limits(pid))

        return process_limits

    def get_hostname_process(self, hostname, pid, section):
        if hostname not in self.conns.keys():
            return "error"

        con = self.conns[hostname]
        process = con.root.get_process(pid, section)

        return process

    def get_hostname_disk(self, hostname):
        if hostname not in self.conns.keys():
            return "error"

        con = self.conns[hostname]
        disk = pickle.loads(con.root.get_disk())

        return disk


    def get_hostname_network(self, hostname):
        if hostname not in self.conns.keys():
            return "error"

        con = self.conns[hostname]
        net = pickle.loads(con.root.get_network())

        return net


    def get_hostname_overview(self, hostname):
        if hostname not in self.conns.keys():
            return "error"

        con = self.conns[hostname]
        overview = pickle.loads(con.root.get_overview())

        return overview

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
        for key in self.conns.keys():
            self.conns[key].close()


if __name__ == "__main__":
    c = Client([["husky003", 5050]])
