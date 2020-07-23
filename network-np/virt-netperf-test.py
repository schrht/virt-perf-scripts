#!/usr/bin/env python


"""Run Netperf Test in RHEL in virtual platforms.
Interface to GenerateTestReport.py. HERE, we change it, GenerateTestReport gets info from JSON files.
This script should do:
   1. The netperf outputs should be stored in a specific path(/tmp/) in *.nplog files.
   2. Save additional information(cpu%, interrputs etc.) into nplog.info. WIP
   3. The *.nplog and *.nplog.info files should be corresponding(Have the same file name.).
   4. Convert above logs into JSON files with result-convert.py.

History:
    v1.0.0  2018-10-11  boyang  Re-build netperf script which run in netperf client.
    v1.1.0  2018-12-03  boyang  Split STREAM mode and RR mode tests as different params.
    v2.0.0  2020-07-06  boyang  Get drivers names dynamically.
    v2.0.1  2020-07-06  boyang  Remove some parameters not used.
"""


import os
import sys
import time
import yaml
import click
import itertools
import subprocess


def load_config(config):
    """Load test configuration file.
    Args:
        config: configuration file format by yaml.
    Return: 
        dict
    """
    config_dir = {}

    if not config:
        print("ERROR: Param [config] Missed.")
        return False
    else:
        try:
            # Load netperf test configuration.
            with open(config, "r") as f:
                config_dir = yaml.load(f)
        except Exception as err:
            print('ERROR: Fail to load YAML file. As error: %s.' % err)

    return config_dir["NetperfRunner"]


