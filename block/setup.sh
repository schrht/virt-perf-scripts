#!/usr/bin/env bash

# Description:
#   Setup environment for running on RHEL.
#
# History:
#   v1.0  2019-12-02  yuxin.sun     init version
#   v1.1  2019-12-30  charles.shih  install gnuplot
#   v1.2  2020-01-02  charles.shih  install sysstat

# Get system info
project=$(cat /etc/redhat-release | grep -Po 'release \K[0-9]*')
echo "Setup block test environment in RHEL-$project..."

# Install fio
yum install -y libaio-devel fio gnuplot

# Install sysstat (sar)
yum install -y sysstat
systemclt enable --now sysstat

# Install Python runtime
if [[ x$project == x'7' ]]; then
    yum install -y python python-yaml
    pip install click pandas numpy scipy
elif [[ x$project == x'8' ]]; then
    yum install -y python3 python3-yaml
    ln -s /usr/bin/python3 /usr/bin/python
    pip3 install click pandas numpy scipy
else
    echo "RHEL-$project is not supported!"
    exit 1
fi

echo "Setup finished!"
exit 0
