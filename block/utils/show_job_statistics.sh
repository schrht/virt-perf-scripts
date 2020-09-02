#!/bin/bash

# Description: Show the job statistics in a table.
# Maintainer: Charles Shih <schrht@gmail.com>

function show_usage() {
	echo "Show the job statistics in a table."
	echo "$(basename $0) <-r RELEASE> <-s SERIES>"
	echo "RELEASE: RHEL7.9 RHEL8.3 ..."
	echo "SERIES : iops bw lat clat slat"
	echo "Note: this script must be run under log path."
}

function geometric_mean() {
	python -c 'from statistics import geometric_mean; import sys; \
		data=[float(x) for x in sys.stdin.readlines()]; \
		print(geometric_mean(data))'
}

function stdev() {
	python -c 'from statistics import stdev; import sys; \
		data=[float(x) for x in sys.stdin.readlines()]; \
		print(stdev(data))'
}

while getopts :hr:s: ARGS; do
	case $ARGS in
	h)
		# Help option
		show_usage
		exit 0
		;;
	r)
		# Release option
		release=$OPTARG
		;;
	s)
		# Series option
		series=$OPTARG
		;;
	"?")
		echo "$(basename $0): unknown option: $OPTARG" >&2
		;;
	":")
		echo "$(basename $0): option requires an argument -- '$OPTARG'" >&2
		echo "Try '$(basename $0) -h' for more information." >&2
		exit 1
		;;
	*)
		# Unexpected errors
		echo "$(basename $0): unexpected error -- $ARGS" >&2
		echo "Try '$(basename $0) -h' for more information." >&2
		exit 1
		;;
	esac
done

if [ -z $release ] || [ -z $series ]; then
	show_usage
	exit 1
fi

# Main

flist=$(ls *_$series.[0-9]*.log)

for file in $flist; do
	re=$release
	se=$(echo $file | sed 's/.*_\(\w*\).\([0-9]*\).log/\1/')
	no=$(echo $file | sed 's/.*_\(\w*\).\([0-9]*\).log/\2/')
	gm=$(cat $file | cut -f2 -d, | geometric_mean)
	sd=$(cat $file | cut -f2 -d, | stdev)
	pt=$(echo "scale=2; $sd*100/$gm" | bc)
	table="${table}$(printf '%s;%s;%d;%.2f;%.2f;%.2f%%' $re $se $no $gm $sd $pt)\n"
done

echo -e $table | sort -t ';' -k 3 -n |
	column -t -s ';' -R 3,4,5,6 -N Release,Series,Job#,Geomean,Stdev,Stdev%
exit 0