class NetperfTestRunner:
    """Run the netperf test cases. As basic functions.
    1. It loads all the needed parameters from dict named 'params';
    2. It splits the test suites into sub-cases and run them one by one;
    3. It generates the netperf test report as log files ending with '.nplog';
    """

    def __init__(self, params={}):
        """Initialize this Class.
        Parse and check the parameters for running the netperf tests.
        Args:
            params: dict
                log_path: str
                    Where the *.nplog files will be saved to.
                     Example: "/root/tmp/netperf_log/"
                 exe_time: int
                     Execution time of a netperf case
                     Example: 60
                 instances: list
                     How many instances run a netperf case
                     Example: 1, 2, 4, 8
                 rounds: int
                     How many rounds the fio test will be repeated.
                     Example: 5
                 data_modes: list
                     Netperf test modes
                     Example: ["TCP_STREAM", "TCP_RR", "TCP_CRR", "UDP_STREAM", "UDP_RR"]
                 rr_size: list
                     RR size when execute TCP_RR, TCP_CRR, UDP_RR
                     Example: [ (64, 64), (128, 128), (256, 256)...]
                 m_size: list
                     M size when execute TCP_STREAM, UDP_STREAM.
                     Example: [32, 64, 128, 256, 512, 1024, 2048....]
         Returns:
             None
         """

        if 'log_path' not in params:
            print('[ERROR] Missing required params: params[log_path]')
            exit(1)
        elif type(params['log_path']) not in (type(u''), type(b'')):
            print('[ERROR] params[backend] must be string.')
            exit(1)
        else:
            self.log_path = params['log_path']

        if 'exe_time' not in params:
            print('[ERROR] Missing required params: params[exe_time]')
            exit(1)
        elif not isinstance(params['exe_time'], int) or params['exe_time'] < 1:
            print('[ERROR] params[exe_time] must be an integer >= 1.')
            exit(1)
        else:
            self.exe_time = params['exe_time']

        if 'instance' not in params:
            print('[ERROR] Missing required params: params[instance]')
            exit(1)
        elif not isinstance(params['instance'], (list, tuple)):
            print('[ERROR] params[instance] must be a list or tuple.')
            exit(1)
        else:
            self.instance = params['instance']

        if 'rounds' not in params:
            print('[ERROR] Missing required params: params[rounds]')
            exit(1)
        elif not isinstance(params['rounds'], int) or params['rounds'] < 1:
            print('[ERROR] params[rounds] must be an integer >= 1.')
            exit(1)
        else:
            self.rounds = params['rounds']

        if 'data_modes' not in params:
            print('[ERROR] Missing required params: params[data_modes]')
            exit(1)
        elif not isinstance(params['data_modes'], (list, tuple)):
            print('[ERROR] params[data_modes] must be a list or tuple.')
            exit(1)
        else:
            self.data_modes = params['data_modes']

        if 'rr_size' not in params:
            print('[ERROR] Missing required params: params[rr_size]')
            exit(1)
        elif not isinstance(params['rr_size'], (list, tuple)):
            print('[ERROR] params[rr_size] must be a list or tuple.')
            exit(1)
        else:
            self.rr_size = params['rr_size']

        if 'm_size' not in params:
            print('[ERROR] Missing required params: params[m_size]')
            exit(1)
        elif not isinstance(params['m_size'], (list, tuple)):
            print('[ERROR] params[m_size] must be a list or tuple.')
            exit(1)
        else:
            self.m_size = params['m_size']

    def _split_netperf_tests(self):
        """Split netperf test parameters.
        This function splits the parameters for running the netperf tests.
        It will do Cartesian product with the following itmes:
        - self.rounds
        - self.driver
        - self.data_mode
        - self.m_size / rr_size
        - self.instances
        Args:
            self
        Returns:
            DICT includes different iters
        """

        stream = []
        rr = []
        total_iter = {}
        # Different platforms, differnt NIC driver.
        driver = subprocess.Popen("ethtool -i `ls /sys/class/net/ | grep ^e[tn][hosp] | awk 'END{print}'` | awk NR==1 | awk '{print $2}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # driver is a str.
        driver = driver.stdout.read().decode("utf-8").strip("\n")
        # driver is a list.
        driver = driver.split("@@")

        # Subcases iter for stream /maerts modes.
        for m in self.data_modes:
            if m.find("STREAM") != -1:
                stream.append(m)
        stream_it = itertools.product(list(range(1, self.rounds + 1)), driver, stream, self.m_size, self.instance)

        # Subcases iter for rr modes
        for m in self.data_modes:
            if m.find("RR") != -1:
                rr.append(m)
        rr_it = itertools.product(list(range(1, self.rounds + 1)), driver, rr, self.rr_size, self.instance)

        total_iter.update({"STREAM": stream_it})
        total_iter.update({"RR": rr_it})

        return total_iter


    def run_local_netperf(self, rmt_ip):
        """Assume Remote Host netserver is running. Run netperf in local VM
        Args:
            self.rmt_ip: Host IP where run netserver.
        Return: 
            True or False.
        """
        diff_iters = self._split_netperf_tests()

        for it in diff_iters["STREAM"]:
            # netperf -t TCP_STREAM -f m -H $remote_server_ip -l 10 -- -m $a
            # netperf -t TCP_MAERTS -f m -H $remote_server_ip -l 10 -- -m $a
            # netperf -t UDP_STREAM -f m -H $remote_server_ip -l 10 -- -m $a
            (rd, driver, data_mode, m_size, instance) = it
            print(it)

            # Check output log DIR
            output_path = os.path.expanduser(self.log_path)
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            # Confirm Output log name
	    # Log file name: TCP_RR-vmxnet3-32_1024-inst1-rd2-20200507113014.nplog
            output_file = '%s-%s-%s-inst%s-rd%s-%s.nplog' % (
		data_mode, driver, m_size, instance, rd, time.strftime('%Y%m%d%H%M%S', time.localtime()) 
            )

            # Confirm full output log file path
            output = output_path + os.sep + output_file

            # Build the command
            command = 'netperf -P 0 -v 0 -D -0.20'
            command += ' -4'
            command += ' -t %s' % data_mode
            command += ' -f m'
            command += ' -H %s' % rmt_ip
            command += ' -l %d' % self.exe_time
            command += ' --'
            command += ' -m %s' % m_size
            command += ' -k THROUGHPUT,TRANSACTION_RATE,PROTOCOL,DIRECTION,SOCKET_TYPE,ELAPSED_TIME,THROUGHPUT_UNITS,LSS_SIZE,RSS_SIZE,LOCAL_SEND_SIZE,LOCAL_RECV_SIZE,REMOTE_SEND_SIZE,REMOTE_RECV_SIZE,REQUEST_SIZE,RESPONSE_SIZE,LOCAL_CPU_UTIL,LOCAL_CPU_PERCENT_USER,CONFIDENCE_INTERVAL,THROUGHPUT_CONFID,CONFIDENCE_ITERATION,LOCAL_TRANSPORT_RETRANS,REMOTE_TRANSPORT_RETRANS,TRANSPORT_MSS,REMOTE_SEND_CALLS,MEAN_LATENCY,COMMAND_LINE'
            command += ' > ' + output

            # Execute netperf test
            print('-' * 50)
            print('Current Time: %s' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
            print('Test Command: %s' % command)
            print('-' * 50)

            os.system(command)

        for it in diff_iters["RR"]:
            # netperf -t TCP_RR -H $remote_server_ip -- -r 256,256 -D
            # netperf -t TCP_CRR -H $remote_server_ip -- -r 256,256 -D
            # netperf -t UDP_RR -H $remote_server_ip -- -r 256,256 -D
            (rd, driver, data_mode, rr_size, instance) = it
            print(it)

            # Check output log DIR
            output_path = os.path.expanduser(self.log_path)
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            # Confirm Output log name
            tmp_rr_size = rr_size.replace(", ", "_")
            output_file = '%s-%s-%s-inst%s-rd%s-%s.nplog' % (
		data_mode, driver, tmp_rr_size, instance, rd, time.strftime('%Y%m%d%H%M%S', time.localtime()) 
            )

            # Confirm full output log file path
            output = output_path + os.sep + output_file

            # Build the command
            command = 'netperf'
            command += ' -t %s' % data_mode
            command += ' -H %s' % rmt_ip
            command += ' --'
            command += ' -r %s' % rr_size
            command += ' -D'
            command += ' -k THROUGHPUT,TRANSACTION_RATE,PROTOCOL,DIRECTION,SOCKET_TYPE,ELAPSED_TIME,THROUGHPUT_UNITS,LSS_SIZE,RSS_SIZE,LOCAL_SEND_SIZE,LOCAL_RECV_SIZE,REMOTE_SEND_SIZE,REMOTE_RECV_SIZE,REQUEST_SIZE,RESPONSE_SIZE,LOCAL_CPU_UTIL,LOCAL_CPU_PERCENT_USER,CONFIDENCE_INTERVAL,THROUGHPUT_CONFID,CONFIDENCE_ITERATION,LOCAL_TRANSPORT_RETRANS,REMOTE_TRANSPORT_RETRANS,TRANSPORT_MSS,REMOTE_SEND_CALLS,MEAN_LATENCY,COMMAND_LINE'
            command += ' > ' + output

            # Execute netperf test
            print('-' * 50)
            print('Current Time: %s' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
            print('Test Command: %s' % command)
            print('-' * 50)

            os.system(command)


def get_cli_params(log_path, exe_time, instance, rounds, data_modes, rr_size, m_size):
    """Get parameters from the CLI.
    Args:
        log_path: Store all logs.
        exe_time: Run time, default 60
        instance: Counts of netperf process
        rounds: Counts of run of a case
        data_modes: Test cases
        rr_size: Size for RR or CRR
        m_size: Size for STREAM
    Returns:
        dict
    """
    cli_params = {}

    if log_path:
        cli_params['log_path'] = log_path
    if exe_time:
        cli_params['exe_time'] = int(exe_time)
    if instance:
        cli_params['instance'] = int(instance)
    if rounds:
        cli_params['rounds'] = int(rounds)
    if data_modes:
        cli_params['data_modes'] = m_size.split(',')
    if rr_size:
        cli_params['rr_size'] = rr_size.split(',')
    if m_size:
        cli_params['m_size'] = m_size.split(',')

    return cli_params


def get_yaml_params():
    """Get parameters from the yaml file.
    Returns:
        dict
    """
    yaml_params = {}

    script_path = os.path.split(os.path.realpath( sys.argv[0]))[0]
    print("DEBUG: script_path: %s" % script_path)
    target_config = os.path.join(script_path, "netperf_config.yaml")
    print("DEBUG: target_config: %s" % target_config)

    try:
        with open(target_config) as f:
            yaml_dict = yaml.load(f)
            yaml_params = yaml_dict['NetperfRunner']

    except Exception as err:
        print('[WARNING] Fail to get default value from yaml file. %s' % err)
        exit(1)

    return yaml_params


def run_netperf_test(rmt_ip, params={}):
    """Initialize and run the netperf test.
    Args:
        rmt_ip: Host IP where netserver
        params: Includes instance, drivers, rounds, data_modes
    """
    print('=' * 50)
    print('Start Time: %s' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
    print('=' * 50)

    runner = NetperfTestRunner(params)
    runner.run_local_netperf(rmt_ip)

    print('=' * 50)
    print('Finish Time: %s' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
    print('=' * 50)


@click.command()
@click.argument('rmt_ip')
@click.option('--log_path', help='DIR stores logs.')
@click.option('--exe_time', type=click.IntRange(1, 60), help='How much time current netperf case run.')
#@click.option('--driver', help='NIC types include vmxnet3 / e1000 / e1000e. Current ONLY supports vmxnet3.')
@click.option('--instance', type=click.IntRange(1, 10), help='[NETPERF]How many instances be started.')
@click.option('--rounds', type=click.IntRange(1, 10), help='How many rounds to run')
@click.option('--data_modes', help='[NETPERF] Test modes includes STREAM and RR and CRR')
@click.option('--rr_size', help='[NETPERF] RR size when test RR mode')
@click.option('--m_size', help='[NETPERF] M size when test STREAM mode')
def cli(rmt_ip, log_path, exe_time, instance, rounds, data_modes, rr_size, m_size):
    """Command line interface.

    Take arguments from CLI, load default parameters from yaml file.
    Then initialize the netperf test.

    Args:
        log_path: Store all logs.
        exe_time: Run time, default 60
        instance: Counts of netperf process
        rounds: Counts of run of a case
        data_modes: Test cases
        rr_size: Size for RR or CRR
        m_size: Size for STREAM
    """
    # Read user specified parameters from CLI
    cli_params = get_cli_params(log_path, exe_time,instance, rounds, data_modes, rr_size, m_size)
    print("DEBUG: Params from CLI:")
    print(cli_params)

    # Read user configuration from yaml file.
    yaml_params = get_yaml_params()
    print("DEBUG: Params from YAML:")
    print(yaml_params)

    # Combine user input and config.
    params = {}
    params.update(yaml_params)
    params.update(cli_params)
    print("DEBUG: Last Params:")
    print(params)

    # Run NETPERF test.
    run_netperf_test(rmt_ip, params)

    exit(0)


if __name__ == '__main__':
    cli()
