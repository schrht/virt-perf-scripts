# _*_encoding:utf-8_*_

############################################################################
#
# Functions:
#   Test IPv4 / IPv6 performance of different RHELs in vSphere with netperf
#
# Versions:
#   v1.0.0 - 06/29/2018 - boyang - Draft the script
#
############################################################################

import os,sys

root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root)

