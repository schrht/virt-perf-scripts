#!/bin/bash

# Description:
# This script used to update the "desciption" according to the log name.

filelist=$(ls *.fiolog)

for file in $filelist; do
	echo "file name: $file"

	# example: gen1_SCSI_raw_write_64k_1_devsdd_1.fiolog
	backend="nvme-ssd"
	driver=$(echo $file | cut -d '_' -f 2)
	round=$(echo $file | cut -d '_' -f 8 | cut -d '.' -f 1)
	format=$(echo $file | cut -d '_' -f 3)
	if [ "$format" = "fs" ]; then
		format="xfs"
	fi

	# update the files
	cp $file ${file}.bak
	target_string="{'backend': \'$backend\', 'driver': \'$driver\', 'round': \'$round\', 'format': \'$format\'}"
	echo $target_string
	sed -i "s/N\/A/$target_string/" $file
done

exit 0
