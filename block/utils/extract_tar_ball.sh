#!/bin/bash

# Description: Extract the tarballs created by RunFioTest.py
# Maintainer: Charles Shih <schrht@gmail.com>

function show_usage() {
	echo "Extract the tarballs created by RunFioTest.py"
	echo "$(basename $0) [-h]"
	echo "Note: this script must be run under log path."
}

if [ "$1" = "-h" ]; then
	show_usage
	exit 0
fi
 
flist=$(ls fio_*.tar.gz) || exit 1

for f in $flist; do
	echo -e "\n$(basename $0): Dealing $f ..."
	d=${f%.tar.gz}

	if [ -d $d ]; then
		echo "$(basename $0): Already exists, skip."
		continue
	else
		mkdir -p $d
	fi

	echo "$(basename $0): Extracting..."
	tar -C $d -xf $f
done

exit 0

