#!/usr/bin/env python

# Generate Benchmark Report

#import json
#import re
#import os
#import prettytable
import pandas as pd


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
        from scipy.stats import ttest_rel
        from scipy.stats import ttest_ind

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
        self.df_report.insert(len(self.df_report.columns), label + '-SIGNI', 0)
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
        series[label + '-SIGNI'] = self._get_significance(
            df_base[source_label], df_test[source_label])
        series[label + '-CONCLUSION'] = self._get_conclusion(
            series[label + '-BASE-%SD'], series[label + '-TEST-%SD'],
            series[label + '-%DIFF'], series[label
                                             + '-SIGNI'], higher_is_better)

        return 0

    def test(self, params={}):

        # Read from CSV files
        self.df_base = pd.read_csv("./fio_report/RHEL74_report.csv")
        print self.df_base

        self.df_test = pd.read_csv("./fio_report/RHEL75_report.csv")
        print self.df_test

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

        #print self.df_report

        for (index, series) in self.df_report.iterrows():
            df_base = self.df_base[
                (self.df_base['Backend'] == series['Backend'])
                & (self.df_base['Driver'] == series['Driver'])
                & (self.df_base['Format'] == series['Format'])
                & (self.df_base['RW'] == series['RW'])
                & (self.df_base['BS'] == series['BS'])
                & (self.df_base['IODepth'] == series['IODepth'])
                & (self.df_base['Numjobs'] == series['Numjobs'])]

            df_test = self.df_test[
                (self.df_test['Backend'] == series['Backend'])
                & (self.df_test['Driver'] == series['Driver'])
                & (self.df_test['Format'] == series['Format'])
                & (self.df_test['RW'] == series['RW'])
                & (self.df_test['BS'] == series['BS'])
                & (self.df_test['IODepth'] == series['IODepth'])
                & (self.df_test['Numjobs'] == series['Numjobs'])]

            # Calculate statistic index
            self._calculate_and_fill_report_dataframe(series, df_base, df_test,
                                                      'BW', 'BW(MiB/s)', True)
            self._calculate_and_fill_report_dataframe(series, df_base, df_test,
                                                      'IOPS', 'IOPS', True)
            self._calculate_and_fill_report_dataframe(series, df_base, df_test,
                                                      'LAT', 'LAT(ms)', False)
            self._calculate_and_fill_report_dataframe(series, df_base, df_test,
                                                      'Util', 'Util(%)', True)

            print series

            self.df_report.iloc[index] = series

        print self.df_report

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
    fbr.test()
    fbr.dump_to_csv('./fio_report/benchmark_report.csv')

    exit(0)
