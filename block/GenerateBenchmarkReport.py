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

    def test(self, params={}):
        pass

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
        self.df_report.insert(len(self.df_report.columns), 'BASE-AVG-BW', 0)
        self.df_report.insert(len(self.df_report.columns), 'BASE-%SD-BW', 0)
        self.df_report.insert(len(self.df_report.columns), 'TEST-AVG-BW', 0)
        self.df_report.insert(len(self.df_report.columns), 'TEST-%SD-BW', 0)
        self.df_report.insert(len(self.df_report.columns), '%DIFF-BW', 0)
        self.df_report.insert(len(self.df_report.columns), 'SIGNI-BW', 0)
        self.df_report.insert(len(self.df_report.columns), 'CONCLUSION-BW', 0)

        self.df_report.insert(len(self.df_report.columns), 'BASE-AVG-IOPS', 0)
        self.df_report.insert(len(self.df_report.columns), 'BASE-%SD-IOPS', 0)
        self.df_report.insert(len(self.df_report.columns), 'TEST-AVG-IOPS', 0)
        self.df_report.insert(len(self.df_report.columns), 'TEST-%SD-IOPS', 0)
        self.df_report.insert(len(self.df_report.columns), '%DIFF-IOPS', 0)
        self.df_report.insert(len(self.df_report.columns), 'SIGNI-IOPS', 0)
        self.df_report.insert(
            len(self.df_report.columns), 'CONCLUSION-IOPS', 0)

        self.df_report.insert(len(self.df_report.columns), 'BASE-AVG-LAT', 0)
        self.df_report.insert(len(self.df_report.columns), 'BASE-%SD-LAT', 0)
        self.df_report.insert(len(self.df_report.columns), 'TEST-AVG-LAT', 0)
        self.df_report.insert(len(self.df_report.columns), 'TEST-%SD-LAT', 0)
        self.df_report.insert(len(self.df_report.columns), '%DIFF-LAT', 0)
        self.df_report.insert(len(self.df_report.columns), 'SIGNI-LAT', 0)
        self.df_report.insert(len(self.df_report.columns), 'CONCLUSION-LAT', 0)

        self.df_report.insert(len(self.df_report.columns), 'BASE-AVG-Util', 0)
        self.df_report.insert(len(self.df_report.columns), 'BASE-%SD-Util', 0)
        self.df_report.insert(len(self.df_report.columns), 'TEST-AVG-Util', 0)
        self.df_report.insert(len(self.df_report.columns), 'TEST-%SD-Util', 0)
        self.df_report.insert(len(self.df_report.columns), '%DIFF-Util', 0)
        self.df_report.insert(len(self.df_report.columns), 'SIGNI-Util', 0)
        self.df_report.insert(
            len(self.df_report.columns), 'CONCLUSION-Util', 0)

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

            # Caluclate statistic index
            series['BASE-AVG-BW'] = df_base['BW(MiB/s)'].mean()
            series['BASE-%SD-BW'] = df_base['BW(MiB/s)'].std(
                ddof=1) / series['BASE-AVG-BW'] * 100
            series['TEST-AVG-BW'] = df_test['BW(MiB/s)'].mean()
            series['TEST-%SD-BW'] = df_test['BW(MiB/s)'].std(
                ddof=1) / series['TEST-AVG-BW'] * 100
            series['%DIFF-BW'] = (series['TEST-AVG-BW'] - series['BASE-AVG-BW']
                                  ) / series['BASE-AVG-BW'] * 100
            series['SIGNI-BW'] = self._get_significance(
                df_base['BW(MiB/s)'], df_test['BW(MiB/s)'])
            series['CONCLUSION-BW'] = self._get_conclusion(
                series['BASE-%SD-BW'], series['TEST-%SD-BW'],
                series['%DIFF-BW'], series['SIGNI-BW'], True)

            series['BASE-AVG-IOPS'] = df_base['IOPS'].mean()
            series['BASE-%SD-IOPS'] = df_base['IOPS'].std(
                ddof=1) / series['BASE-AVG-IOPS'] * 100
            series['TEST-AVG-IOPS'] = df_test['IOPS'].mean()
            series['TEST-%SD-IOPS'] = df_test['IOPS'].std(
                ddof=1) / series['TEST-AVG-IOPS'] * 100
            series['%DIFF-IOPS'] = (
                series['TEST-AVG-IOPS'] - series['BASE-AVG-IOPS']
            ) / series['BASE-AVG-IOPS'] * 100
            series['SIGNI-IOPS'] = self._get_significance(
                df_base['IOPS'], df_test['IOPS'])
            series['CONCLUSION-IOPS'] = self._get_conclusion(
                series['BASE-%SD-IOPS'], series['TEST-%SD-IOPS'],
                series['%DIFF-IOPS'], series['SIGNI-IOPS'], True)

            series['BASE-AVG-LAT'] = df_base['LAT(ms)'].mean()
            series['BASE-%SD-LAT'] = df_base['LAT(ms)'].std(
                ddof=1) / series['BASE-AVG-LAT'] * 100
            series['TEST-AVG-LAT'] = df_test['LAT(ms)'].mean()
            series['TEST-%SD-LAT'] = df_test['LAT(ms)'].std(
                ddof=1) / series['TEST-AVG-LAT'] * 100
            series['%DIFF-LAT'] = (
                series['TEST-AVG-LAT'] - series['BASE-AVG-LAT']
            ) / series['BASE-AVG-LAT'] * 100
            series['SIGNI-LAT'] = self._get_significance(
                df_base['LAT(ms)'], df_test['LAT(ms)'])
            series['CONCLUSION-LAT'] = self._get_conclusion(
                series['BASE-%SD-LAT'], series['TEST-%SD-LAT'],
                series['%DIFF-LAT'], series['SIGNI-LAT'], False)

            series['BASE-AVG-Util'] = df_base['Util(%)'].mean()
            series['BASE-%SD-Util'] = df_base['Util(%)'].std(
                ddof=1) / series['BASE-AVG-Util'] * 100
            series['TEST-AVG-Util'] = df_test['Util(%)'].mean()
            series['TEST-%SD-Util'] = df_test['Util(%)'].std(
                ddof=1) / series['TEST-AVG-Util'] * 100
            series['%DIFF-Util'] = (
                series['TEST-AVG-Util'] - series['BASE-AVG-Util']
            ) / series['BASE-AVG-Util'] * 100
            series['SIGNI-Util'] = self._get_significance(
                df_base['Util(%)'], df_test['Util(%)'])
            series['CONCLUSION-Util'] = self._get_conclusion(
                series['BASE-%SD-Util'], series['TEST-%SD-Util'],
                series['%DIFF-Util'], series['SIGNI-Util'], True)

            print series

            self.df_report.iloc[index] = series

            #print self.df_report

            break


if __name__ == '__main__':

    fbr = FioBenchmarkReporter()
    fbr.test()

    exit(0)
