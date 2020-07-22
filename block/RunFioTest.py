#!/usr/bin/env python3
"""Run FIO Test.

# Interface between GenerateTestReport.py
# This script should do:
# 1. the fio outputs should be at least in json+ format
#    the "fio --group_reporting" must be used
# 2. save the fio outputs into *.fiolog
# 3. put all *.fiolog files into the spcified path
# 4. pass the additional information by "fio --description"
#    a) "driver" - frontend driver, such as SCSI or IDE
#    b) "format" - the disk format, such as raw or xfs
#    c) "round" - the round number, such as 1, 2, 3...
#    d) "backend" - the hardware which data image based on

History:
v0.1    2018-07-31  charles.shih  Refactory based on StoragePerformanceTest.py
v0.2    2018-08-03  charles.shih  Implement Class RunFioTest.
v0.3    2018-08-07  charles.shih  Finish the logic of log handling.
v0.4    2018-08-07  charles.shih  Add logic to handling CLI.
v1.0    2018-08-08  charles.shih  Init version.
v1.0.1  2018-08-09  charles.shih  Enhance the output messages.
v1.1    2018-08-20  charles.shih  Support Python 3.
v1.2    2018-08-23  charles.shih  Fix string adjustment issue in Python 2.
v1.2.1  2019-05-13  charles.shih  Support testing against multiple targets.
v1.2.2  2019-06-06  charles.shih  Fix a parameter parsing issue with the new
                                  version of click module.
v1.2.3  2019-07-03  charles.shih  Fix the last issue with a better solution.
v1.3    2019-07-09  charles.shih  Drop the caches before each fio test.
v1.3.1  2019-09-11  charles.shih  Change disk size for the testing.
v1.4    2019-12-16  charles.shih  Support specifying an ioengine for the tests.
v1.4.1  2019-12-16  charles.shih  Bugfix for the ioengine support.
v1.5    2019-12-17  charles.shih  Technical Preview, collect CPU idleness.
v1.5.1  2019-12-17  charles.shih  Bugfix for the direct parameter.
v1.6    2019-12-19  charles.shih  Add the dry-run support.
v1.7    2019-12-20  charles.shih  Refactory the job controller part.
v1.8    2019-12-26  charles.shih  Support generating logs for the plots.
v1.8.1  2019-12-30  charles.shih  Bugfix for the dryrun and plots parameters.
v2.0    2019-12-30  charles.shih  Support Generating bw/iops/lat plots.
v2.1    2020-01-02  charles.shih  Technical Preview, collect SAR logs.
v2.1.1  2020-01-02  charles.shih  Add switch for technical preview features.
v2.2    2020-01-03  charles.shih  Use customized plots generator.
v2.2.1  2020-03-13  charles.shih  PEP-8 Formatting.
v2.3    2020-07-22  charles.shih  Name all files uniformly.
v2.4    2020-07-22  charles.shih  Technical Preview, wait before collection.
v2.5    2020-07-22  charles.shih  Log the fio command.
"""

import os
import time
import itertools
import yaml
import click


