#!/usr/bin/python


########################################################################################
# Function: 
#   Convert original log file to json log.
# Author:
#    boyang@redhat.com
# History:
#   v1.0.0 - 06/03/2020 - boyang - Draft script.
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
# kernel version.
kernel = platform.platform()
# VM CPU count
cpu = os.cpu_count()
# VM hostname and ip.
hostname = socket.gethostname()
local_host = socket.gethostbyname(hostname)

print("DEBUG: release %s" % release)
print("DEBUG: kernel %s" % kernel)
print("DEBUG: cpu %s" % cpu)
print("DEBUG: local_host %s" % local_host)

# Main network performace output.
rr_size=""
m_size=""


# Check logs path.
log_path = "/tmp/netperf_result/"
if not os.path.exists(log_path):
    print("WARNING: %s doesn't exist! Confirm netperf test has been done." % log_path)
    sys.exit(1)
else:
    print("INFO: %s exists!" % log_path)
    logs = os.listdir(log_path)
    if len(logs) == 0:
    	print("ERROR: Can't find any log file under %s." % log_path)    
    	sys.exit(1)
    else:
    	print("INFO: Found log files: %s" % logs)


# Handle every log. Convert it to a json file.
for l in logs:
    output_format = []
    print("INFO: =============Handle file: %s.=============" % l)

    # Current test case name
    cur_case = l.split("-")[0]
    data_modes = l.split("-")[0]
    # Driver
    driver = l.split("-")[1]
    # m_size or rr_size
    if "RR" in cur_case:
        print("INFO: RR or CRR size")
        rr_size = l.split("-")[2]
    else:
        print("INFO: M size")
        m_size = l.split("-")[2]
    # Instance
    instance = l.split("-")[3]
    # Rounds
    rounds = l.split("-")[4]
    # Timestamp
    timestamp = l.split("-")[5]

    with open (os.path.join(log_path, l), "r") as f:
        lines=f.readlines()

    print("DEBUG: lines: %s" % lines)

    keys=[k for k in range(0, len(lines))]
    result={k:v for k, v in zip(keys, lines[::-1])}
    # Last 26 lines incldues netperf output
    for i in range(26):
        output_format.append(result[i].replace("\n", ""))

    new_out = []
    # Make output_format like key: value
    for i in output_format:
        new_out.append(i.replace("=", ":"))
        
    output_format = new_out
    print("DEBUG: output_format: %s" % output_format)

    new_lines=[]
    keys=[]
    values=[]
    for i in output_format:
        keys.append(i.split(":")[0])
        values.append(i.split(":")[1])
    
    new_format = dict(zip(keys,values))
    print("debug new %s" % new_format)
	    
    template2 = {
	"metadata": {
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
            "SERIES_META": {
	       	cur_case: new_format
	    }
	}
    }
	

    json_str = json.dumps(template2, indent=4)
    print("DEBUG: json: %s" % json_str)


    # Write tempalte2 to a json file.
    with open(os.path.join(log_path, l + ".json"), "w") as fw:
        json.dump(template2, fw, indent=4)
