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
        self.df_report.insert(len(self.df_report.columns), 'BASE-STD-BW', 0)
        self.df_report.insert(len(self.df_report.columns), 'TEST-AVG-BW', 0)
        self.df_report.insert(len(self.df_report.columns), 'TEST-STD-BW', 0)
        self.df_report.insert(len(self.df_report.columns), '%DIFF-BW', 0)
        self.df_report.insert(len(self.df_report.columns), 'SIGNI-BW', 0)

        self.df_report.insert(len(self.df_report.columns), 'BASE-AVG-IOPS', 0)
        self.df_report.insert(len(self.df_report.columns), 'BASE-STD-IOPS', 0)
        self.df_report.insert(len(self.df_report.columns), 'TEST-AVG-IOPS', 0)
        self.df_report.insert(len(self.df_report.columns), 'TEST-STD-IOPS', 0)
        self.df_report.insert(len(self.df_report.columns), '%DIFF-IOPS', 0)
        self.df_report.insert(len(self.df_report.columns), 'SIGNI-IOPS', 0)

        self.df_report.insert(len(self.df_report.columns), 'BASE-AVG-LAT', 0)
        self.df_report.insert(len(self.df_report.columns), 'BASE-STD-LAT', 0)
        self.df_report.insert(len(self.df_report.columns), 'TEST-AVG-LAT', 0)
        self.df_report.insert(len(self.df_report.columns), 'TEST-STD-LAT', 0)
        self.df_report.insert(len(self.df_report.columns), '%DIFF-LAT', 0)
        self.df_report.insert(len(self.df_report.columns), 'SIGNI-LAT', 0)

        self.df_report.insert(len(self.df_report.columns), 'BASE-AVG-Util', 0)
        self.df_report.insert(len(self.df_report.columns), 'BASE-STD-Util', 0)
        self.df_report.insert(len(self.df_report.columns), 'TEST-AVG-Util', 0)
        self.df_report.insert(len(self.df_report.columns), 'TEST-STD-Util', 0)
        self.df_report.insert(len(self.df_report.columns), '%DIFF-Util', 0)
        self.df_report.insert(len(self.df_report.columns), 'SIGNI-Util', 0)

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
            print df_base
            print df_test

            series['BASE-AVG-BW'] = df_base['BW(MiB/s)'].mean()
            series['BASE-STD-BW'] = df_base['BW(MiB/s)'].std()
            series['TEST-AVG-BW'] = df_test['BW(MiB/s)'].mean()
            series['TEST-STD-BW'] = df_test['BW(MiB/s)'].std()
            series['%DIFF-BW'] = (series['TEST-AVG-BW'] - series['BASE-AVG-BW']
                                  ) / series['BASE-AVG-BW'] * 100
            series['SIGNI-BW'] = 0.99

            print series

            self.df_report.iloc[index] = series

            #print self.df_report

            break


if __name__ == '__main__':

    fbr = FioBenchmarkReporter()
    fbr.test()

    exit(0)
