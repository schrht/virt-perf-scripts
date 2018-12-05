# virt-perf-scripts

The Storage and Network Performance test scripts / suites for virtualization.

## Storage Performance Test - FIO test

This tool is designed for running an FIO benchmark in guest.

### Prepare the guest

1. Install [`fio`](https://github.com/axboe/fio/releases) on the guest.

2. Install the following Python modules:
- `click`
- `pandas`
- `numpy`
- `scipy`
- `yaml`

> Notes:  
> `yaml` can be installed with `python-yaml` or `python3-yaml` package via `yum`;
> Other modules can be install by `pip install <module-name>`.

3. Deliver the following scripts to the guest:
- `./block/RunFioTest.py`
- `./block/GenerateBenchmarkReport.py`
- `./block/GenerateTestReport.py`
- `./virt_perf_scripts.yaml`

### Run FIO test

The manual page of `RunFioTest.py`:

```
$ ./RunFioTest.py --help
Usage: RunFioTest.py [OPTIONS]

  Command line interface.

  Take arguments from CLI, load default parameters from yaml fisle. Then
  initialize the fio test.

Options:
  --backend TEXT           The backend device where vdisk image is based on.
  --driver TEXT            The driver to power the vdisk..
  --fs TEXT                The filesystem of the disk to be tested, "RAW" for
                           no fs.
  --rounds INTEGER RANGE   How many rounds the fio test will be repeated.
  --filename TEXT          [FIO] The disk or specified file(s) to be tested by
                           fio.
  --runtime TEXT           [FIO] Terminate a job after the specified period of
                           time.
  --direct [0|1]           [FIO] Direct access to the disk.
  --numjobs INTEGER RANGE  [FIO] Create the specified number of clones of the
                           job.
  --rw_list TEXT           [FIO] Type of I/O pattern.
  --bs_list TEXT           [FIO] The block size in bytes used for I/O units.
  --iodepth_list TEXT      [FIO] # of I/O units to keep in flight against the
                           file.
  --log_path TEXT          Where the *.fiolog files will be saved to.
  --help                   Show this message and exit.
```

If you run `./RunFioTest.py` without any parameter, it will load default value from `./virt_perf_scripts.yaml`. Please check the yaml file for details.

Typically, you should run the following command to provide enough information:

```
$ ./RunFioTest.py --backend NVME --driver SCSI --fs RAW --filename /dev/sdb --log_path $HOME/workspace/log/ESXi_FIO_RHEL7u6_20180809
```

This command will create `$HOME/workspace/log/ESXi_FIO_RHEL7u6_20180809` and generate *.fiolog file for each subcase to this path.

### Generate FIO test report

The manual page of `GenerateTestReport.py`:

```
$ ./GenerateTestReport.py --help
Usage: GenerateTestReport.py [OPTIONS]

  Command Line Interface.

Options:
  --result_path PATH  Specify the path where *.fiolog files are stored in.
  --report_csv PATH   Specify the name of CSV file for fio test reports.
  --help              Show this message and exit.
```

Typically, you should run the following command:

```
$ ./GenerateTestReport.py --result_path $HOME/workspace/log/ESXi_FIO_RHEL7u6_20180809 --report_csv ESXi_FIO_RHEL7u6_20180809.csv
```

This command will create a CSV test report with all the performance KPIs in.

### Generate FIO benchmark report

The manual page of `GenerateBenchmarkReport.py`:

```
$ ./GenerateBenchmarkReport.py --help
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
$ ./GenerateBenchmarkReport.py --base_csv ./ESXi_FIO_RHEL7u5_20180401.csv --test_csv ./ESXi_FIO_RHEL7u6_20180809.csv --report_csv ESXi_FIO_Benchmark_RHEL7u6_against_RHEL7u5_20180809.csv
```

This command will create a CSV benchmark report which comparing RHEL7.6 performance KPIs against RHEL7.5.

### Paste the results into Google Speardsheets

You can copy & paste the contents from CSV file into the [Template of Google Speardsheets](https://docs.google.com/spreadsheets/d/1C5DsB5oWXI0Wl5rGiCLQI09w2nbq96uovPYoF6rvM6Y/edit?usp=sharing). So that you could check the benchmark results much more conveniently.


## Network Performance Test - Netperf Test (Alpha)

The test suite is designed for running a network performance test in a Linux Guest.

### Prepare the guest

1. Install [`netperf`](https://github.com/HewlettPackard/netperf.git) on the guest.

2. Install [`sysstat`](git@github.com:sysstat/sysstat.git) on the guest.

3. Install the following Python modules:
- `click`
- `pandas`
- `numpy`
- `scipy`
- `yaml`

> Notes:  
> `yaml` can be installed with `python-yaml` or `python3-yaml` package via `yum`;
> Other modules can be install by `pip install <module-name>`.

4. Deliver the following scripts to the guest:
- `./network/main.sh`
- `./network/virt_netperf_pre_test.py`
- `./network/tools_installation.sh`
- `./network/virt_netperf_test.py`
- `./network/netperf_config.yaml`
> Notes:
> Run main.sh to complete these prepare steps before Netperf Test. Call it PRE-Test.

### Run Netperf test

The manual page of `virt_netperf_test.py`:

```
Usage: virt_netperf_test.py [OPTIONS] LOC_IP RMT_IP

  Command line interface. Take arguments from CLI, load default parameters
  from yaml file. Then initialize the netperf test.

Options:
  --log_path TEXT           DIR stores logs.
  --install_path TEXT       The script installs tools required.
  --ssh_key TEXT            The SSH KEY is used to access any VM.
  --exe_time INTEGER RANGE  How much time current netperf case run.
  --driver TEXT             NIC types include vmxnet3 / e1000 / e1000e.
                            Current ONLY supports vmxnet3.
  --instance INTEGER RANGE  [NETPERF]How many instances be started.
  --rounds INTEGER RANGE    How many rounds to run
  --data_modes TEXT         [NETPERF] Test modes includes STREAM and RR and
                            CRR
  --rr_size TEXT            [NETPERF] RR size when test RR mode
  --m_size TEXT             [NETPERF] M size when test STREAM mode
  --help                    Show this message and exit.
```

If you run `./virt_netperf_test.py LOC_IP RMT_IP`, it will load default value from `./netperf_config.yaml`. Please check the yaml file for details.

Typically, you should run the following command to provide enough information:

```
$ ./virt_netperf_test.py LOC_IP RMT_IP --log_path /tmp --install_path /root/install.sh --ssh_key ~/.ssh/id_rsa_private --exe_time 60 --driver vmxnet3 --instance 1 --rounds 2 --data_modes ["TCP_STREAM", "TCP_RR"] --rr_size [(256, 256), (512, 512)] --m_size [32, 64, 128]
```

This command will create `/tmp/netperf/` and generate *.nplog file for each subcase.