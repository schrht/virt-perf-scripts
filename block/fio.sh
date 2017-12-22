#!/bin/bash

# Description:
# $1: logfile
# $2: disktype (GP2, IO1, SC1, ST1)
# $3: fio - rw (read, write, randread, ...)
# $4: fio - bs (4k, 16k, 64k, 256k, ...)
# $5: fio - iodepth (1, 8, 64, ...)

PATH=~/workspace/bin:/usr/sbin:/usr/local/bin:$PATH

vmsize=$(metadata.sh -t | awk '{print $2}')
disktype=$2
rw=$3
bs=$4
iodepth=$5
tformat=raw

tlog=$(mktemp)
logfile=$1

# When testing this case, only one volume should be attached once
if [ "$(lsblk -d | grep -v NAME | grep -v xvda | wc -l)" != "1" ]; then
	echo "Not only one additional volume attached, exit." && exit 1
else
	dev=$(lsblk -d -p --output NAME | grep -v NAME | grep -v xvda)
fi

filename=$dev	# raw format test

# Set Command
cmd="sudo fio --rw=$rw --size=10G --bs=$bs --iodepth=$iodepth --ioscheduler=deadline --direct=1 \
	--filename=$filename -ioengine=libaio --thread --group_reporting --numjobs=16 \
	--name=test --runtime=1m --time_based"

# Run test
echo -e "\nTest Run: \n----------\n" >> $tlog
echo -e "\n$ $cmd" >> $tlog
eval $cmd >> $tlog 2>&1

# Get the BW and IOPS

if [ "$(grep IOPS $tlog | wc -l)" = "0" ]; then
	# fio-2.2.8
	# read : io=1280.1MB, bw=21845KB/s, iops=5461, runt= 60043msec
	BW=`grep iops $tlog | awk -F', ' '{ split($2, parts1, "=") } { split(parts1[2], parts2, "K") } { print parts2[1] }'`
	IOPS=`grep iops $tlog | awk -F', ' '{ split($3, parts3, "=") } { print parts3[2]}'`
else
	# fio-2.20
	# read: IOPS=3109, BW=12.1MiB/s (12.7MB/s)(729MiB/60005msec)
	BW=`grep IOPS $tlog | cut -d= -f3 | cut -d" " -f1`
	IOPS=`grep IOPS $tlog | cut -d= -f2 | cut -d, -f1`
fi

# Write down a summary
echo -e "\nTest Summary: \n----------\n" >> $tlog
printf "** %-12s %-10s %-10s %-6s %-9s %-9s %-12s %-8s\n" VMSize DiskType I/OMode BS IODepth Format "BW(KB/s)" IOPS >> $tlog
printf "** %-12s %-10s %-10s %-6s %-9s %-9s %-12s %-8s\n" $vmsize $disktype $rw $bs $iodepth $tformat $BW $IOPS >> $tlog

# Save log
cat $tlog >> $logfile && rm $tlog

exit 0

