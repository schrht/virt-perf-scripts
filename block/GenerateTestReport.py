#!/usr/bin/env python

# What to do next?
# - make a cpu of office and enjoy it.
# - make fio generates the results in normal and json+.
# - get the json parts from the output files.
# - analyse it and keep KPIs in python dict.
# - load the dicts into PrettyTalbe.
# - show it or export as csv files.

# Interface between StoragePerformanceTest.py
# StoragePerformanceTest.py should do:
# 1. the fio outputs should be at least in json+ format
#    the "fio --group_reporting" must be used
# 2. save the fio outputs into *.fiolog
# 3. put all *.fiolog files into ./fio_result/
# 4. empty ./fio_report/ folder
# 5. pass the additional information by "fio --description"

import json
import re
import os


class FioPerformanceKPIs():
    '''
    Get, deal with and covert the performance KPI data from FIO tools.
    '''

    # The list of raw data, the item is loaded from fio output file.
    # Each item is a full data source (raw data) and it is in json format.
    raw_data_list = []

    # The list of performance KPIs, which are extracted from the raw data.
    # Each item represents a single fio test and it is in python dict format.
    perf_kpi_list = []

    def file_to_raw(self, params={}):
        '''
        This function open a specified fio output file and read the first json block which is expected to be the fio outputs in json/json+ format.
        And convert the json block into the json format in python. With the help of function byteify, it converts the unicode string to bytes.
        '''

        def byteify(inputs):
            '''Convert unicode to utf-8 string.'''
            if isinstance(inputs, dict):
                return {
                    byteify(key): byteify(value)
                    for key, value in inputs.iteritems()
                }
            elif isinstance(inputs, list):
                return [byteify(element) for element in inputs]
            elif isinstance(inputs, unicode):
                return inputs.encode('utf-8')
            else:
                return inputs

        # Parse required params
        if 'data_file' not in params:
            print 'Missing required params: params[data_file]'
            return (1, None)

        # Generate json file with the first json block in data file
        try:
            with open(params['data_file'], 'r') as f:
                file_content = f.readlines()

            # Locate the first json block
            begin = end = num = 0
            while num < len(file_content):
                if re.search(r'^{', file_content[num]):
                    begin = num
                    break
                num += 1
            while num < len(file_content):
                if re.search(r'^}', file_content[num]):
                    end = num
                    break
                num += 1

            # Write the json block into file
            if begin < end:
                with open(params['data_file'] + '.json', 'w') as f:
                    f.writelines(file_content[begin:end + 1])
            else:
                print 'Cannot found validate json block in file: %s' % params[
                    'data_file']
                return (1, None)

        except Exception, err:
            print 'Error while handling data file: %s' % err
            return (1, None)

        try:
            with open(params['data_file'] + '.json', 'r') as json_file:
                json_data = json.load(json_file)
                raw_data = byteify(json_data)
        except Exception, err:
            print 'Error while handling data file: %s' % err
            return (1, None)

        return (0, raw_data)

    def load_raw_data(self, params={}):
        '''
        This function loads json raw data from a sort of fio output files and save them into self.raw_data_list.
        '''

        # Parse required params
        if 'result_path' not in params:
            print 'Missing required params: params[result_path]'
            return 1

        # load raw data from files
        for basename in os.listdir(params['result_path']):
            filename = params['result_path'] + '/' + basename

            if filename.endswith('.fiolog') and os.path.isfile(filename):
                (result, raw_data) = self.file_to_raw({'data_file': filename})
                if result == 0:
                    self.raw_data_list.append(raw_data)

        return 0

    def raw_to_kpi(self, params={}):
        '''
        This function extracts performance KPIs from a tuple of raw data.
        '''

        # Parse required params
        if 'raw_data' not in params:
            print 'Missing required params: params[raw_data]'
            return (1, None)

        # Extract the performance KPIs
        perf_kpi = {}
        raw_data = params['raw_data']

        try:
            perf_kpi['rw'] = raw_data['jobs'][0]['job options']['rw']
            perf_kpi['bs'] = raw_data['jobs'][0]['job options']['bs']
            perf_kpi['iodepth'] = raw_data['jobs'][0]['job options']['iodepth']
            perf_kpi['numjobs'] = raw_data['jobs'][0]['job options']['numjobs']

            perf_kpi['util'] = raw_data['disk_util'][0]['aggr_util']

            # The unit for "bw" is "KiB/s", for "lat" is "ns".
            perf_kpi['r-bw'] = raw_data['jobs'][0]['read']['bw']
            perf_kpi['r-iops'] = raw_data['jobs'][0]['read']['iops']
            perf_kpi['r-lat'] = raw_data['jobs'][0]['read']['lat_ns']['mean']
            perf_kpi['w-bw'] = raw_data['jobs'][0]['write']['bw']
            perf_kpi['w-iops'] = raw_data['jobs'][0]['write']['iops']
            perf_kpi['w-lat'] = raw_data['jobs'][0]['write']['lat_ns']['mean']

            perf_kpi['bw'] = perf_kpi['r-bw'] + perf_kpi['w-bw']
            perf_kpi['iops'] = perf_kpi['r-iops'] + perf_kpi['w-iops']
            perf_kpi['lat'] = perf_kpi['r-lat'] + perf_kpi['w-lat']

        except Exception, err:
            print 'Error while extracting performance KPIs: %s' % err
            return (1, None)

        return (0, perf_kpi)

    def extracts_perf_kpis(self, params={}):
        '''
        This function extracts performance KPIs from self.raw_data_list and save the tuples into self.perf_kpi_list.
        '''

        # Extracts performance KPIs
        for raw_data in self.raw_data_list:
            (result, perf_kpi) = perf_kpis.raw_to_kpi({'raw_data': raw_data})
            if result == 0:
                self.perf_kpi_list.append(perf_kpi)

        return 0


if __name__ == '__main__':

    perf_kpis = FioPerformanceKPIs()
    perf_kpis.load_raw_data({'result_path': './block/samples'})
    perf_kpis.extracts_perf_kpis()

    print 'perf_kpis.perf_kpi_list:', perf_kpis.perf_kpi_list

    exit(0)
