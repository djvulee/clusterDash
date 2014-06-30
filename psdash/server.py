# coding=utf-8

"""
This is the server who worker on a lot of machine, it will get a remote call from the client
"""


from rpyc.utils.server import TheadedServer
from dash_service import DashService


def main():
    s = TheadedServer(DashService)
    s.start()






