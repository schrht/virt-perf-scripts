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
import glob
from time import gmtime, strftime
if sys.version < '2.5':
    from email.MIMEText import MIMEText
else:
    from email.mime.text import MIMEText
from argparse import ArgumentParser

LOG = logging.getLogger(__name__)



class MakeTestReport:
    def __init__(self, dir_input, dir_output):

        self.dir_input= dir_input
        self.dir_output= dir_output

    def get_single_dic(self,fh):
        """
        Description:
                Get the single result dic from one original result file by matching the format
                read : io=1869.4MB, bw=31894KB/s, iops=7973, runt= 60017msec
                write: io=4360.0KB, bw=3382.5KB/s, iops=845, runt= 1289msec
        Input Parameter:
                fh - single result file, e.g gen1_SCSI_fs_randrw_4k_1_mnttmp_1.csv
        Return Value:
                return single_dic e.g.: {'rw_write': {'iops': '154', 'bw': '634541B/s'}, 'rw_read': {'iops': '169', 'bw': '695143B/s'}}
        """
        model= re.compile('[read|write]\s*:\s*io=\d+.*\d*[MB|KB|B], bw=\d+.*\d*[KB|B]/s, iops=\d+')

        target_lines=[]
        with open(fh) as fp:
            for line in fp:
                line=line.strip()
                result =model.search(line)
                if result != None:
                    target_lines.append(line)

        single_dic={}
        len_target = len(target_lines)
        for line in target_lines:
            contents = line.split(":")
            if len_target==2: # for rw with two lines
                contents[0]="rw_"+contents[0]
            pairs=contents[1].split(",")
            sub_dic={}
            for pair in pairs:
                p_temp = pair.split("=")
                p_key=p_temp[0]
                p_value = p_temp[1]
                p_key=p_key.strip()
                p_value=p_value.strip()
                if p_key=="bw" or p_key=="iops":
                    sub_dic[p_key] = p_value
            single_dic[contents[0].strip()] = sub_dic

        return single_dic

    def calculate_average(self,file_uniq_item,full_dic, rw_type, evaluate_type):

        """
        Description:
            Get on aveage dic to all the files based on include many round result, key is full file name e.g. gen1_IDE_fs_randrw_4k_1_hometmp_0.csv,
            dic value is still dictionary about bw, iops by looping all the files.
        Input Parameter:
            file_uniq_item: file name without test round number, gen1_IDE_fs_randrw_4k_1_hometmp
            full_dic: one dic to include all the files result, including the different running rounds
            rw_type: can be 'read','write','rw_read','rw_write'
            evaluate_type: can be 'iops','bw'

        Return Value:
            v_dic: dic about the average value.e.g. {'avg_rw_write_bw': '1405.4'} or {'avg_rw_write_iops': '351.0'}

        """

        v_sum=0
        v_avearage=0
        v_rw_sufix=""
        v_dic ={}

        if rw_type not in ['read','write','rw_read','rw_write']:
            raise Exception("Please set the correct rw_type")

        if evaluate_type not in ['iops','bw']:
            raise Exception("Please set the correct property")

        count=0
        # item_key: file name includes test round
        for item_key in full_dic.keys():

            if item_key.find(file_uniq_item)!=-1:
                v_value = full_dic[item_key][rw_type][evaluate_type]
                # re compiled model for 1376.1 from {bw:1376.1KB/s} dic
                v_model_number= re.compile("\d+.?[0-9]")
                v_value_number = v_model_number.match(v_value).group(0)

                v_model_suffix = re.compile("B|KB|MB", re.I)
                v_temp = v_model_suffix.search(v_value)

                # if this is value of bw including the suffix "B|KB|MB"
                if v_temp!=None:

                    v_rw_sufix=v_temp.group(0)
                    #if shows as bw BS, divide 1000 to changes to KB
                    if v_rw_sufix == 'B':
                        v_value_number = float(v_value_number)/1000.0
                    #if shows as bw MS, divide 1000 to changes to KB
                    if v_rw_sufix == 'MB':
                        v_value_number = float(v_value_number)*1000.0
                    v_rw_sufix = 'KB'
                    v_rw_sufix = ' '+v_rw_sufix +'/s'

                v_sum= v_sum+ float(v_value_number)
                count=count+1
                #avg_read_bw = sum_read_bw/count
                if v_sum >0 :
                    v_average = v_sum/count
                    v_average = str(v_average)
                    #v_average = v_average + v_rw_sufix
                    key="avg_"+ rw_type +"_"+ evaluate_type
                    v_dic= {key: v_average}
        return v_dic


    def get_full_dic(self,dir_input, suffix='.csv'):
        """
        Description:
            Get on full dic to all the files, include many round result, key is full file name e.g. gen1_IDE_fs_randrw_4k_1_hometmp_0.csv,
            dic value is still dictionary about bw, iops by looping all the files.
        Input Parameter:
            dir_input: the dir include all the original test result files.
        Return Value:
            One dic to include all the result parsed from single file.
        """

        full_dic={}
        for fd in os.listdir(dir_input):
            if fd.endswith(suffix):
                signle_path= dir_input + os.sep+ fd
                single_dic=self.get_single_dic(signle_path)
                full_dic[fd]=single_dic
        return full_dic

    def get_average_dic(self,full_dic):
        """
        Description:
            get average value of bw, iops for different running rounds
        Input Parameter:
            full_dic: One dic includes all the files result, including the different running rounds
        Return Value:
            avg_dic: One dic to include all the results, and merge serveral rounds' value to one average dic,
        e.g original key, gen1_SCSI_fs_randrw_4k_1_mnttmp_0.csv, gen1_SCSI_fs_randrw_4k_1_mnttmp_1.csv
        after merge, the average key is gen1_SCSI_fs_randrw_4k_1_mnttmp.
        """

        file_uniq_list=[]
        for item_key in full_dic:
            file_name_key=item_key.rsplit("_",1)[0]
            file_name_round=item_key.rsplit("_",1)[1]
            if file_name_key not in file_uniq_list:
                file_uniq_list.append(file_name_key)

        avg_dict={}

        for file_uniq_item in file_uniq_list:

            if file_uniq_item.find('read')!=-1:
                dic_a = self.calculate_average(file_uniq_item,full_dic, 'read', 'bw')
                dic_b = self.calculate_average(file_uniq_item,full_dic, 'read', 'iops')
                avg_dict[file_uniq_item]=[dic_a,dic_b]

            if file_uniq_item.find('write')!=-1:
                dic_a =  self.calculate_average(file_uniq_item,full_dic, 'write', 'bw')
                dic_b =  self.calculate_average(file_uniq_item,full_dic, 'write', 'iops')
                avg_dict[file_uniq_item]=[dic_a,dic_b]

            if file_uniq_item.find('rw')!=-1:

                dic_a = self.calculate_average(file_uniq_item,full_dic, 'rw_write', 'bw')
                dic_b=  self.calculate_average(file_uniq_item,full_dic, 'rw_write', 'iops')
                dic_c=  self.calculate_average(file_uniq_item,full_dic, 'rw_read', 'bw')
                dic_d=  self.calculate_average(file_uniq_item,full_dic, 'rw_read', 'iops')
                avg_dict[file_uniq_item]=[dic_a,dic_b,dic_c,dic_d]
        return avg_dict

    def write_dic_to_report(self,fpath,final_avg_dic):
        """
        Description:
            write average dic to the report.txt
        Input Parameter:
            fpath: report.txt full path
            final_avg_dic: One dic includes all the results, and merge serveral rounds' value to one average dic
        Return Value:
            None
        """

        fp = open(fpath, "w")
        fp.write("\n %-50s %-50s %-50s\n" %('filename','avg_bw (KB/s)','avg_iops'))

        for key_name in sorted(final_avg_dic.keys()):

            str_bw = ''
            str_iops=''
            str_bw_read =''
            str_bw_write =''
            str_iops_read =''
            str_iops_write =''

            evaluate_list =  final_avg_dic[key_name]
            key_name=key_name.rsplit("_",1)[0] # remove the /mnt/tmp /dev/sdb in the file name
            # for read category

            if key_name.find('read')!=-1:
                for item in evaluate_list:
                    if item.keys() == ['avg_read_bw']:
                        str_bw = item['avg_read_bw']
                    elif item.keys() == ['avg_read_iops']:
                        str_iops = item['avg_read_iops']

                fp.write("\n %-50s %-50s %-50s" %(key_name,str_bw,str_iops))
            if key_name.find('write')!=-1:
                for item in evaluate_list:
                    if item.keys() == ['avg_write_bw']:
                        str_bw = item['avg_write_bw']
                    elif item.keys() == ['avg_write_iops']:
                        str_iops = item['avg_write_iops']

                fp.write("\n %-50s %-50s %-50s" %(key_name,str_bw,str_iops))
            if key_name.find('rw')!=-1:
                for item in evaluate_list:
                    if item.keys() == ['avg_rw_read_bw']:
                        str_bw_read = item['avg_rw_read_bw']
                    elif item.keys() == ['avg_rw_read_iops']:
                        str_iops_read = item['avg_rw_read_iops']

                    if item.keys() == ['avg_rw_write_bw']:
                        str_bw_write = item['avg_rw_write_bw']
                    elif item.keys() == ['avg_rw_write_iops']:
                        str_iops_write = item['avg_rw_write_iops']
                fp.write("\n %-50s %-50s %-50s" %(key_name+'_read',str_bw_read,str_iops_read))
                fp.write("\n %-50s %-50s %-50s" %(key_name+'_write',str_bw_write,str_iops_write))

        fp.close()


    def rewrite_to_seprate_reports(self,fpath):
        """
        Description:
            rewrite test report file report.txt to seprate files and sorted by easier read styple, e.g. gen1, IDE, read, 4k firstly,
            seprate reports file under same folder of fpath
        Input Parameter:
            fpath: report.txt full path
        Return Value:
            None
        """

        current_time = strftime("%Y%m%d%H%M", gmtime())
        target_lines = []

        with open(fpath) as fp:
            for line in fp:
                line=line.strip()
                target_lines.append(line)

        #get disk types from test report.
        #e.g. disk_types=['gen1_IDE','gen1_SCSI','gen2_IDE','gen2_SCSI', 'gen1_FC','gen2_FC','gen1_SSD','gen2_SSD']
        disk_types =[]
        for line in target_lines:
            # ignore the first line about table title
            if line.find('gen')==-1:
                continue
            # disk_type: 'gen1_IDE'
            disk_type =line.split('_')[0]+'_'+line.split('_')[1]

            if disk_type not in disk_types:
                disk_types.append(disk_type)

        output_dir = os.path.dirname(fpath)
        for disk_type in disk_types:
            seprate_report_name = output_dir+ os.sep+ disk_type +"_"+current_time
            fsp = open(seprate_report_name, "w")
            fsp.write("\n%20s %20s %20s %15s %20s %15s %15s\n" %('fs_type','read_write','block_size','io-depth','sub_read_write','avg_bw(KB/s)','avg_iops'))

            for line in target_lines:
                        if line.find(disk_type)!= -1:
                                # remove disk_type, e.g. remove gen1_IDE
                                line=line.replace(disk_type,'')
                                result_items=re.split('\s+', line)

                                avg_bw = result_items[1].strip()
                                avg_iops = result_items[2].strip()

                                name_infos= result_items[0].strip().split('_')
                                raw_str =''
                                for name_info in name_infos:
                                    raw_str= raw_str + '{:18}'.format(name_info)
                                if line.find('randrw')== -1:
                                    raw_str= raw_str + '{:18}'.format(' - ')
                                raw_str =raw_str + '{:20}'.format(avg_bw)+'{:20}'.format(avg_iops)
                                fsp.write(raw_str)
                                fsp.write('\n')

            fsp.close()
            # resort the seprate report based to make more easier to read
            self.resort_seprate_report(seprate_report_name)
    # print to different report based on gen1_SCSI_timestamp, gen1_IDE_timestamp
    def resort_seprate_report(self,fpath):
        """
        Description:
            resort test seprate report file based on disk type  for more easier read styple, e.g. gen1, IDE, read, 4k firstly, output
            gen1_SCSI_timestamp_sort file
        Input Parameter:
            fpath: seprate report file, e.g. gen1_SCSI_timestamp
        Return Value:
            None
        """
        target_lines=[]

        #reread the report as list
        with open(fpath) as fp:
            for line in fp:
                line=line.strip()
                target_lines.append(line)

        print target_lines

        fp = open(fpath+"_sorted", "w")

        for line in target_lines:
            # write down the first line
            if line.find('KB/s')!=-1:
                fp.write(line)
                fp.write('\n')
        #the first sort level :fs, raw, second level: read, write, randrw, third level sort: 4k,16k,64k..
        sort_list=['fs\s+read','fs\s+write','fs\s+randrw','raw\s+read','raw\s+write','raw\s+randrw']
        sort_list2=['\s+4k','\s+16k','\s+64k','\s+128k','\s+256k']
        for sort_item in sort_list:
            for sort_item2 in sort_list2:
                for line in target_lines:
                    model =re.compile(sort_item + sort_item2)
                    if model.search(line)!=None:
                        fp.write(line)
                        fp.write('\n')
        fp.close()

    # main funciton to parse original result file to final report
    def parse_result_to_report(self):
        """
        Description:
            Main function to parse result files to final report.
        Input Parameter:
            None
        Return Value:
            None
        """
        full_dic = self.get_full_dic(self.dir_input)
        print "full dic for all the files:\n",full_dic
        final_avg_dic = self.get_average_dic(full_dic)

        print " final_avg_dic", final_avg_dic
        fpath = self.dir_output+ os.sep+'report.txt'

        if not os.path.exists(self.dir_output):
            os.mkdir(self.dir_output)
        if os.path.exists(fpath):
            os.remove(fpath)
        # get the report.txt based on test result files e.g ./csv_report/report.txt"
        self.write_dic_to_report(fpath,final_avg_dic)
        # rewrite to seprate report based on VM generation and disk type ./csv_report/gen1_IDE_201610100658.txt
        self.rewrite_to_seprate_reports(fpath)
        # change the output fold permission
        cmd ="chmod 777 -R "+ self.dir_output
        os.system(cmd)



if __name__ == '__main__':

    dir_input=r"/home/xuemin/Automation/csv_result"
    dir_output= r"/home/xuemin/Automation/csv_report"
    make_report = MakeTestReport(dir_input, dir_output)

    make_report.parse_result_to_report()


    sys.exit(0)
