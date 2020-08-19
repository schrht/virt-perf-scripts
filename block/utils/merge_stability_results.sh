#!/bin/bash

basename=$(find fio*.tar.gz| rev|cut -d. -f3- |rev)

tar -zxf fio*.tar.gz

for file in $(ls $basename*.log);do
    for ((i=500;i<=1192500;i+=500));do echo $i,;done > arr
    gawk -i inplace 'FNR==NR{a[NR]=$1;next}{$1=a[FNR]}1' arr $file
done
rm -f arr

items=(iops bw clat lat slat)
for item in ${items[@]};do
    awk '{if(NR>1)a[$1]+=$2}END{for(i in a)printf "%s %d, 0, 0\n",i,a[i]}' *_$item.*.log | sort -n > ${basename}_${item}.0.log
done

