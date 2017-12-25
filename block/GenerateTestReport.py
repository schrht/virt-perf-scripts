#!/usr/bin/env python

# What to do next?
# - make a cpu of office and enjoy it.
# - make fio generates the results in normal and json+.
# - get the json parts from the output files.
# - analyse it and keep KPIs in python dict.
# - load the dicts into PrettyTalbe.
# - show it or export as csv files.

import json
import re


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

    def file_to_raw(self, params):
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

    def load_raw_data(self, params):
        '''
        This function loads json raw data from a sort of fio output files and save them into self.raw_data_list.
        '''
        pass

    def raw_to_kpi(self, params):
        '''
        This function extracts performance KPIs from a tuple of raw data.
        '''
        pass

    def extracts_perf_kpis(self, params):
        '''
        This function extracts performance KPIs from self.raw_data_list and save the tuples into self.perf_kpi_list.
        '''
        pass


if __name__ == '__main__':

    perf_kpis = FioPerformanceKPIs()

    params = {
        'data_file':
        '/home/cheshi/workspace/vsc_workspace/virt-perf-scripts/block/samples/randread-test.log.sample'
    }
    (result, raw_data) = perf_kpis.file_to_raw(params)

    if result == 0:
        print raw_data
    else:
        print 'error!'

    exit(0)
