#!/bin/bash


########################################################################################
##  Descrition:
##      Setup network performance test environment
##
##  Revision:
##      v1.0.0 - boyang - 04/24/2018 - Built the program
########################################################################################


# Check argv count
test $# -eq 2 || { echo "ERROR: Missed Argvs. Need two IP as Argvs"; exit 1;}


# Check two argvs (IP) available or not
function check_ip()
{
    echo -e "\033[34mINFO: Check IP provided: [$1]\033[0m" 

    ip=$1
    ip_check=$(echo $ip | awk -F . '$1<=255&&$2<=255&&$3<=255&&$4<=255 {print "yes"}')

    if echo $ip | grep -E "^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$" > /dev/null; then
        if [ ${ip_check:-no} != "yes" ]; then
    	    echo -e "\033[34mERROR: IP [${ip}] isn't available\033[0m" 
            exit 1
        fi
    else
    	echo -e "\033[34mERROR: IP [${ip}] is invalid format\033[0m" 
        exit 1
    fi
}

# Check local and remote IP
loc_ip=$1
check_ip $loc_ip
rmt_ip=$2
check_ip $rmt_ip


# Download source to VMs
# GIT or SCP source code to VMs
echo -e "\033[34mINFO: Download network performance test source code to client and server from controller\033[0m" 
scp -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa_private -r /root/performance/network root@$loc_ip:/root/ || { echo "ERROR: Download source code to $loc_ip";}
scp -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa_private -r /root/performance/network root@$rmt_ip:/root/ || { echo "ERROR: Download source code to $rmt_ip";}


# Run setup.sh in VMs
echo -e "\033[34mINFO: Controller trigger the setup script in client and server to setup the ENV\033[0m" 
ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa_private root@$loc_ip "/usr/bin/bash /root/network/env/setup.sh" || { echo "ERROR: Install expect failed in $loc_ip";}
ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa_private root@$rmt_ip "/usr/bin/bash /root/network/env/setup.sh" || { echo "ERROR: Install expect failed in $rmt_ip";}