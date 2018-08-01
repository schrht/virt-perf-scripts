#!/usr/bin/env python
"""Run FIO Test.

# Interface between GenerateTestReport.py
# This script should do:
# 1. the fio outputs should be at least in json+ format
#    the "fio --group_reporting" must be used
# 2. save the fio outputs into *.fiolog
# 3. put all *.fiolog files into ./fio_result/
# 4. empty ./fio_report/ folder
# 5. pass the additional information by "fio --description"
#    a) "driver" - frontend driver, such as SCSI or IDE
#    b) "format" - the disk format, such as raw or xfs
#    c) "round" - the round number, such as 1, 2, 3...
#    d) "backend" - the hardware which data image based on

History:
v0.1    2018-07-31  charles.shih  Refactory based on StoragePerformanceTest.py
"""

import sys
import os
import time
import itertools
import yaml


class RunFioTest:
    def __init__(self, params={}):
        """Init RunFioTest Class.

        This function initializes the parameters for running the fio tests.

        Args:
            params: dict
                backend:    The backend device where vdisk based on. Such as
                            "HDD", "SSD", "NVME"...
                driver:     The vdisk driver used in hypervisor.
                            Example: "SCSI", "IDE"...
                fs:         The filesystem of the disk in VM, "RAW" for none.
                            Example: "RAW", "XFS", "EXT4"...
                rounds:     Rounds which the same test repeats for.
                target:     [FIO] The raw disk or file to be tested by fio.
                runtime:    [FIO] The interval for the test to be lasted.
                direct:     [FIO] Direct access to the disk.
                            Example: '0' (using cache), '1' (direct access).
                numbjobs:   [FIO] The number of jobs for an fio test.
                rw_list:    [FIO] The list of rw parameters for fio.
                            Example: 'write, read, randrw'...
                bs_list:    [FIO] The list of bs parameters for fio.
                            Example: '4k, 16k, 64k, 256k, 1m'...
                iodepth_list:
                            [FIO] The list of iodepth parameters for fio.
                            Example: '1, 8, 64'...
        Returns:
            None

        """

        # Parse the params
        if 'backend' not in params:
            print 'WARNING: Missing required params: params[backend]'
            self.backend = ''
        else:
            self.backend = params['backend']

        if 'driver' not in params:
            print 'WARNING: Missing required params: params[driver]'
            self.driver = ''
        else:
            self.driver = params['driver']

        if 'fs' not in params:
            print 'WARNING: Missing required params: params[fs]'
            self.fs = ''
        else:
            self.fs = params['fs']

        if 'rounds' not in params:
            print 'WARNING: Missing required params: params[rounds]'
            self.rounds = 1
        else:
            self.rounds = params['rounds']

        if 'target' not in params:
            print 'ERROR: Missing required params: params[target]'
            exit(1)
        else:
            self.target = params['target']

        if 'runtime' not in params:
            print 'ERROR: Missing required params: params[runtime]'
            exit(1)
        else:
            self.runtime = params['runtime']

        if 'direct' not in params:
            print 'ERROR: Missing required params: params[direct]'
            exit(1)
        else:
            self.direct = params['direct']

        if 'numbjobs' not in params:
            print 'ERROR: Missing required params: params[numbjobs]'
            exit(1)
        elif not isinstance(params['numbjobs'], int):
            print 'ERROR: params[numbjobs] must be an integer.'
            exit(1)
        else:
            self.numbjobs = params['numbjobs']

        if 'rw_list' not in params:
            print 'ERROR: Missing required params: params[rw_list]'
            exit(1)
        elif not isinstance(params['rw_list'], list) and not isinstance(
                params['rw_list'], tuple):
            print 'ERROR: params[rw_list] must be a list or tuple.'
            exit(1)
        else:
            self.rw_list = params['rw_list']

        if 'bs_list' not in params:
            print 'ERROR: Missing required params: params[bs_list]'
            exit(1)
        elif not isinstance(params['bs_list'], list) and not isinstance(
                params['bs_list'], tuple):
            print 'ERROR: params[bs_list] must be a list or tuple.'
            exit(1)
        else:
            self.bs_list = params['bs_list']

        if 'iodepth_list' not in params:
            print 'ERROR: Missing required params: params[iodepth_list]'
            exit(1)
        elif not isinstance(params['iodepth_list'], list) and not isinstance(
                params['iodepth_list'], tuple):
            print 'ERROR: params[iodepth_list] must be a list or tuple.'
            exit(1)
        else:
            self.iodepth_list = params['iodepth_list']

        return None

    def _split_fio_tests(self):
        # Cartesian product the fio parameters
        # (round, rw, bs, iodepth)
        fio_params = itertools.product(
            range(1, self.rounds + 1), self.rw_list, self.bs_list,
            self.iodepth_list)

        num = 0
        for i in fio_params:
            num += 1
            print i
        print num

    def do_fio_run(self):

        file_number = 0
        for m_test_round_item in range(1, self.m_test_round + 1):
            for m_rw_item in self.m_rw:
                for m_bs_item in self.m_bs:
                    for m_iodepth_item in self.m_iodepth:
                        for m_disk_filename_dic_key in self.m_disk_filename_dic:

                            m_filename_item = self.m_disk_filename_dic[
                                m_disk_filename_dic_key]

                            seq = (self.m_gen_type, m_disk_filename_dic_key,
                                   m_rw_item, m_bs_item, m_iodepth_item,
                                   m_filename_item, str(m_test_round_item))
                            # This is sequence of strings.
                            output_name = "_".join(seq)
                            output_name = output_name
                            output_name = output_name.replace(os.sep, '')
                            output_name_fio = output_name + ".fiolog"
                            output_name_fio = self.m_dir_result + os.sep + output_name_fio
                            if not os.path.exists(self.m_dir_result):
                                os.mkdir(self.m_dir_result)

                            # Set additional information
                            try:
                                info = {}
                                info['backend'] = 'nvme-ssd'
                                info['round'] = str(m_test_round_item)
                                info['driver'] = m_disk_filename_dic_key.split(
                                    '_')[0]
                                if m_disk_filename_dic_key.split('_')[
                                        1] == 'fs':
                                    info['format'] = self.m_fs_type
                                else:
                                    info['format'] = 'raw'

                            except Exception, err:
                                print 'Error while setting additional information: %s' % err

                            if 'backend' not in info:
                                info['backend'] = 'n/a'
                            if 'round' not in info:
                                info['round'] = 'n/a'
                            if 'driver' not in info:
                                info['driver'] = 'n/a'
                            if 'format' not in info:
                                info['format'] = 'n/a'

                            description = str(info)

                            # Execute command
                            command = 'fio --filename=%s --name=%s --ioengine=libaio --iodepth=%s --rw=%s \
                            --bs=%s --direct=%s --size=512M --numjobs=%s --group_reporting --time_based --runtime=%s \
                            --output-format=normal,json+ --output=%s --description="%s"' % (
                                m_filename_item, output_name, m_iodepth_item,
                                m_rw_item, m_bs_item, self.m_direct,
                                self.m_numbjobs, self.m_runtime,
                                output_name_fio, description)
                            os.system(command)
                            time.sleep(1)
                            print command
                            print "current test number is:", file_number
                            print "======================================================\n"
                            file_number = file_number + 1


if __name__ == '__main__':

    starttime = time.time()
    #time.sleep(5)

    print "Start to run fio performance test ! \n"

    params = {}

    # Read user configuration from yaml file
    try:
        if os.path.exists('./RunFioTest.yaml'):
            config_file = './RunFioTest.yaml'
        else:
            config_file = os.path.expanduser('~/.RunFioTest.yaml')

        with open(config_file, 'r') as f:
            yaml_dict = yaml.load(f)

        if 'RunFioTest' in yaml_dict:
            params = yaml_dict['RunFioTest']

    except Exception as err:
        print 'ERROR: error while parsing "%s".' % (config_file)
        print err
        exit(1)

    print params

    rft = RunFioTest(params)
    rft._split_fio_tests()

    exit(0)
