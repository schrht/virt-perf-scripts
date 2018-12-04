#!/bin/bash


########################################################################################
##  Descrition:
##      Main script to start NETPERF test
##
##  Revision:
##      v1.0.0 - boyang - 12/02/2018 - Built the program
##      v1.0.1 - boyang - 12/04/2018 - Optimize pip check and installation
##      v1.0.2 - boyang - 12/04/2018 - Optimize pip-packages check and installation
##      v1.0.3 - boyang - 12/04/2018 - Check IP(s) format
########################################################################################


# Check argv count
if [ $# -ne 2 ]; then
    echo "ERROR: Missed Params. Need two IP as Params"
    exit 1
fi


# Check PIP
echo -e ""
echo -e "INFO: Checking PIP"
if [ -z `whereis pip | awk '{print $2}'` ]; then
    echo -e "WARNING: NO PIP. Try to install it"

    # Installation of pip
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    if [ $? -ne 0 ]; then
        echo -e "ERROR: Curl PIP failed"
        exit 1
    fi

    python get-pip.py
    if [ $? -ne 0 ]; then
        echo -e "ERROR: Install PIP failed"
        exit 1
    fi
fi


# Check PIP packages
function check_pip_package()
{
    echo -e ""
    echo -e "INFO: Checking $1"
    pip show $1 > /dev/null
    if [ $? -ne 0 ]; then
        echo -e "WARNING: Package $1 doesn't exist. Try to install it"

        # PIP installs pyyaml
        pip install $1
        if [ $? -ne 0 ]; then
            echo -e "ERROR: Install $1 package failed"
            exit 1
        fi
    fi
}

check_pip_package pyyaml
check_pip_package click


# Check two IP available or not
function check_ip()
{
    echo -e ""
    echo -e "INFO: Checking IP $1"

    IP=$1
    VALID_CHECK=$(echo $IP|awk -F. '$1<=255&&$2<=255&&$3<=255&&$4<=255{print "yes"}')
    if echo $IP|grep -E "^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$">/dev/null; then
        if [ ${VALID_CHECK:-no} != "yes" ]; then
            echo "IP $IP not available!"
            exit 1
        fi
    else
        echo "IP format error!"
        exit 1
    fi
}

loc_ip=$1
check_ip $loc_ip
rmt_ip=$2
check_ip $rmt_ip


# Start NETPERF PRE test and test
echo -e ""
echo -e "INFO: Start virt netperf PRE test"
python virt_netperf_pre_test.py $loc_ip $rmt_ip
if [ $? -ne 0 ]; then
    echo -e "ERROR: Install tools required failed"
    exit 1
fi

echo -e ""
echo -e "INFO: Start virt netperf test"
python virt_netperf_test.py $loc_ip $rmt_ip
