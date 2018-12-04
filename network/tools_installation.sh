#!/bin/bash


########################################################################################
##  Descrition:
##      Install NETPERF required by performance test
##
##  Revision:
##      v1.0.0 - boyang - 09/17/2018 - Built the script
##      v1.1.0 - boyang - 10/14/2018 - Installation of NETPERF
##      v1.1.1 - boyang - 10/14/2018 - Installation of MPSTAT
##      v1.1.2 - boyang - 11/23/2018 - Change internal repo to centos repo as security
##      v1.1.3 - boyang - 11/23/2018 - Yum installs a tool if no function installs it
########################################################################################


# Check argv count
if [ $# -ne 1 ]; then
    echo "ERROR: NO argv is passed"
    exit 1
fi


# Part 1. INSTALLATION of NETPERF
function install_netperf()
{
    # Clone netperf
    echo -e "INFO: GIT Clone Netperf Phrase"
    git clone https://github.com/HewlettPackard/netperf.git /root/netperf
    if [ $? -ne 0 ];then
        echo "ERROR: Git clone netperf source code failed"
        exit 1
    fi
    
    # Install required packages before compile netperf
    echo -e "INFO: Install Pre-packages Phrase"
    yum -y install perl automake autoconf libtool bison flex
    if [ $? -ne 0 ];then
        echo "ERROR: Install perl or automake or autoconf or libtool or bison or flex failed"
        exit 1
    fi
    
    # As RHEL8 or higher also uses this package
    yum -y install http://rpmfind.net/linux/centos/7.5.1804/os/x86_64/Packages/help2man-1.41.1-3.el7.noarch.rpm
    if [ $? -ne 0 ];then
        echo "ERROR: Install help2man failed"
        exit 1
    fi
    
    # As RHEL8 or higher also uses this package
    yum -y install http://rpmfind.net/linux/centos/7.5.1804/os/x86_64/Packages/texinfo-5.1-5.el7.x86_64.rpm
    if [ $? -ne 0 ];then
        echo "ERROR: Install texinfo failed"
        exit 1
    fi
    
    # As RHEL8 or higher also uses this package
    yum -y install http://rpmfind.net/linux/centos/7.5.1804/os/x86_64/Packages/texinfo-tex-5.1-5.el7.x86_64.rpm
    if [ $? -ne 0 ];then
        echo "ERROR: Install texinfo-tex failed"
        exit 1
    fi
    
    # Compile tool netperf
    echo -e "INFO: Compile Netperf Phrase"
    cd /root/netperf
    ./autogen.sh && ./configure && make && make install && echo 0
    if [ $? -ne 0 ];then
        echo "ERROR: Compile netperf failed"
        exit 1
    fi
}    


# Part 2. INSTALLATION of MPSTAT
function install_sysstat()
{
    yum -y install sysstat
    if [ $? -ne 0 ];then
        echo "ERROR: Install sysstat(mpstat) failed"
        exit 1
    fi
}


# Main
if [ $1 == "netperf" ]; then
    echo "INFO: Install netperf tool"
    install_netperf
    exit 0
elif [ $1 == "sysstat" ]; then
    echo "INFO: Install sysstat"
    install_sysstat
    exit 0
else
    echo "WARNING: NO function installs $1. Try install it by yum"
    yum -y install $1
    if [ $? -ne 0 ];then
        echo "ERROR: Install $1 failed by yum"
        exit 1
    fi
fi
