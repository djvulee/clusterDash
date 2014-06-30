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
        pass

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

    def stop(self):
        for con in self.conns:
            con.close()


if __name__ == "__main__":
    c = Client([["husky003", 5050]])
