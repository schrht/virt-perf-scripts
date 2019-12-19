# virt-perf-scripts

The performance test scripts for virtualization.

# FIO test

This tool is designed for running an FIO benchmark in guest.

## Prepare the guest

1. Install [`fio`](https://github.com/axboe/fio/releases) on the guest.

> `sudo yum install -y fio`

2. Install the following Python modules:
- `click`
- `pandas`
- `numpy`
- `scipy`
- `yaml`

> Notes:  
> You can use `./block/setup.sh` on RHEL systems.

3. Deliver the following scripts to the guest:
- `./block/RunFioTest.py`
- `./block/GenerateBenchmarkReport.py`
- `./block/GenerateTestReport.py`
- `./virt_perf_scripts.yaml`

## Run FIO test

The manual page of `RunFioTest.py`:

```
$ python3 ./RunFioTest.py --help
Usage: RunFioTest.py [OPTIONS]

  Command line interface.

  Take arguments from CLI, load default parameters from yaml file. Then
  initialize the fio test.

Options:
  --backend TEXT           The backend device where vdisk image is based on.
  --driver TEXT            The driver to power the vdisk..
  --fs TEXT                The filesystem of the disk to be tested, "RAW" for
                           no fs.
  --rounds INTEGER RANGE   How many rounds the fio test will be repeated.
  --filename TEXT          [FIO] The disk(s) or specified file(s) to be tested
                           by fio. You can specify a number of targets by
                           separating the names with a ':' colon.
  --runtime TEXT           [FIO] Terminate a job after the specified period of
                           time.
  --ioengine TEXT          [FIO] Defines how the job issues I/O to the file.
                           Such as: 'libaio', 'io_uring', etc.
  --direct INTEGER RANGE   [FIO] Direct access to the disk.
  --numjobs INTEGER RANGE  [FIO] Create the specified number of clones of the
                           job.
  --rw_list TEXT           [FIO] Type of I/O pattern.
  --bs_list TEXT           [FIO] The block size in bytes used for I/O units.
  --iodepth_list TEXT      [FIO] # of I/O units to keep in flight against the
                           file.
  --log_path TEXT          Where the *.fiolog files will be saved to.
  --dryrun                 Print the commands that would be executed, but do
                           not execute them.
  --help                   Show this message and exit.
```

If you run `./RunFioTest.py` without any parameter, it will load default value from `./virt_perf_scripts.yaml`. Please check the yaml file for details.

Typically, you should run the following command to provide enough information:

```
$ python3 ./RunFioTest.py --backend NVME --driver SCSI --fs RAW --filename /dev/sdb --log_path $HOME/workspace/log/ESXi_FIO_RHEL7u6_20180809
```

This command will create `$HOME/workspace/log/ESXi_FIO_RHEL7u6_20180809` and generate *.fiolog file for each subcase to this path.

## Generate FIO test report

The manual page of `GenerateTestReport.py`:

```
$ python3 ./GenerateTestReport.py --help
Usage: GenerateTestReport.py [OPTIONS]

  Command Line Interface.

Options:
  --result_path PATH  Specify the path where *.fiolog files are stored in.
  --report_csv PATH   Specify the name of CSV file for fio test reports.
  --help              Show this message and exit.
```

Typically, you should run the following command:

```
$ python3 ./GenerateTestReport.py --result_path $HOME/workspace/log/ESXi_FIO_RHEL7u6_20180809 --report_csv ESXi_FIO_RHEL7u6_20180809.csv
```

This command will create a CSV test report with all the performance KPIs in.

## Generate FIO benchmark report

The manual page of `GenerateBenchmarkReport.py`:

```
$ python3 ./GenerateBenchmarkReport.py --help
Usage: GenerateBenchmarkReport.py [OPTIONS]

  Command Line Interface.

Options:
  --base_csv PATH    Specify the CSV file of the base samples.
  --test_csv PATH    Specify the CSV file of the test samples.
  --report_csv PATH  Specify the CSV file to store the benchmark report.
  --help             Show this message and exit.
```

Typically, you should run the following command:

```
$ python3 ./GenerateBenchmarkReport.py --base_csv ./ESXi_FIO_RHEL7u5_20180401.csv --test_csv ./ESXi_FIO_RHEL7u6_20180809.csv --report_csv ESXi_FIO_Benchmark_RHEL7u6_against_RHEL7u5_20180809.csv
```

This command will create a CSV benchmark report which comparing RHEL7.6 performance KPIs against RHEL7.5.

### About the index and conclusion

The conclusion can be the following values in specific situations:
```
Conclusion              Situation
Data Invalid            The input data is invalid;
Variance Too Large      The %SD beyonds the MAX_PCT_DEV;
No Difference           The %DIFF is zero;
No Significance         The Significance less than CONFIDENCE_THRESHOLD;
Major Improvement       The Significance beyonds CONFIDENCE_THRESHOLD and %DIFF beyonds REGRESSION_THRESHOLD;
Major Regression        The Significance beyonds CONFIDENCE_THRESHOLD and %DIFF beyonds REGRESSION_THRESHOLD;
Minor Improvement       The Significance beyonds CONFIDENCE_THRESHOLD but %DIFF belows REGRESSION_THRESHOLD;
Minor Regression        The Significance beyonds CONFIDENCE_THRESHOLD but %DIFF belows REGRESSION_THRESHOLD;

MAX_PCT_DEV = 10
REGRESSION_THRESHOLD = 5
CONFIDENCE_THRESHOLD = 0.95
```

Calculation:
```
AVG = SUM(the performance number of sample 1~5) / 5
%SD = (The Standard Deviation of the 5 samples) / AVG * 100%
%DIFF = (TEST-AVG - BASE-AVG) / BASE-AVG * 100%
Significance = (1 - TTEST(BASE Sample 1~5, TEST Sample 1~5))
```

## Paste the results into Google Speardsheets

You can copy & paste the contents from CSV file into the [Template of Google Speardsheets](https://drive.google.com/open?id=1cdz1m8dPNoaH-dkOAxSbhvg-fFIdY7hh). So that you could check the benchmark results much more conveniently.
