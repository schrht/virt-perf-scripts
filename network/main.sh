#!/bin/bash


########################################################################################
##  Descrition:
##      Main script to start NETPERF PRE and test
##
##  Revision:
##      v1.0.0 - boyang - 12/02/2018 - Built the program
##      v1.0.1 - boyang - 12/04/2018 - Optimize pip check and installation
##      v1.0.2 - boyang - 12/04/2018 - Optimize pip-packages check and installation
##      v1.0.3 - boyang - 12/04/2018 - Check IP(s) format
##      v1.0.4 - boyang - 12/05/2018 - Python packages pandas, numpy, scipy
########################################################################################


# Check argv count
test $# -eq 2 || { echo "ERROR: Missed Params. Need two IP as Param"; exit 1;}


# Check PIP
echo -e ""
echo -e "INFO: Checking PIP"
if [ -z `whereis pip | awk '{print $2}'` ]; then
    echo -e "WARNING: NO PIP. Try to install it"

    # Installation of pip
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py || { echo "ERROR: Curl PIP failed"; exit 1;}
    python get-pip.py || { echo "ERROR: Install PIP failed"; exit 1;}
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
        pip install $1 || { echo "ERROR: Install $1 package failed"; exit 1;}
    fi
}

check_pip_package pyyaml
check_pip_package click
check_pip_package pandas
check_pip_package numpy
check_pip_package scipy


# Check two IP available or not
function check_ip()
{
    echo -e ""
    echo -e "INFO: Checking IP $1"

    IP=$1
    VALID_CHECK=$(echo $IP|awk -F. '$1<=255&&$2<=255&&$3<=255&&$4<=255{print "yes"}')
    if echo $IP|grep -E "^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$">/dev/null; then
        if [ ${VALID_CHECK:-no} != "yes" ]; then
            echo "ERROR: IP [${IP}] is not available"
            exit 1
        fi
    else
        echo -e "ERROR: IP format error"
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
python virt_netperf_pre_test.py $loc_ip $rmt_ip || { echo "ERROR: Install tools required failed"; exit 1;}

echo -e ""
echo -e "INFO: Start virt netperf test"
python virt_netperf_test.py $loc_ip $rmt_ip
