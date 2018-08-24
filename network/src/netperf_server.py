# _*_encoding:utf-8_*_

############################################################################
#
# Functions:
#   Test IPv4 / IPv6 performance of different RHELs in vSphere with netperf
#
# Versions:
#   v1.0.0 - 06/29/2018 - boyang - Draft the script
#
############################################################################


import re
import time
import os,sys
import logging
import platform
import subprocess
import configparser
import src.utils as utils


# Deploy projects in all TARGET platforms
root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root)


# Receive parameter from PS1
type = sys.argv[1]


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
intr = ""
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


def netserver_exe():
    """
    Execute netperf based on cases list
    :return: True
    """
    if type.endwith("6"):
        cmd = "netserver -6"
    else:
        cmd = "netserver"
        ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

netserver_exe()

