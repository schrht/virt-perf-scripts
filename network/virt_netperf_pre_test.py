# _*_encoding:utf-8_*_


#!/usr/bin/env python


"""Run Netperf PRE Test in RHEL in virtual platforms
# Interface to GenerateTestReport.py
# This script should do:
# 1. Check tools required by NETPERF test
# 2. Install the missed tools after check


History:
v0.1    2018-12-03  boyang  Build the program
v0.2    2018-12-04  boyang  Optimize function load_config
"""

import sys
import yaml
import subprocess


def load_config(config):
    """
    Load test configuration file
    :param config: configuration file format by yaml
    :return: dict
    """

    config_dir = {}

    if not config:
        print("ERROR: Param [config] Missed")
        return False
    else:
        try:
            # Load netperf test configuration
            with open(config, "r") as f:
                config_dir = yaml.load(f)
        except Exception as err:
            print('ERROR: Fail to load YAML file. %s' % err)

    return config_dir["NetperfRunner"]


def check_tool_installation(vm_ip, tool_name):
    """
    Check a tool installation
    :param vm_ip: Target VM IP
    :param tool_name: Target tool will be installed name
    :return: True or False
    """

    if not tool_name or not vm_ip:
        print("ERROR: Parameter(s) Missed")
        return False
    else:
        configs = load_config("netperf_config.yaml")
        if len(configs) == 0:
            print("ERROR: Load netperf config file failed")
            return False

    # Check target tool name in target VM
    print("INFO: Tool of [%s] checking in [%s]" % (tool_name, vm_ip))
    tool_exist = subprocess.Popen(["ssh", "-i", configs["ssh_key"], "root@" + vm_ip, "whereis", tool_name],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    out_tool_exist = tool_exist.stdout.read().strip()
    # print("DEBUG: out_tool_exist: %s" % out_tool_exist)

    # Check the result of a tool installation
    if len(out_tool_exist) <= (len(tool_name) + 1):
        print("ERROR: Tool of [%s] NOT found. Try to install it" % tool_name)
        return install_tools(vm_ip, tool_name)
    else:
        return True


def install_tools(vm_ip, tool_name):
    """
    Install a tool
    :param vm_ip: Target VM IP
    :param tool_name: Target tool will be installed name
    :return: True or False
    """

    if not tool_name or not vm_ip:
        print("ERROR: Parameter(s) Missed")
        return False
    else:
        configs = load_config("netperf_config.yaml")
        if len(configs) == 0:
            print("ERROR: Load netperf config file failed")
            return False

    # SCP the installation script to target VM
    print("INFO: SCP installation script to %s" % tool_name)
    scp = subprocess.Popen(
        ["/bin/scp", "-i", configs["ssh_key"], configs["install_path"], "root@" + vm_ip + ":/root/install.sh"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    err_scp = scp.stderr.read().strip()

    # Check result of SCP
    if len(err_scp) != 0:
        print("ERROR: SCP installation script to %s failed" % vm_ip)
        return False

    # Install the target tool
    print("INFO: Install %s" % tool_name)
    install = subprocess.Popen(
        ["ssh", "-i", configs["ssh_key"], "root@" + vm_ip, "/bin/bash", "/root/install.sh", tool_name],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    err_install = install.stderr.read().strip()

    # Check result of installation
    if len(err_install) != 0:
        print("ERROR: Install %s failed" % tool_name)
        return False
    else:
        return True


if __name__ == '__main__':

    if len(sys.argv) != 3:
        print("ERROR: Missed command line args")
        exit(1)

    loc_ip = sys.argv[1]
    rmt_ip = sys.argv[2]

    for vm_ip in (loc_ip, rmt_ip):
        check_ret = check_tool_installation(vm_ip, "netperf")
        if not check_ret:
            exit(1)
        check_tool_installation(vm_ip, "netserver")
        if not check_ret:
            exit(1)
        check_tool_installation(vm_ip, "sysstat")
        if not check_ret:
            exit(1)
