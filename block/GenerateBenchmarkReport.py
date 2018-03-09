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
        self.df_s1 = pd.read_csv(
            "./fio_report/RHEL74_report.csv"
        )
        print self.df_s1

        self.df_s2 = pd.read_csv(
            "./fio_report/RHEL75_report.csv"
        )
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

        print self.df_report

        for (idx, se) in self.df_report.iterrows():
            df_s1 = self.df_s1[(self.df_s1['Backend'] == se['Backend'])
                               & (self.df_s1['Driver'] == se['Driver'])
                               & (self.df_s1['Format'] == se['Format'])
                               & (self.df_s1['RW'] == se['RW'])
                               & (self.df_s1['BS'] == se['BS'])
                               & (self.df_s1['IODepth'] == se['IODepth'])
                               & (self.df_s1['Numjobs'] == se['Numjobs'])]

            df_s2 = self.df_s2[(self.df_s2['Backend'] == se['Backend'])
                               & (self.df_s2['Driver'] == se['Driver'])
                               & (self.df_s2['Format'] == se['Format'])
                               & (self.df_s2['RW'] == se['RW'])
                               & (self.df_s2['BS'] == se['BS'])
                               & (self.df_s2['IODepth'] == se['IODepth'])
                               & (self.df_s2['Numjobs'] == se['Numjobs'])]
            print df_s1
            print df_s2
            break



if __name__ == '__main__':

    fbr = FioBenchmarkReporter()
    fbr.test()

    exit(0)
