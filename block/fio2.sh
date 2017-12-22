#!/bin/bash

# Description:
# $1: logfile
# $2: disktype (GP2, IO1, SC1, ST1)
# $3: fio script

PATH=~/workspace/bin:/usr/sbin:/usr/local/bin:$PATH

function get_value(){
	# This function lookup and print the value from $script file
	# Inputs:
	#     $1: key
	# Outputs:
	#     The value or "-" if not found

	value=$(grep "^$1=" $script | tail -1 | cut -d= -f2 | cut -f1)
	[ -z "$value" ] && echo "-" || echo $value
}

vmsize=$(metadata.sh -t | awk '{print $2}')
disktype=$2
script=$3
rw=$(get_value rw)
bs=$(get_value bs)
iodepth=$(get_value iodepth)
ioengine=$(get_value ioengine)
direct=$(get_value direct)
numjobs=$(get_value numjobs)
tformat=raw

tlog=$(mktemp)
logfile=$1

# write down debug log
echo "$0: Called by other scripts..." >> $logfile
echo "$0: Input parameter: $@" >> $logfile

# filename should be a disk
filename=$(get_value filename)
if [[ "$filename" =~ "/dev/" ]] && [ -z "$(lsblk -pd | grep $filename)" ]; then
	echo "$0: \"$filename\" is not a disk. Exit..." >> $logfile
	exit 1
fi

# Set Command
cmd="sudo fio $script"

# Run test
echo -e "\nTest Run: \n----------\n" >> $tlog

# Show fio script
echo -e "$ cat $script" >> $tlog
cat $script >> $tlog

# Run script
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
printf "** %-12s %-10s %-10s %-6s %-9s %-8s %-8s %-7s %-9s %-12s %-8s\n" VMSize DiskType I/OMode BS IOEngine IODepth Numjobs Direct Format "BW(KB/s)" IOPS >> $tlog
printf "** %-12s %-10s %-10s %-6s %-9s %-8s %-8s %-7s %-9s %-12s %-8s\n" $vmsize $disktype $rw $bs $ioengine $iodepth $numjobs $direct $tformat $BW $IOPS >> $tlog

# Save log
cat $tlog >> $logfile && rm $tlog

exit 0

