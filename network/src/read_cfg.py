#!/usr/bin/env python
# _*_encoding:utf-8_*_


"""Read global configuration.

History:
v1.0.0 - 2018-06-29 - boyang - Draft the script
v1.0.1 - 2018-07-13 - boyang - RHEL8 support
v1.0.1 - 2018-07-14 - boyang - Optimize platform support list
"""


import re
import os, sys
import configparser


# Deploy in all TARGET platforms supported
root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root)
# Config configuration path
CFG_PATH = os.path.join(root, "config")
GLOBAL_CFG = os.path.join(CFG_PATH, "global.cfg")


def env(cfg_file):
    """
    Get VM's hypervisor env and VM's user name and password
    :param cfg_file:
    :return:
    """
    pass


def netperf_ver(cfg_file):
    """
    Get netperf version
    :param cfg_file:
    :return:
    """

    cfg = configparser.ConfigParser()
    cfg.read(cfg_file)

    return cfg.get("netperf", "version")


def netperf_url(cfg_file):
    """
    Get netperf url, if netpef is not installed
    :param cfg_file:
    :return:
    """

    cfg = configparser.ConfigParser()
    cfg.read(cfg_file)

    return cfg.get("netperf", "url")


def platforms_supported(cfg_file):
    """
    Get test scope supported
    :param cfg_file:
    :return: A list of platforms supported
    """

    cfg = configparser.ConfigParser()
    cfg.read(cfg_file)
    plt_items = cfg.items("platform")

    plt_lst = []
    for i in plt_items:
        if re.search("support", i[0]):
            plt_lst.append(i)
    # print(plt_lst)

    support_plt = []
    for i in plt_lst:
        support_plt.append(i[1])
    # print(support_plt)

    return support_plt


def cases_list_load(cfg_file):
    """
    Get all test cases
    :param cfg_file:
    :return: A list of cases need to be tested
    """
    cfg = configparser.ConfigParser()
    cfg.read(cfg_file)

    cases_items = cfg.items("cases_list")
    cases_lst = []
    for i in cases_items:
        if re.search("netperf", i[0]):
            cases_lst.append(i)

    return cases_lst