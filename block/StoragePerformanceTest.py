#!/usr/bin/env python

import signal
import sys
import os
import re
import logging
import commands
import subprocess
import shutil
import smtplib
import tempfile
import time
from MakeTestReport import MakeTestReport
if sys.version < '2.5':
    from email.MIMEText import MIMEText
else:
    from email.mime.text import MIMEText
from argparse import ArgumentParser

smtpserver = "smtp.corp.redhat.com"
mail_from = "xuli@redhat.com"
mail_to = ["xuli@redhat.com"]

# Test requirement
#Gen1:
#IDE: /home (fs belongs to /sda2)
#IDE: /dev/sdb  (add disk raw disk)
#SCSI: /mnt/tmp (add disks. format, mount from /dev/sdc1 to /mnt, touch tmp file /mnt/tmp)
#SCSI: /dev/sdd (add disk raw disk)

#(fs, raw)

#Gen2:
#SCSI: /home  (fs belongs to /sda2)
#SCSI: /dev/sdb (add disk raw disk)

# 5 string, by default


def send_email(subject, content):

    msg = MIMEText(content, _subtype='plain', _charset='utf-8')
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = ','.join(mail_to)

    try:
        server = smtplib.SMTP()
        server.connect(smtpserver)
        server.sendmail(mail_from, mail_to, msg.as_string())
        server.close()
    except Exception, e:
        print str(e)

