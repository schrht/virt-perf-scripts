#!/usr/bin/env python
"""Generate FIO Benchmark Report."""

import click
import pandas as pd
from scipy.stats import ttest_rel
from scipy.stats import ttest_ind


class FioBenchmarkReporter():
    """FIO Benchmark Reporter.

    This class used to generate the fio benchmark report. As basic functions:
    1. It loads base samples and test samples from csv files;
    2. It calculates the mean, std dev and significance;
    3. It generates the report and dump to a csv file;

    Attributes:
        df_base: a DataFrame to store base samples.
        df_test: a DataFrame to store test samples.
        df_report: a DataFrame to store the benchmark report.

    """

    # The DataFrame to store base samples and test samples
    df_base = df_test = None

    # The DataFrame to store the benchmark report
    df_report = None

    def _get_significance(self, array1, array2, paired):
        """Get the significance of t-test.

        Args:
            array1: array like, the samples to do t-test;
            array2: array like, the samples to do t-test;
            paired: flag, paired or unpaired t-test;

        Returns:
            The Significance which value between 0 and 1. When the calculation
            fails, it will return 'nan' instead.

        """
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
        """Get the conclusion of the specified KPI.

        To reach the conclusion, we need to consider the following conditions:
        1. The base %SD and test %SD should below MAX_PCT_DEV;
        2. Whether the %DIFF of the KPI beyonds REGRESSION_THRESHOLD;
        3. Whether the Significance beyonds CONFIDENCE_THRESHOLD.

        Args:
            base_pct_dev: float, the base %SD;
            test_pct_dev: float, the test %SD;
            pct_diff: float, the %DIFF of the KPI;
            significance: float, 0 <= x <= 1, the Significance;
            higher_is_better: flag, used to adjust improvment or regression.

        Returns:
            'Variance Too Large': the %SD beyonds MAX_PCT_DEV;
            'No Difference': the %DIFF is zero;
            'No Significance': the Significance less than CONFIDENCE_THRESHOLD;
            'Significantly Improvement' and 'Significantly Regression':
                the Significance beyonds CONFIDENCE_THRESHOLD and %DIFF
                beyonds REGRESSION_THRESHOLD;
            'Slightly Improvement' and 'Slightly Regression':
                the Significance beyonds CONFIDENCE_THRESHOLD but %DIFF
                is below REGRESSION_THRESHOLD;

        """
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
                return 'Significantly Improvement'
            else:
                return 'Slightly Improvement'
        else:
            if abs(pct_diff) >= REGRESSION_THRESHOLD:
                return 'Significantly Regression'
            else:
                return 'Slightly Regression'

    def _add_columns_into_report_dataframe(self, label):
        """Add a serial of columns into report DataFrame."""
        # Add a serial of columns for the specified label
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

        return None

    def _calculate_and_fill_report_series(self, series, df_base, df_test,
                                          label, source_label,
                                          higher_is_better):
        """Calculate the statistics and fill the Series for specified label."""
        # Calculate and fill the average and %SD of the base and test samples
        series[label + '-BASE-AVG'] = df_base[source_label].mean()
        series[label + '-BASE-%SD'] = df_base[source_label].std(
            ddof=1) / series[label + '-BASE-AVG'] * 100
        series[label + '-TEST-AVG'] = df_test[source_label].mean()
        series[label + '-TEST-%SD'] = df_test[source_label].std(
            ddof=1) / series[label + '-TEST-AVG'] * 100

        # Calculate and fill the %DIFF of the test samples againest base
        series[label + '-%DIFF'] = (
            series[label + '-TEST-AVG'] - series[label + '-BASE-AVG']
        ) / series[label + '-BASE-AVG'] * 100

        # Calculate and fill the Significance
        series[label + '-SIGN'] = self._get_significance(
            df_base[source_label], df_test[source_label], False)

        # Calculate and fill the Conclusion
        series[label + '-CONCLUSION'] = self._get_conclusion(
            series[label + '-BASE-%SD'], series[label + '-TEST-%SD'],
            series[label + '-%DIFF'], series[label
                                             + '-SIGN'], higher_is_better)

        return None

    def load_samples(self, params={}):
        """Load the base and test samples.

        Load the base and test samples from csv files specified.

        Args:
            params: dict
                base_csv: string, the csv file for base samples;
                test_csv: string, the csv file for test samples;

        Returns:
            0: Passed
            1: Failed

        Updates:
            self.df_base: store the base samples;
            self.df_test: store the test samples;

        Raises:
            1. Error while reading from csv file

        """
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
        """Create the report DataFrame."""
        # Create the report DataFrame according to self.df_test
        self.df_report = self.df_test[[
            'Backend', 'Driver', 'Format', 'RW', 'BS', 'IODepth', 'Numjobs'
        ]].drop_duplicates()

        # Sort the report DataFrame and reset its index
        self.df_report = self.df_report.sort_values(by=[
            'Backend', 'Driver', 'Format', 'RW', 'BS', 'IODepth', 'Numjobs'
        ])
        self.df_report = self.df_report.reset_index().drop(columns=['index'])

        # Add the new columns to report DataFrame
        # [Note] Units: BW(MiB/s) / IOPS / LAT(ms) / Util(%)
        self._add_columns_into_report_dataframe('BW')
        self._add_columns_into_report_dataframe('IOPS')
        self._add_columns_into_report_dataframe('LAT')
        self._add_columns_into_report_dataframe('Util')

        return None

    def _complete_report_dataframe(self):
        """Complete the report DataFrame."""
        # Deal with every Series in report DataFrame
        for (index, series) in self.df_report.iterrows():

            # Look up the sub DataFrame from the base samples
            my_sub_base = self.df_base[
                (self.df_base['Backend'] == series['Backend'])
                & (self.df_base['Driver'] == series['Driver'])
                & (self.df_base['Format'] == series['Format'])
                & (self.df_base['RW'] == series['RW'])
                & (self.df_base['BS'] == series['BS'])
                & (self.df_base['IODepth'] == series['IODepth'])
                & (self.df_base['Numjobs'] == series['Numjobs'])]

            # Look up the sub DataFrame from the test samples
            my_sub_test = self.df_test[
                (self.df_test['Backend'] == series['Backend'])
                & (self.df_test['Driver'] == series['Driver'])
                & (self.df_test['Format'] == series['Format'])
                & (self.df_test['RW'] == series['RW'])
                & (self.df_test['BS'] == series['BS'])
                & (self.df_test['IODepth'] == series['IODepth'])
                & (self.df_test['Numjobs'] == series['Numjobs'])]

            # Calculate the statistics
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

            # Save current series
            self.df_report.iloc[index] = series

        return None

    def generate_report(self, params={}):
        """Generate benchmark report.

        This function creates the report DataFrame, completes and formats it.

        As data source, the following DataFrame should be ready to use:
        1. self.df_base: store the base samples;
        2. self.df_test: store the test samples;

        Updates:
            self.df_report: store the benchmark report;

        """
        # Create report DataFrame
        self._create_report_dataframe()

        # Complete report DataFrame
        self._complete_report_dataframe()

        # Format report DataFrame
        self._format_report_dataframe()

        return None

    def _format_report_dataframe(self):
        """Format the report DataFrame."""
        self.df_report = self.df_report.round(4)
        self.df_report = self.df_report.fillna('N/A')
        return None

    def report_to_csv(self, params={}):
        """Dump the report DataFrame to a csv file.

        As data source, the report DataFrame should be ready to use.

        Args:
            params: dict
                report_csv: string, the csv file to dump benchmark report;

        Returns:
            0: Passed
            1: Failed

        Raises:
            1. Error while dumping to csv file

        """
        # Parse required params
        if 'report_csv' not in params:
            print 'Missing required params: params[report_csv]'
            return 1

        # Write the report to the csv file
        try:
            print 'Dumping data into csv file "%s"...' % params['report_csv']
            content = self.df_report.to_csv()
            with open(params['report_csv'], 'w') as f:
                f.write(content)
            print 'Finished!'

        except Exception, err:
            print 'Error while dumping to csv file: %s' % err
            return 1

        return 0


@click.command()
@click.argument('base_csv')
@click.argument('test_csv')
@click.argument('report_csv')
def generate_fio_benchmark_report(base_csv, test_csv, report_csv):
    """Generate FIO benchmark report."""
    fbr = FioBenchmarkReporter()

    ret = fbr.load_samples({'base_csv': base_csv, 'test_csv': test_csv})
    if ret != 0:
        exit(1)

    fbr.generate_report()

    ret = fbr.report_to_csv({'report_csv': report_csv})
    if ret != 0:
        exit(1)

    exit(0)


if __name__ == '__main__':

    generate_fio_benchmark_report()
