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
v0.2    2018-08-03  charles.shih  Implement Class RunFioTest.
v0.3    2018-08-07  charles.shih  Finish the logic of log handling.
"""

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
                numjobs:    [FIO] The number of jobs for an fio test.
                rw_list:    [FIO] The list of rw parameters for fio.
                            Example: 'write, read, randrw'...
                bs_list:    [FIO] The list of bs parameters for fio.
                            Example: '4k, 16k, 64k, 256k, 1m'...
                iodepth_list:
                            [FIO] The list of iodepth parameters for fio.
                            Example: '1, 8, 64'...
                log_path:   Where the fio output log will be generated to.
        Returns:
            None

        """

        # Parse and check the params
        if 'backend' not in params:
            print 'ERROR: Missing required params: params[backend]'
            exit(1)
        elif not isinstance(params['backend'], str):
            print 'ERROR: params[backend] must be string.'
            exit(1)
        else:
            self.backend = params['backend']

        if 'driver' not in params:
            print 'ERROR: Missing required params: params[driver]'
            exit(1)
        elif not isinstance(params['driver'], str):
            print 'ERROR: params[driver] must be string.'
            exit(1)
        else:
            self.driver = params['driver']

        if 'fs' not in params:
            print 'ERROR: Missing required params: params[fs]'
            exit(1)
        elif not isinstance(params['fs'], str):
            print 'ERROR: params[fs] must be string.'
            exit(1)
        else:
            self.fs = params['fs']

        if 'rounds' not in params:
            print 'ERROR: Missing required params: params[rounds]'
            exit(1)
        elif not isinstance(params['rounds'], int) or params['rounds'] < 1:
            print 'ERROR: params[rounds] must be an integer >= 1.'
            exit(1)
        else:
            self.rounds = params['rounds']

        if 'target' not in params:
            print 'ERROR: Missing required params: params[target]'
            exit(1)
        elif not isinstance(params['target'], str):
            print 'ERROR: params[target] must be string.'
            exit(1)
        else:
            self.target = params['target']

        if 'runtime' not in params:
            print 'ERROR: Missing required params: params[runtime]'
            exit(1)
        elif not isinstance(params['runtime'], str):
            print 'ERROR: params[runtime] must be string.'
            exit(1)
        else:
            self.runtime = params['runtime']

        if 'direct' not in params:
            print 'ERROR: Missing required params: params[direct]'
            exit(1)
        elif not params['direct'] in (0, 1):
            print 'ERROR: params[direct] must be integer 0 or 1.'
            exit(1)
        else:
            self.direct = params['direct']

        if 'numjobs' not in params:
            print 'ERROR: Missing required params: params[numjobs]'
            exit(1)
        elif not isinstance(params['numjobs'], int):
            print 'ERROR: params[numjobs] must be an integer.'
            exit(1)
        else:
            self.numjobs = params['numjobs']

        if 'rw_list' not in params:
            print 'ERROR: Missing required params: params[rw_list]'
            exit(1)
        elif not isinstance(params['rw_list'], (list, tuple)):
            print 'ERROR: params[rw_list] must be a list or tuple.'
            exit(1)
        else:
            self.rw_list = params['rw_list']

        if 'bs_list' not in params:
            print 'ERROR: Missing required params: params[bs_list]'
            exit(1)
        elif not isinstance(params['bs_list'], (list, tuple)):
            print 'ERROR: params[bs_list] must be a list or tuple.'
            exit(1)
        else:
            self.bs_list = params['bs_list']

        if 'iodepth_list' not in params:
            print 'ERROR: Missing required params: params[iodepth_list]'
            exit(1)
        elif not isinstance(params['iodepth_list'], (list, tuple)):
            print 'ERROR: params[iodepth_list] must be a list or tuple.'
            exit(1)
        else:
            self.iodepth_list = params['iodepth_list']

        if 'log_path' not in params:
            print 'ERROR: Missing required params: params[log_path]'
            exit(1)
        elif not isinstance(params['log_path'], str):
            print 'ERROR: params[log_path] must be string.'
            exit(1)
        else:
            self.log_path = params['log_path']

        return None

    def _split_fio_tests(self):
        """Split fio test parameters.

        This function splits the parameters for running the fio tests.

        It will do Cartesian product with self.rounds, self.rw_list,
        self.bs_list and self.iodepth_list.

        Args:
            None

        Returns:
            The iterator of fio test parameters in (round, rw, bs, iodepth).

        """

        # Cartesian product with fio parameters
        return itertools.product(
            range(1, self.rounds + 1), self.rw_list, self.bs_list,
            self.iodepth_list)

    def run_tests(self):
        fio_params = self._split_fio_tests()
        for fio_param in fio_params:
            (rd, rw, bs, iodepth) = fio_param

            # Set log file
            output_path = os.path.expanduser(self.log_path)
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            output_file = 'fio_%s_%s_%s_%s_%s_%s_%s_%s_%s.fiolog' % (
                self.backend, self.driver, self.fs, rw, bs, iodepth,
                self.numjobs, rd,
                time.strftime('%Y%m%d%H%M%S', time.localtime()))

            output = output_path + os.sep + output_file

            # Build fio command
            command = 'fio'
            command += ' --filename=%s' % self.target
            command += ' --ioengine=libaio'
            command += ' --iodepth=%s' % iodepth
            command += ' --rw=%s' % rw
            command += ' --bs=%s' % bs
            command += ' --direct=%s' % self.direct
            command += ' --size=512M'
            command += ' --numjobs=%s' % self.numjobs
            command += ' --group_reporting'
            command += ' --time_based'
            command += ' --runtime=%s' % self.runtime
            command += ' --output-format=normal,json+'
            command += ' --output=%s' % output
            command += ' --description="%s"' % {
                'backend': self.backend,
                'driver': self.driver,
                'format': self.fs,
                'round': rd
            }

            # Execute fio test
            print command
            #os.system(command)


if __name__ == '__main__':

    starttime = time.strftime('%Y%m%d%H%M%S', time.localtime())
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
    rft.run_tests()

    exit(0)