class StoragePerformanceTest:

    def __init__(self):

        if os.path.exists('/sys/firmware/efi'):
            self.m_gen_type = 'gen2'
        else:
            self.m_gen_type = 'gen1'

        # default value for parameter
        self.m_disk_type='SCSI_fs'
        self.m_filename= None
        self.m_runtime='1m'
        self.m_fs_type='xfs'

        # run how many round performance tets, if 0, only generate report
        self.m_test_round=5
        self.m_direct='1'
        # 1 cost string
        self.m_numbjobs='16'

        #m_rw=['write','read','randwrite','randread','randrw']
        #4 loop array

        # *) rw, "read write randread randwrite rw randrw" 
        # *) bs, "4k 16k 64k 256k" 
        # *) iodepth, "1 8 64", IO Engine = libaio 
        self.m_rw= ['read', 'write', 'randread', 'randwrite', 'rw', 'randrw']
        self.m_bs=['4k','16k', '64k','256k']
        self.m_iodepth=['1', '8', '64']
        self.m_disk_filename_dic={}

        self.m_dir_result=r"./csv_result"
        self.m_dir_report= r"./csv_report"

    def parse_argument(self):
        """
        Description:
            Parse input argument for fio, test round .etc
        Input Parameter:
            None
        Return Value:
            None
        """

        # running command "python mk_iso.py -b RHEL-7.2-20151030.0 -d"
        parser = ArgumentParser()

        parser.add_argument("-rw", type=str, dest='m_rw',help="set the rw mode, write,read,randrw", required=False)
        parser.add_argument("-bs", type=str, dest='m_bs',help="set the block size, 4k,16k,128k", required=False)
        parser.add_argument("-iodepth", type=str, dest='m_iodepth',help="set the iodepth, 1,16", required=False)
        parser.add_argument("-filename", type=str, dest='m_filename',help="set the test file path, /dev/sdb,/mnt", required=False)

        parser.add_argument("-disk_type", type=str, dest='m_disk_type',help="set the disk type, fc_raw,fc_fs,scsi_raw,scsi_fs,ide_raw,ide_fs,ssd", required=False)
        parser.add_argument("-runtime", type=str, dest='m_runtime',help="set the run time duration", required=False)
        parser.add_argument("-fs_type", type=str, dest='m_fs_type',help="set the test file system type, xfs,ext4 ", required=False)
        parser.add_argument("-direct", type=str, dest='m_direct',help="set the direct option, whether use cache data", required=False)
        parser.add_argument("-test_round", type=int, dest='m_test_round',help="set the test round number, if set as 0, only generate report", required=False)

        parser.add_argument("-dir_result", type=str, dest='m_dir_result',help="set the fio output file directory", required=False)
        parser.add_argument("-dir_report", type=str, dest='m_dir_report',help="set the final test report directory", required=False)

        args = parser.parse_args()

        if args.m_rw !=None:
            self.m_rw = args.m_rw.split(",")

        if args.m_bs !=None:
            self.m_bs = args.m_bs.split(",")

        if args.m_iodepth !=None:
            self.m_iodepth = args.m_iodepth.split(",")


        if args.m_filename !=None:
            self.m_filename = args.m_filename.split(",")


        if args.m_disk_type !=None:
            self.m_disk_type = args.m_disk_type.split(",")


        if args.m_runtime !=None:
            self.m_runtime = args.m_runtime


        if args.m_fs_type !=None:
            self.m_fs_type = args.m_fs_type


        if args.m_test_round !=None:
            self.m_test_round = args.m_test_round


        if args.m_direct !=None:
            self.m_direct = args.m_direct

        if args.m_dir_result !=None:
            self.m_dir_result = args.m_dir_result

        if args.m_dir_report !=None:
            self.m_dir_report = args.m_dir_report

        if self.m_filename == None:
            if self.m_gen_type=='gen2':
                self.m_disk_filename_dic={'SCSI_fs':'/home/tmp','SCSI_raw':'/dev/sdb'}

            elif self.m_gen_type=='gen1':
                self.m_disk_filename_dic={'IDE_fs':'/home/tmp','IDE_raw':'/dev/sdb', 'SCSI_fs':'/mnt/tmp','SCSI_raw':'/dev/sdd'}
                if not os.path.exists('/home/tmp'):
                    os.system('touch /home/tmp')
            #TODO, check /dev/sdc mounted to /mnt
        else:
                temp_disk_type=0
                for m_filename_item in self.m_filename:
                    if not os.path.exists(m_filename_item):
                        raise Exception("filename path does not exist%s" %m_filename_item)
                    for m_disk_type_item in self.m_disk_type:
                        self.m_disk_filename_dic[m_disk_type_item+str(temp_disk_type)]=m_filename_item
                        temp_disk_type=temp_disk_type+1

    def do_fio_run(self):

        file_number=0
        for m_test_round_item in range(0, self.m_test_round):
            for m_rw_item in self.m_rw:
                for m_bs_item in self.m_bs:
                    for m_iodepth_item in self.m_iodepth:
                        for m_disk_filename_dic_key in self.m_disk_filename_dic:

                            m_filename_item=self.m_disk_filename_dic[m_disk_filename_dic_key]

                            seq= (self.m_gen_type,m_disk_filename_dic_key,m_rw_item,m_bs_item,m_iodepth_item,m_filename_item,str(m_test_round_item)); # This is sequence of strings.
                            output_name="_".join( seq )
                            output_name = output_name
                            output_name = output_name.replace(os.sep,'')
                            output_name_csv = output_name+".csv"
                            output_name_csv = self.m_dir_result + os.sep+ output_name_csv
                            if not os.path.exists(self.m_dir_result):
                                os.mkdir(self.m_dir_result)

                            #command="fio -filename=%s --name=%s --ioengine=libaio --iodepth=%s --rw=%s --bs=%s --direct=%s --size=2048M --numjobs=%s --runtime=%s --group_reporting --output=%s" %(m_filename_item,output_name,m_iodepth_item, m_rw_item,m_bs_item, self.m_direct, self.m_numbjobs, self.m_runtime, output_name_csv)
                            command="fio -filename=%s --name=%s --ioengine=libaio --iodepth=%s --rw=%s --bs=%s --direct=%s --size=2048M --numjobs=%s --runtime=%s --group_reporting --output=%s" %(m_filename_item,output_name,m_iodepth_item, m_rw_item,m_bs_item, self.m_direct, self.m_numbjobs, self.m_runtime, output_name_csv)
                            os.system(command)
                            time.sleep(1)
                            print command
                            print "current test number is:" ,file_number
                            print "======================================================\n"
                            file_number = file_number+1




if __name__ == '__main__':

    starttime= time.time()
    time.sleep(5)

    print "Start to run fio performance test ! \n"

    # Run performa
    storage_performance = StoragePerformanceTest()
    storage_performance.parse_argument()
    storage_performance.do_fio_run()
    time.sleep(1)
    print "Start to generate fio performance test report! \n"
    make_report = MakeTestReport(storage_performance.m_dir_result, storage_performance.m_dir_report)
    make_report.parse_result_to_report()
    time.sleep(5)

    #print "total file number is:", file_number
    endtime= time.time()
    duration_time= (endtime-starttime)/60.0
    print "total running duration is: %s minutes" %duration_time

    send_email("Have done storage performance test",
                    "----------\nThis is a mail sent automatically by performance test MakeTestReport.py")
    sys.exit(0)