class FioTestRunner:
    """FIO Test Runner.

    This class used to run the fio test cases. As basic functions:
    1. It loads all the needed parameters from dict named 'params';
    2. It splits the test suites into sub-cases and run them one by one;
    3. It generates the fio test report as log files ending with '.fiolog';

    """

    # Initialize the test runner
    def __init__(self, params={}):
        """Initialize this Class.

        This function parse and check the parameters for running the fio tests.

        Args:
            params: dict
                backend: str
                    The backend device where vdisk image is based on.
                    Example: "HDD", "SSD", "NVME"...
                driver: str
                    The driver to power the vdisk..
                    Example: "SCSI", "IDE"...
                fs: str
                    The filesystem of the disk to be tested, "RAW" for no fs.
                    Example: "RAW", "XFS", "EXT4"...
                rounds: int
                    How many rounds the fio test will be repeated.
                filename: str
                    [FIO] The disk or specified file(s) to be tested by fio.
                runtime: str
                    [FIO] Terminate a job after the specified period of time.
                ioengine: str
                    [FIO] Defines how the job issues I/O to the file.
                direct: int
                    [FIO] Direct access to the disk.
                    Example: '0' (using cache), '1' (direct access).
                numjobs: int
                    [FIO] Create the specified number of clones of the job.
                rw_list: list
                    [FIO] Type of I/O pattern.
                    Example: 'write, read, randrw'...
                bs_list: list
                    [FIO] The block size in bytes used for I/O units.
                    Example: '4k, 16k, 64k, 256k, 1m'...
                iodepth_list: list
                    [FIO] # of I/O units to keep in flight against the file.
                    Example: '1, 8, 64'...
                log_path: str
                    Where the *.fiolog files will be saved to.
                plots: bool
                    Generate bw/iops/lat logs and plots in their lifetime.
                dryrun: bool
                    Print the commands that would be executed, but do not
                    execute them.
        Returns:
            None

        """
        # Parse Args
        if 'backend' not in params:
            print('[ERROR] Missing required params: params[backend]')
            exit(1)
        elif type(params['backend']) not in (type(u''), type(b'')):
            print('[ERROR] params[backend] must be string.')
            exit(1)
        else:
            self.backend = params['backend']

        if 'driver' not in params:
            print('[ERROR] Missing required params: params[driver]')
            exit(1)
        elif type(params['driver']) not in (type(u''), type(b'')):
            print('[ERROR] params[driver] must be string.')
            exit(1)
        else:
            self.driver = params['driver']

        if 'fs' not in params:
            print('[ERROR] Missing required params: params[fs]')
            exit(1)
        elif type(params['fs']) not in (type(u''), type(b'')):
            print('[ERROR] params[fs] must be string.')
            exit(1)
        else:
            self.fs = params['fs']

        if 'rounds' not in params:
            print('[ERROR] Missing required params: params[rounds]')
            exit(1)
        elif not isinstance(params['rounds'], int) or params['rounds'] < 1:
            print('[ERROR] params[rounds] must be an integer >= 1.')
            exit(1)
        else:
            self.rounds = params['rounds']

        if 'filename' not in params:
            print('[ERROR] Missing required params: params[filename]')
            exit(1)
        elif type(params['filename']) not in (type(u''), type(b'')):
            print('[ERROR] params[filename] must be string.')
            exit(1)
        else:
            self.filename = params['filename']

        if 'runtime' not in params:
            print('[ERROR] Missing required params: params[runtime]')
            exit(1)
        elif type(params['runtime']) not in (type(u''), type(b'')):
            print('[ERROR] params[runtime] must be string.')
            exit(1)
        else:
            self.runtime = params['runtime']

        if 'ioengine' not in params:
            print('[ERROR] Missing required params: params[ioengine]')
            exit(1)
        elif type(params['ioengine']) not in (type(u''), type(b'')):
            print('[ERROR] params[ioengine] must be string.')
            exit(1)
        else:
            self.ioengine = params['ioengine']

        if 'direct' not in params:
            print('[ERROR] Missing required params: params[direct]')
            exit(1)
        elif not params['direct'] in (0, 1):
            print('[ERROR] params[direct] must be integer 0 or 1.')
            exit(1)
        else:
            self.direct = params['direct']

        if 'numjobs' not in params:
            print('[ERROR] Missing required params: params[numjobs]')
            exit(1)
        elif not isinstance(params['numjobs'], int):
            print('[ERROR] params[numjobs] must be an integer.')
            exit(1)
        else:
            self.numjobs = params['numjobs']

        if 'rw_list' not in params:
            print('[ERROR] Missing required params: params[rw_list]')
            exit(1)
        elif not isinstance(params['rw_list'], (list, tuple)):
            print('[ERROR] params[rw_list] must be a list or tuple.')
            exit(1)
        else:
            self.rw_list = params['rw_list']

        if 'bs_list' not in params:
            print('[ERROR] Missing required params: params[bs_list]')
            exit(1)
        elif not isinstance(params['bs_list'], (list, tuple)):
            print('[ERROR] params[bs_list] must be a list or tuple.')
            exit(1)
        else:
            self.bs_list = params['bs_list']

        if 'iodepth_list' not in params:
            print('[ERROR] Missing required params: params[iodepth_list]')
            exit(1)
        elif not isinstance(params['iodepth_list'], (list, tuple)):
            print('[ERROR] params[iodepth_list] must be a list or tuple.')
            exit(1)
        else:
            self.iodepth_list = params['iodepth_list']

        if 'log_path' not in params:
            print('[ERROR] Missing required params: params[log_path]')
            exit(1)
        elif type(params['log_path']) not in (type(u''), type(b'')):
            print('[ERROR] params[log_path] must be string.')
            exit(1)
        else:
            self.log_path = params['log_path']

        if 'plots' not in params:
            self.plots = False
        elif not isinstance(params['plots'], bool):
            print('[ERROR] params[plots] must be bool.')
            exit(1)
        else:
            self.plots = params['plots']

        if 'dryrun' not in params:
            self.dryrun = False
        elif not isinstance(params['dryrun'], bool):
            print('[ERROR] params[dryrun] must be bool.')
            exit(1)
        else:
            self.dryrun = params['dryrun']

        # Init variables
        self.jobs = []
        self.path = ''

        return None

    def _split_tests(self):
        """Split fio test parameters and create job list.

        This function splits the parameters for running the fio tests.

        It will do Cartesian product with the following itmes:
        - self.rounds
        - self.bs_list
        - self.iodepth_list
        - self.rw_list
        (Most often changing)

        Args:
            None

        Returns:
            None

        Updates:
            self.jobs: the job list.

        """
        # Overall parameters
        self.path = os.path.expanduser(self.log_path)

        # Technical Preview
        support_idleness = True
        support_sar = True

        # Split parameters
        param_tuples = itertools.product(list(range(1, self.rounds + 1)),
                                         self.bs_list, self.iodepth_list,
                                         self.rw_list)

        # Generate command for all the tests
        jobnum = 0
        for param_tuple in param_tuples:
            (rd, bs, iodepth, rw) = param_tuple

            command = pre_command = post_command = ''

            # Set case and log file name
            casename = 'fio_%s_%s_%s_%s_%s_%s_%s_%s_%s_%s' % (
                self.backend, self.driver, self.fs, self.ioengine, rw, bs,
                iodepth, self.numjobs, rd,
                time.strftime('%Y%m%d%H%M%S', time.localtime()))
            output_path = self.path + os.sep + casename
            output = output_path + os.sep + casename + '.fiolog'

            # Build fio command
            command = 'fio'
            command += ' --name=%s' % casename
            command += ' --filename=%s' % self.filename
            command += ' --size=80G'
            command += ' --ioengine=%s' % self.ioengine
            command += ' --direct=%s' % self.direct
            command += ' --rw=%s' % rw
            command += ' --bs=%s' % bs
            command += ' --iodepth=%s' % iodepth
            command += ' --numjobs=%s' % self.numjobs
            command += ' --time_based'
            command += ' --runtime=%s' % self.runtime
            command += ' --group_reporting'
            command += ' --output-format=normal,json+'
            command += ' --output=%s' % output

            # Reuse 'description' to integrate some metadata
            command += ' --description="%s"' % {
                'backend': self.backend,
                'driver': self.driver,
                'format': self.fs,
                'round': rd
            }

            # Technical Preview: Collect CPU idleness
            if support_idleness and not support_sar:
                command += ' --idle-prof=percpu'

            # Technical Preview: Wait before collection
            command += ' --ramp_time=20'

            # Generate bw/iops/lat logs in their lifetime for the plots
            if self.plots:
                prefix = output_path + os.sep + casename
                command += ' --write_bw_log=%s' % prefix
                command += ' --write_iops_log=%s' % prefix
                command += ' --write_lat_log=%s' % prefix
                command += ' --log_avg_msec=500'
                command += ' --per_job_logs=1'

            # Parse options only, don't start any I/O
            # command += ' --parse-only'  # (comment this line for testing)

            # Set pre-command
            pre_command += 'mkdir -p %s; cd %s; ' % (output_path, output_path)
            # Drop caches
            pre_command += 'sync; echo 3 > /proc/sys/vm/drop_caches; '

            # Technical Preview: SAR
            if support_sar:
                pre_command += 'sar -A 1 -o %s.sa &>/dev/null & ' % casename

            # Set post-command
            if self.plots:
                post_command += 'export PATH=$PATH:$PWD/utils/; '
                post_command += 'pushd %s &>/dev/null; ' % output_path
                post_command += 'generate_plots.sh %s &>/dev/null; ' % casename
                post_command += 'popd &>/dev/null; '

            # Technical Preview: SAR
            if support_sar:
                post_command += 'pushd %s &>/dev/null; ' % output_path
                post_command += 'killall sar; '
                post_command += 'sar -f %s.sa -u > %s-sa_cpu.log; ' % (
                    casename, casename)
                post_command += 'popd &>/dev/null; '

            # Log the fio command
            post_command += 'pushd %s &>/dev/null; ' % output_path
            post_command += 'echo %s > %s.cmd; ' % (command, casename)
            post_command += 'popd &>/dev/null; '

            # Collect log files and create tarball
            post_command += 'pushd %s &>/dev/null' % output_path
            post_command += ' && tar zcf %s.tar.gz *; ' % casename
            post_command += 'popd &>/dev/null; '
            post_command += 'mv -t %s %s/%s.tar.gz' % (self.path, output_path,
                                                       casename)
            post_command += ' && rm -r %s; ' % output_path

            # save the current test command into jobs
            jobnum += 1
            self.jobs.append({
                'jobnum': jobnum,
                'command': command,
                'pre_command': pre_command,
                'post_command': post_command,
                'status': 'NOTRUN',
                'start': None,
                'stop': None
            })

        return None

    def start(self):
        """Start to run all tests in the job list."""
        if not self.jobs:
            self._split_tests()

        jobnum = 0
        total_num = len(self.jobs)
        for job in self.jobs:
            # Show job information
            jobnum += 1
            start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            print('-' * 50)
            print('Current Job  : %s / %s' % (jobnum, total_num))
            print('Current Time : %s' % start_time)
            print('Pre Command  : %s' % job['pre_command'])
            print('Test Command : %s' % job['command'])
            print('Post Command : %s' % job['post_command'])
            print('-' * 50)

            if self.dryrun is False:
                # Create log directory
                if not os.path.exists(self.path):
                    os.makedirs(self.path)

                # Execute current test
                os.system(job['pre_command'])
                os.system(job['command'])
                os.system(job['post_command'])
            else:
                time.sleep(0.2)

            # Update jobs data
            job['status'] = 'FINISH'
            job['start'] = start_time
            job['stop'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        return None


def get_cli_params(backend, driver, fs, rounds, filename, runtime, ioengine,
                   direct, numjobs, rw_list, bs_list, iodepth_list, log_path,
                   plots, dryrun):
    """Get parameters from the CLI."""
    cli_params = {}

    if backend is not None:
        cli_params['backend'] = backend
    if driver is not None:
        cli_params['driver'] = driver
    if fs is not None:
        cli_params['fs'] = fs
    if rounds is not None:
        cli_params['rounds'] = int(rounds)
    if filename is not None:
        cli_params['filename'] = filename
    if runtime is not None:
        cli_params['runtime'] = runtime
    if ioengine is not None:
        cli_params['ioengine'] = ioengine
    if direct is not None:
        cli_params['direct'] = direct
    if numjobs is not None:
        cli_params['numjobs'] = numjobs
    if rw_list is not None:
        cli_params['rw_list'] = rw_list.split(',')
    if bs_list is not None:
        cli_params['bs_list'] = bs_list.split(',')
    if iodepth_list is not None:
        cli_params['iodepth_list'] = iodepth_list.split(',')
    if log_path is not None:
        cli_params['log_path'] = log_path
    if plots is not None:
        cli_params['plots'] = plots
    if dryrun is not None:
        cli_params['dryrun'] = dryrun

    return cli_params


def get_yaml_params():
    """Get parameters from the yaml file."""
    yaml_params = {}

    try:
        with open('./virt_perf_scripts.yaml', 'r') as f:
            yaml_dict = yaml.load(f)
            yaml_params = yaml_dict['FioTestRunner']

    except Exception as err:
        print('[WARNING] Fail to get default value from yaml file. %s' % err)

    return yaml_params


def run_fio_test(params={}):
    """Initialize and run the fio test."""
    print('=' * 50)
    print('Start Time: %s' %
          time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
    print('=' * 50)

    fiorunner = FioTestRunner(params)
    fiorunner.start()

    print('=' * 50)
    print('Finish Time: %s' %
          time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
    print('=' * 50)


@click.command()
@click.option('--backend',
              help='The backend device where vdisk image is based on.')
@click.option('--driver', help='The driver to power the vdisk..')
@click.option('--fs',
              help='The filesystem of the disk to be tested, "RAW" for no fs.')
@click.option('--rounds',
              type=click.IntRange(1, 1000),
              help='How many rounds the fio test will be repeated.')
@click.option(
    '--filename',
    help='[FIO] The disk(s) or specified file(s) to be tested by fio. You can \
specify a number of targets by separating the names with a \':\' colon.')
@click.option('--runtime',
              help='[FIO] Terminate a job after the specified period of time.')
@click.option('--ioengine',
              help='[FIO] Defines how the job issues I/O to the file. \
Such as: \'libaio\', \'io_uring\', etc.')
@click.option('--direct',
              type=click.IntRange(0, 1),
              help='[FIO] Direct access to the disk.')
@click.option('--numjobs',
              type=click.IntRange(1, 65535),
              help='[FIO] Create the specified number of clones of the job.')
@click.option('--rw_list', help='[FIO] Type of I/O pattern.')
@click.option('--bs_list',
              help='[FIO] The block size in bytes used for I/O units.')
@click.option('--iodepth_list',
              help='[FIO] # of I/O units to keep in flight against the file.')
@click.option('--log_path', help='Where the *.fiolog files will be saved to.')
@click.option('--plots/--no-plots',
              is_flag=True,
              default=None,
              help='Generate \
bw/iops/lat logs and plots in their lifetime.')
@click.option('--dryrun',
              is_flag=True,
              default=None,
              help='Print the commands \
that would be executed, but do not execute them.')
def cli(backend, driver, fs, rounds, filename, runtime, ioengine, direct,
        numjobs, rw_list, bs_list, iodepth_list, log_path, plots, dryrun):
    """Command line interface.

    Take arguments from CLI, load default parameters from yaml file.
    Then initialize the fio test.

    """
    # Read user specified parameters from CLI
    cli_params = get_cli_params(backend, driver, fs, rounds, filename, runtime,
                                ioengine, direct, numjobs, rw_list, bs_list,
                                iodepth_list, log_path, plots, dryrun)

    # Read user configuration from yaml file
    yaml_params = get_yaml_params()

    # Combine user input and config
    params = {}
    params.update(yaml_params)
    params.update(cli_params)

    # Run fio test
    run_fio_test(params)

    exit(0)


if __name__ == '__main__':
    cli()
