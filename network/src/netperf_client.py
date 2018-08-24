#!/usr/bin/env python3
# _*_encoding:utf-8_*_


"""Test IPv4 / IPv6 performance of different RHELs in vSphere with netperf.

History:
v1.0.0 - 2018-06-29 - boyang - Draft the script
v1.0.1 - 2018-07-03 - boyang - Support fedora
v1.0.1 - 2018-07-11 - boyang - Checking points before netperf
v1.0.2 - 2018-07-20 - boyang - Setup the second VM as the netserver
"""


import re
import time
import os,sys
import logging
import platform
import subprocess
import configparser
import src.utils as utils
import src.read_cfg as read_cfg


# Deploy projects in all TARGET platforms
root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root)


# Receive parameter from PS1
type = sys.argv[1]
ipv4B = sys.argv[2]


# Before netperf starts, check the necessary requirements
tools = utils.Utlis()
ret = tools.scope_check()
if not ret:
    print("ERROR: Current Guest / Platform isn't support")
    exit(-1)

ret = tools.netperf_check()
if not ret:
    print("ERROR: Tool netperf isn't installed and failed to install by auto")
    exit(-1)

ret = tools.network_interface_check()
intr=""
if not ret[0]:
    print("ERROR: [ %s ] isn't the target interface" % ret[1])
    exit(-1)
else:
    intr = ret[1]

ipv4 = tools.network_ipv4(intr)
if not ipv4:
    exit(-1)

ipv6 = tools.network_ipv6(intr)
if not ipv6:
    exit(-1)


# Load test cases para
cases_lst = tools.cases_load()


def netperf_exe():
    """
    Execute netperf based on cases list
    :return: True
    """

    cmd = ""
    for i in cases_lst:
        m_size = i[1]
        cmd = "netperf -D 1 -H %s -l 67.5 -C -c -t %s -- -m %d >> %s_%d.nplog" % (ipv4B, i[0].split("-")[3], m_size, i[0].split("-")[3], m_size)
        print(cmd)
        ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

netperf_exe()

