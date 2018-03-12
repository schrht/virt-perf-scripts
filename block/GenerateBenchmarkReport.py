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
    df_s1 = df_s2 = None

    # The DataFrame for target data which used for reporting.
    df_report = None

    def test(self, params={}):
        pass

        # Read from CSV files
        self.df_s1 = pd.read_csv("./fio_report/RHEL74_report.csv")
        print self.df_s1

        self.df_s2 = pd.read_csv("./fio_report/RHEL75_report.csv")
        print self.df_s2

        # Create the DataFrame for reporting
        self.df_report = self.df_s2[[
            'Backend', 'Driver', 'Format', 'RW', 'BS', 'IODepth', 'Numjobs'
        ]].drop_duplicates()

        # Sort the DataFrame and reset the index
        self.df_report = self.df_report.sort_values(by=[
            'Backend', 'Driver', 'Format', 'RW', 'BS', 'IODepth', 'Numjobs'
        ])
        self.df_report = self.df_report.reset_index().drop(columns=['index'])

        # Add new columns to the DataFrame
        # [Notes] The units: BW(MiB/s) / IOPS / LAT(ms) / Util(%)
        self.df_report.insert(len(self.df_report.columns), 'S1-AVG-BW', 0)
        self.df_report.insert(len(self.df_report.columns), 'S1-STD-BW', 0)
        self.df_report.insert(len(self.df_report.columns), 'S2-AVG-BW', 0)
        self.df_report.insert(len(self.df_report.columns), 'S2-STD-BW', 0)
        self.df_report.insert(len(self.df_report.columns), '%DIFF-BW', 0)
        self.df_report.insert(len(self.df_report.columns), 'SIGNI-BW', 0)

        self.df_report.insert(len(self.df_report.columns), 'S1-AVG-IOPS', 0)
        self.df_report.insert(len(self.df_report.columns), 'S1-STD-IOPS', 0)
        self.df_report.insert(len(self.df_report.columns), 'S2-AVG-IOPS', 0)
        self.df_report.insert(len(self.df_report.columns), 'S2-STD-IOPS', 0)
        self.df_report.insert(len(self.df_report.columns), '%DIFF-IOPS', 0)
        self.df_report.insert(len(self.df_report.columns), 'SIGNI-IOPS', 0)

        self.df_report.insert(len(self.df_report.columns), 'S1-AVG-LAT', 0)
        self.df_report.insert(len(self.df_report.columns), 'S1-STD-LAT', 0)
        self.df_report.insert(len(self.df_report.columns), 'S2-AVG-LAT', 0)
        self.df_report.insert(len(self.df_report.columns), 'S2-STD-LAT', 0)
        self.df_report.insert(len(self.df_report.columns), '%DIFF-LAT', 0)
        self.df_report.insert(len(self.df_report.columns), 'SIGNI-LAT', 0)

        self.df_report.insert(len(self.df_report.columns), 'S1-AVG-Util', 0)
        self.df_report.insert(len(self.df_report.columns), 'S1-STD-Util', 0)
        self.df_report.insert(len(self.df_report.columns), 'S2-AVG-Util', 0)
        self.df_report.insert(len(self.df_report.columns), 'S2-STD-Util', 0)
        self.df_report.insert(len(self.df_report.columns), '%DIFF-Util', 0)
        self.df_report.insert(len(self.df_report.columns), 'SIGNI-Util', 0)

        #print self.df_report

        for (index, series) in self.df_report.iterrows():
            df_s1 = self.df_s1[(self.df_s1['Backend'] == series['Backend'])
                               & (self.df_s1['Driver'] == series['Driver'])
                               & (self.df_s1['Format'] == series['Format'])
                               & (self.df_s1['RW'] == series['RW'])
                               & (self.df_s1['BS'] == series['BS'])
                               & (self.df_s1['IODepth'] == series['IODepth'])
                               & (self.df_s1['Numjobs'] == series['Numjobs'])]

            df_s2 = self.df_s2[(self.df_s2['Backend'] == series['Backend'])
                               & (self.df_s2['Driver'] == series['Driver'])
                               & (self.df_s2['Format'] == series['Format'])
                               & (self.df_s2['RW'] == series['RW'])
                               & (self.df_s2['BS'] == series['BS'])
                               & (self.df_s2['IODepth'] == series['IODepth'])
                               & (self.df_s2['Numjobs'] == series['Numjobs'])]
            print df_s1
            print df_s2

            series['S1-AVG-BW'] = df_s1['BW(MiB/s)'].mean()
            series['S1-STD-BW'] = df_s1['BW(MiB/s)'].std()
            series['S2-AVG-BW'] = df_s2['BW(MiB/s)'].mean()
            series['S2-STD-BW'] = df_s2['BW(MiB/s)'].std()
            series['%DIFF-BW'] = (series['S2-AVG-BW'] - series['S1-AVG-BW']
                                  ) / series['S1-AVG-BW'] * 100
            series['SIGNI-BW'] = 0.99

            print series

            self.df_report.iloc[index] = series

            #print self.df_report

            break


if __name__ == '__main__':

    fbr = FioBenchmarkReporter()
    fbr.test()

    exit(0)
