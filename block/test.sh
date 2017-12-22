#!/bin/bash

# Discription:
# $1: disk type

PATH=~/workspace/bin:/usr/sbin:/usr/local/bin:$PATH

# setup
setup.sh

if [ "$1" != "" ]; then
	disktype=$1
else
	disktype=unknown
fi

inst_type=$(metadata.sh -t | awk '{print $2}')
time_stamp=$(timestamp.sh)
logfile=~/workspace/log/storage_performance_${inst_type}_${disktype}_${time_stamp}.log

# log the informaiton
show_info.sh >> $logfile 2>&1

# perform this test
function run_cmd(){
	# $1: Command

	echo -e "\n$ $1" >> $logfile
	eval $1 >> $logfile 2>&1
}

echo -e "\n\nTest Results:\n===============\n" >> $logfile

run_cmd 'setup_fio.sh'

run_cmd 'lsblk -d'
run_cmd 'lsblk -t'
run_cmd 'sudo blockdev --report'

mode=fio_script_test

# blind test for all parameters
if [ "$mode" = "blind_test" ]; then
	## fio.sh $log $disktype $rw $bs $iodepth
	fio.sh $logfile $disktype read 4k 1
	fio.sh $logfile $disktype read 16k 1
	fio.sh $logfile $disktype read 256k 1
	fio.sh $logfile $disktype read 1024k 1
	fio.sh $logfile $disktype read 2048k 1
	fio.sh $logfile $disktype write 4k 1
	fio.sh $logfile $disktype write 16k 1
	fio.sh $logfile $disktype write 256k 1
	fio.sh $logfile $disktype write 1024k 1
	fio.sh $logfile $disktype write 2048k 1
	fio.sh $logfile $disktype randread 4k 1
	fio.sh $logfile $disktype randread 16k 1
	fio.sh $logfile $disktype randread 256k 1
	fio.sh $logfile $disktype randread 1024k 1
	fio.sh $logfile $disktype randread 2048k 1
	fio.sh $logfile $disktype randwrite 4k 1
	fio.sh $logfile $disktype randwrite 16k 1
	fio.sh $logfile $disktype randwrite 256k 1
	fio.sh $logfile $disktype randwrite 1024k 1
	fio.sh $logfile $disktype randwrite 2048k 1

# choose parameters by disktype
elif [ "$mode" = "capacity_test" ]; then

	if [ "$disktype" = "gp2" ] || [ "$disktype" = "io1" ]; then
		# IOPS performance hit
		fio.sh $logfile $disktype randread 16k 1
		fio.sh $logfile $disktype randwrite 16k 1
		# BW performance hit
		fio.sh $logfile $disktype randread 256k 1
		fio.sh $logfile $disktype randwrite 256k 1
	fi

	if [ "$disktype" = "st1" ] || [ "$disktype" = "sc1" ]; then
		# IOPS and BW performance hit
		fio.sh $logfile $disktype read 1024k 1
		fio.sh $logfile $disktype write 1024k 1
	fi

elif [ "$mode" = "fio_script_test" ]; then

	cd ~/workspace/bin

	if [ "$disktype" = "gp2" ] || [ "$disktype" = "io1" ]; then
		# IOPS and BW performance hit
		fio2.sh $logfile $disktype ebs_ssd_randread.fio
		fio2.sh $logfile $disktype ebs_ssd_randwrite.fio
	fi

	if [ "$disktype" = "st1" ] || [ "$disktype" = "sc1" ]; then
		# IOPS and BW performance hit
		fio2.sh $logfile $disktype ebs_hdd_read.fio
		fio2.sh $logfile $disktype ebs_hdd_write.fio
	fi

elif [ "$mode" = "ebs_bandwidth_test" ]; then

	cd ~/workspace/bin

	# EBS Bandwidth Test
	fio2.sh $logfile multi-io1 ebs_bandwidth_test.fio

fi

# teardown
teardown.sh

exit 0

