#!/usr/bin/python


########################################################################################
# Function: Convert original log file to json log.
# Reversion: 1.0.0
# Author: boyang@redhat.com
# History:
#	1.0.0 - 06/03/2020 - boyang - Draft script.
########################################################################################


import os
import sys
import json
import socket
import platform
import subprocess


# Get basic info of netperf VM.
# Linux release.
release = subprocess.Popen("cat /etc/redhat-release", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
release = release.stdout.read().decode("utf-8").strip("\n")
print("DEBUG: release %s" % release)
# kernel version.
kernel = platform.platform()
print("DEBUG: kernel %s" % kernel)
# VM CPU count
cpu = os.cpu_count()
print("DEBUG: cpu %s" % cpu)
# VM hostname and ip.
hostname = socket.gethostname()
local_host = socket.gethostbyname(hostname)
print("DEBUG: local_host %s" % local_host)
# Netserver host ip.
#remote_host = ""
# Main network performace output.
output_format=""
rr_size=""
m_size=""

# Check logs path.
log_path = "/tmp/netperf_result_test/"
if not os.path.exists(log_path):
	print("WARNING: %s doesn't exist!" % log_path)
	sys.exit(1)
else:
    logs = os.listdir(log_path)
    if len(logs) == 0:
    	print("ERROR: Can't find logs files")    
    	sys.exit(1)
    else:
    	print("INFO: Found logs files: %s" % logs)

    print("INFO: %s exists!" % log_path)


# Handle every log. Convert it to a json file.
for l in logs:
    print("INFO: Handle file: %s" % l)

    # Current test case name
    cur_case = l.split("-")[0]
    data_modes = l.split("-")[0]
    # Driver
    driver = l.split("-")[1]
    # m_size or rr_size
    if "RR" in cur_case:
        print("RR or CRR size")
        rr_size = l.split("-")[2]
    else:
        m_size = l.split("-")[2]
    # Instance
    instance = l.split("-")[3]
    # Rounds
    rounds = l.split("-")[4]
    # Timestamp
    timestamp = l.split("-")[5]

    with open (os.path.join(log_path, l), "r") as f:
        lines=f.readlines()

    # If logs lines < 35, maybe it can't capture netperf output.

    print("debug: lines %s" % lines)
    new_lines=[]
    keys=[]
    values=[]
    for n in lines:
        n=n.strip("\n")
        n=n.replace("=", ":")
        keys.append(n.split(":")[0])
        values.append(n.split(":")[1])

    print(keys)
    print(values)
    output_format = dict(zip(keys,values))
    print("debug: output_format: %s" % output_format)

	    
    template2 = {
	"metadata": {
            "BATCH_NAME": "n/a",
            "BATCH_TIME": "n/a",
            "BATCH_TITLE": "n/a",
            "BATCH_UUID": "n/a",
            "DATA_FILENAME": l,
            "EGRESS_INFO": "n/a",
            "FAILED_RUNNERS": 0,
            "FLENT_VERSION": "n/a",
            "HOST": "n/a",
            "HOSTS": "n/a",
            "HTTP_GETTER_DNS": "n/a",
            "HTTP_GETTER_URLLIST": "n/a",
            "HTTP_GETTER_WORKERS": "n/a",
            "IP_VERSION": 4,
            "KERNEL_NAME": "Linux",
            "RELEASE": release,
            "KERNEL_RELEASE": kernel,
            "DRIVER": driver,
            "INSTANCE": instance,
            "ROUNDS": rounds,
            "DATA_MODES": data_modes,
            "RR_SIZE": rr_size,
            "M_SIZE": m_size,
            "INSTANCE": instance,
            "CPU_COUNT": cpu,
            "NAME": cur_case,
            "TIMESTAMP": timestamp,
            "LENGTH": 60,
            "MODULE_VERSIONS": "n/a",
            "NOTE": "n/a",
            "REMOTE_METADATA": "n/a",
            "SERIES_META": {
	        "Ping (ms) ICMP": "n/a",
	       	"test_output": output_format
	    },
            "STEP_SIZE": 0.2,
            "SYSCTLS": "n/a",
            "T0": "n/a",
            "TEST_PARAMETERS": "n/a",
            "TIME": "n/a",
            "TITLE": "",
            "TOTAL_LENGTH": "n/a"
	},
	"raw_values": {
	    "Ping (ms) ICMP": [],
	    "tcp_stream":[]
	},
	"results": {
	    "Ping (ms) ICMP": [],
	    "tcp_stream":[]
	},
        "version": 4,
	"x_values": []
    }
	
    json_str = json.dumps(template2, indent=4)
    print("DEBUG: json: %s" % json_str)
	
    # Write tempalte2 to a json file
    with open(os.path.join(log_path, l + ".json"), "w") as fw:
        json.dump(template2, fw, indent=4)
