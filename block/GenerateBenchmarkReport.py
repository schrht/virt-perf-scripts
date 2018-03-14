#!/usr/bin/env python

# Generate Benchmark Report

#import json
#import re
#import os
#import prettytable
import pandas as pd
from scipy.stats import ttest_rel
from scipy.stats import ttest_ind

class FioBenchmarkReporter():
    '''
    Read data from csv files, compare the performance KPI data for benchmarking.
    '''

    # The DataFrame for set 1 and set 2, which are powered by pandas.
    df_base = df_test = None

    # The DataFrame for target data which used for reporting.
    df_report = None

    def _get_significance(self, array1, array2, paired=False):
        '''
        This function used to get the significance of t-test.
        '''

        if paired:
            (statistic, pvalue) = ttest_rel(array1, array2)
        else:
            (statistic, pvalue) = ttest_ind(array1, array2)

        significance = 1 - pvalue

        return significance

    def _get_conclusion(self,
                        base_pct_dev,
                        test_pct_dev,
                        pct_diff,
                        significance,
                        higher_is_better=True):
        '''
        This function used to get the conclusion.
        '''

        MAX_PCT_DEV = 10
        REGRESSION_THRESHOLD = 5
        CONFIDENCE_THRESHOLD = 0.95

        if base_pct_dev > MAX_PCT_DEV or test_pct_dev > MAX_PCT_DEV:
            return 'Variance Too Large'

        if pct_diff == 0:
            return 'No Difference'

        if significance < CONFIDENCE_THRESHOLD:
            return 'No Significance'

        if (higher_is_better and pct_diff > 0) or (not higher_is_better
                                                   and pct_diff < 0):
            if abs(pct_diff) >= REGRESSION_THRESHOLD:
                return 'Significantly Improved'
            else:
                return 'Slightly Improved'
        else:
            if abs(pct_diff) >= REGRESSION_THRESHOLD:
                return 'Significantly Regression'
            else:
                return 'Slightly Regression'

    def _add_columns_into_report_dataframe(self, label):
        self.df_report.insert(
            len(self.df_report.columns), label + '-BASE-AVG', 0)
        self.df_report.insert(
            len(self.df_report.columns), label + '-BASE-%SD', 0)
        self.df_report.insert(
            len(self.df_report.columns), label + '-TEST-AVG', 0)
        self.df_report.insert(
            len(self.df_report.columns), label + '-TEST-%SD', 0)
        self.df_report.insert(len(self.df_report.columns), label + '-%DIFF', 0)
        self.df_report.insert(len(self.df_report.columns), label + '-SIGN', 0)
        self.df_report.insert(
            len(self.df_report.columns), label + '-CONCLUSION', 0)
        return 0

    def _calculate_and_fill_report_dataframe(self, series, df_base, df_test,
                                             label, source_label,
                                             higher_is_better):
        series[label + '-BASE-AVG'] = df_base[source_label].mean()
        series[label + '-BASE-%SD'] = df_base[source_label].std(
            ddof=1) / series[label + '-BASE-AVG'] * 100
        series[label + '-TEST-AVG'] = df_test[source_label].mean()
        series[label + '-TEST-%SD'] = df_test[source_label].std(
            ddof=1) / series[label + '-TEST-AVG'] * 100
        series[label + '-%DIFF'] = (
            series[label + '-TEST-AVG'] - series[label + '-BASE-AVG']
        ) / series[label + '-BASE-AVG'] * 100
        series[label + '-SIGN'] = self._get_significance(
            df_base[source_label], df_test[source_label])
        series[label + '-CONCLUSION'] = self._get_conclusion(
            series[label + '-BASE-%SD'], series[label + '-TEST-%SD'],
            series[label + '-%DIFF'], series[label
                                             + '-SIGN'], higher_is_better)

        return 0

    def load_samples(self, params={}):
        # Parse required params
        if 'base_csv' not in params:
            print 'Missing required params: params[base_csv]'
            return 1

        if 'test_csv' not in params:
            print 'Missing required params: params[test_csv]'
            return 1

        try:
            # Load base samples from CSV file
            print 'Reading base samples from csv file "%s"...' % params[
                'base_csv']
            self.df_base = pd.read_csv(params['base_csv'])

            # Load test samples from CSV file
            print 'Reading test samples from csv file "%s"...' % params[
                'test_csv']
            self.df_test = pd.read_csv(params['test_csv'])

        except Exception, err:
            print 'Error while reading from csv file: %s' % err
            return 1

        return 0

    def _create_report_dataframe(self):
        # Create the DataFrame for reporting
        self.df_report = self.df_test[[
            'Backend', 'Driver', 'Format', 'RW', 'BS', 'IODepth', 'Numjobs'
        ]].drop_duplicates()

        # Sort the DataFrame and reset the index
        self.df_report = self.df_report.sort_values(by=[
            'Backend', 'Driver', 'Format', 'RW', 'BS', 'IODepth', 'Numjobs'
        ])
        self.df_report = self.df_report.reset_index().drop(columns=['index'])

        # Add new columns to the DataFrame
        # [Notes] The units: BW(MiB/s) / IOPS / LAT(ms) / Util(%)
        self._add_columns_into_report_dataframe('BW')
        self._add_columns_into_report_dataframe('IOPS')
        self._add_columns_into_report_dataframe('LAT')
        self._add_columns_into_report_dataframe('Util')

        return 0

    def _complete_report_dataframe(self):
        for (index, series) in self.df_report.iterrows():

            if index > 5:
                continue

            my_sub_base = self.df_base[
                (self.df_base['Backend'] == series['Backend'])
                & (self.df_base['Driver'] == series['Driver'])
                & (self.df_base['Format'] == series['Format'])
                & (self.df_base['RW'] == series['RW'])
                & (self.df_base['BS'] == series['BS'])
                & (self.df_base['IODepth'] == series['IODepth'])
                & (self.df_base['Numjobs'] == series['Numjobs'])]

            my_sub_test = self.df_test[
                (self.df_test['Backend'] == series['Backend'])
                & (self.df_test['Driver'] == series['Driver'])
                & (self.df_test['Format'] == series['Format'])
                & (self.df_test['RW'] == series['RW'])
                & (self.df_test['BS'] == series['BS'])
                & (self.df_test['IODepth'] == series['IODepth'])
                & (self.df_test['Numjobs'] == series['Numjobs'])]

            # Calculate statistic index
            self._calculate_and_fill_report_series(
                series, my_sub_base, my_sub_test, 'BW', 'BW(MiB/s)', True)
            self._calculate_and_fill_report_series(
                series, my_sub_base, my_sub_test, 'IOPS', 'IOPS', True)
            self._calculate_and_fill_report_series(
                series, my_sub_base, my_sub_test, 'LAT', 'LAT(ms)', False)
            self._calculate_and_fill_report_series(
                series, my_sub_base, my_sub_test, 'Util', 'Util(%)', True)

            # Show current series
            print series

            # Save the changes
            self.df_report.iloc[index] = series

        return 0

    def generate_report(self, params={}):

        # Create report DataFrame
        self._create_report_dataframe()

        # Complete report DataFrame
        self._complete_report_dataframe()

        # Format report DataFrame
        self._format_report_dataframe()

        return 0

    def _format_report_dataframe(self):
        self.df_report = self.df_report.round(4)
        self.df_report = self.df_report.fillna('N/A')
        return 0

    def dump_to_csv(self, csv_file):
        # Write the content to a csv file
        try:
            print 'Dumping data into csv file "%s"...' % csv_file
            content = self.df_report.to_csv()
            with open(csv_file, 'w') as f:
                f.write(content)
            print 'Finished!'

        except Exception, err:
            print 'Error while dumping to csv file: %s' % err
            return 1


if __name__ == '__main__':

    fbr = FioBenchmarkReporter()

    fbr.load_samples({
        'base_csv': './fio_report/RHEL74_report.csv',
        'test_csv': './fio_report/RHEL75_report.csv'
    })

    fbr.generate_report()

    #fbr.load_samples()
    print fbr.df_report

    fbr.report_to_csv('./fio_report/benchmark_report.csv')

    exit(0)
