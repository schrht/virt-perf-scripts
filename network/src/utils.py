#!/usr/bin/env python
# _*_encoding:utf-8_*_


"""Provides all utils for projects.

History:
v1.0.0 - 2018-06-29 - boyang - Draft the script
v1.0.1 - 2018-07-03 - boyang - Support test scope check
v1.0.1 - 2018-07-11 - boyang - Support network interface check
v1.0.2 - 2018-07-20 - boyang - Support netperf installation by auto
"""


import re
import os,sys
import platform
import subprocess
import configparser

import src.read_cfg as read_cfg

# Deploy source path
root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root)


class Utlis:
    """All tools for the performance test
        1. Check test scope;
        2. Check netperf installation;
        3. Check network interface and IPs;
    Attributes:
        None
    """

    def scope_check(self):
        """
        Check current target VM is supported to test
        :return: true or false
        """
        plt = re.search("(redhat|fedora)-\d\.?\d", platform.platform()).group()

        for i in read_cfg.platforms_supported(read_cfg.GLOBAL_CFG):
            if i in plt:
                print("%s is supported" % i)
                return True

    def netperf_check(self):
        """
        Check netperf installation, if not, install it
        :return: true or false
        """
        ret = subprocess.run("rpm -qa | grep netperf", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        netperf = ret.stdout.decode("utf-8").strip()
        if len(netperf) == 0:
            print("WARNING: Tool netperf isn't installed, will install it automatically")
            url = read_cfg.netperf_url(read_cfg.GLOBAL_CFG)
            ret = subprocess.run("yum -y install %s > /dev/null && echo $?" % url, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                installed = int(ret.stdout.decode("utf-8").strip())
                if installed != 0:
                    print("ERROR: Install netprf failed")
                    return False
            except ValueError:
                print("ERROR: Return a non-number")
                return False
        else:
            print("INFO: Tool netperf [ %s ] has been installed" % netperf)
            return True

    def network_interface_check(self):
        """
        Check current target VM network interface
        :return: A list like [true or false, intr]
        """

        ret = subprocess.run("ls /sys/class/net/ | egrep 'e[tn][hspo]'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        intr = ret.stdout.decode("utf-8").strip()
        if not intr:
            print("ERROR: [ %s ] is not target network interface" % intr)
            return [False, intr]
        else:
            print("INFO: [ %s ] is the target interface" % intr)
            return [True, intr]

    def network_ipv4(self, intr):
        """
        Check current target VM network ipv4
        :return: VM's ip
        """

        ret = subprocess.run("ifconfig %s | grep 'inet ' | awk '{print $2}'" % intr, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        v4 = ret.stdout.decode("utf-8").strip()
        if not v4:
            print("ERROR: [ %s ] is not target IP format" % v4)
            return False
        else:
            print("INFO: [ %s ] is the target IPv4 format" % v4)
            return v4

    def network_ipv6(self, intr):
        """
        Check current target VM network ipv6
        :return: VM's ip
        """

        ret = subprocess.run("ifconfig %s | grep 'inet6 ' | awk '{print $2}'" % intr, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        v6 = ret.stdout.decode("utf-8").strip()
        if not v6:
            print("ERROR: [ %s ] is not target IP format" % v6)
            return False
        else:
            print("INFO: [ %s ] is the target IPv6 format" % v6)
            return v6

    def cases_load(self):
        """
        Load test cases
        :return: A list of cases
        """

        return read_cfg.cases_list_load(read_cfg.GLOBAL_CFG)