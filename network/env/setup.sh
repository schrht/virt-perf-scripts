#!/bin/bash


########################################################################################
##  Descrition:
##      Install Miniconda and netperf
##
##  Revision:
##      v1.0.0 - boyang - 04/25/2019 - Built the program
########################################################################################


# Check target VM kernel info to select a related Anaconda
function install_anaconda()
{
    # Check VM's kernel
    kernel_ver=`uname -r | grep -E "^4\.[0-9]+\.[0-9]+"`

    if [ -f /root/miniconda/bin/conda ]; then
	echo -e "\033[34mINFO: Miniconda has been installed, skip its installation\033[0m" 
    else
    	# Kernel means 3.6.10
    	if [ -z $kernel_ver ]; then
	    echo -e "\033[34mINFO: Suggest to install a Miniconda2\033[0m" 
            wget https://repo.anaconda.com/miniconda/Miniconda2-latest-Linux-x86_64.sh -O /root/miniconda.sh || { echo "ERROR: WGET anaconda2 installer failed"; exit 1;}
    	# Kernel means 4.18.0
    	else
	    echo -e "\033[34mINFO: Suggest to install a Miniconda3\033[0m" 
            wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /root/miniconda.sh || { echo "ERROR: WGET anaconda3 installer failed"; exit 1;}
	fi

    	# Install the miniiconda
    	bash /root/miniconda.sh -b -p /root/miniconda

    	# Source miniconda bin, includes pip, conda
    	echo -e "\n# Add: Miniconda\nPATH=$PATH:/root/miniconda/bin/" >> /root/.bashrc
	source /root/.bashrc
    fi
}


# Check python packages required, if not, pip installs them
function check_pip_package()
{
    # Install package $1 passed
    echo -e "\033[34mINFO: Check package [${1}] exists or not\033[0m" 
    pip3 show $1 > /dev/null
    if [ $? -ne 0 ]; then 
    	echo -e "\033[33mWARNING: Package[${1}] doesn't exist, try to install\033[0m" 
        pip3 install --user $1 || { echo "ERROR: Install $1 package failed"; exit 1;}
    fi
}


function install_dependencies_packages()
{
    echo -e "\033[34mINFO: Install dependencies packages. If can't install some of them, based on error info, install them by manual, and run again\033[0m" 
    yum -y install perl automake autoconf libtool bison flex sysstat bzip2
    yum -y install http://rpmfind.net/linux/centos/7/os/x86_64/Packages/help2man-1.41.1-3.el7.noarch.rpm
    yum -y install http://rpmfind.net/linux/centos/7/os/x86_64/Packages/texinfo-5.1-5.el7.x86_64.rpm
    yum -y install http://rpmfind.net/linux/centos/7/os/x86_64/Packages/texlive-epsf-svn21461.2.7.4-43.el7.noarch.rpm
    yum -y install http://rpmfind.net/linux/centos/7/os/x86_64/Packages/texinfo-tex-5.1-5.el7.x86_64.rpm
}


# Install netperf and netserver
function install_netperf()
{
    # Clone netperf
    echo -e "\033[34mINFO: GIT clone netperf source code\033[0m" 
    rm /root/netperf -rf
    git clone https://github.com/HewlettPackard/netperf.git /root/netperf || { echo "ERROR: Git clone netperf source code failedli"; exit 1;}
    
    # Compile  netperf source code
    echo -e "\033[34mINFO: Compile netperf source code\033[0m" 
    cd /root/netperf
    ./autogen.sh && ./configure && make && make install && echo 0
    if [ $? -ne 0 ];then
    	echo -e "\033[31mERROR: Compile netperf source code failed\033[0m" 
        exit 1
    fi
}    


# Main
install_dependencies_packages
install_anaconda
install_netperf
check_pip_package pyyaml
check_pip_package click
check_pip_package pandas
check_pip_package numpy
check_pip_package scipy
