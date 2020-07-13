#!/usr/bin/env python3
"""Generate flent Benchmark Report.

History:
v0.1    2020-05-20  charles.shih  Init version
v0.2    2020-07-06  charles.shih  Basic function completed
v0.3    2020-07-13  charles.shih  Define benchmark report by yaml
v0.4    2020-07-13  charles.shih  Support renaming KEY columns
v0.5    2020-07-13  charles.shih  Support customizing KPI columns
v0.6    2020-07-13  charles.shih  Support appending units to the columns
"""

import os
import click
import yaml
import pandas as pd
import numpy as np
from scipy.stats import ttest_rel
from scipy.stats import ttest_ind


class FlentBenchmarkReporter():
    """Flent Benchmark Reporter.

    This class used to generate the flent benchmark report. As basic functions:
    1. It loads base samples and test samples from csv files;
    2. It calculates the mean, std dev and significance;
    3. It generates the report and dump to a csv file;

    Attributes:
        df_base: a DataFrame to store base samples.
        df_test: a DataFrame to store test samples.
        df_report: a DataFrame to store the benchmark report.
        config: the user config defined in the yaml file.
        keys: the user config data for the KEYs.
        kpis: the user config data for the KPIs.

    """
    def __init__(self):
        """Load config and init benchmark reporter."""
        # Load config
        dirname = os.path.split(os.path.abspath(__file__))[0]
        with open(dirname + os.sep + 'benchmark_reporter_config.yaml',
                  'r') as f:
            content = yaml.safe_load(f)
            self.config = content['FlentBenchmarkReporter']

        self.keys = []
        for key_attr in self.config['keys']:
            key = {}
            if type(key_attr) is dict:
                key['source_label'] = key_attr['source_label']
                key['target_label'] = key_attr['target_label']
                key['target_unit'] = key_attr[
                    'target_unit'] if 'target_unit' in key_attr.keys(
                    ) else None
            else:
                key['source_label'] = key['target_label'] = key_attr
                key['target_unit'] = None
            self.keys.append(key)

        self.kpis = []
        for kpi_attr in self.config['kpis']:
            kpi = {}
            kpi.update(self.config['kpi_defaults'])
            kpi['target_unit'] = None
            kpi.update(kpi_attr)
            self.kpis.append(kpi)

        # The DataFrame to store base samples and test samples
        self.df_base = self.df_test = None

        # The DataFrame to store the benchmark report
        self.df_report = None

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
            print('[ERROR] Missing required params: params[base_csv]')
            return 1

        if 'test_csv' not in params:
            print('[ERROR] Missing required params: params[test_csv]')
            return 1

        try:
            # Load base samples from CSV file
            print('[NOTE] Reading base samples from csv file "%s"...' %
                  params['base_csv'])
            self.df_base = pd.read_csv(params['base_csv'])

            # Load test samples from CSV file
            print('[NOTE] Reading test samples from csv file "%s"...' %
                  params['test_csv'])
            self.df_test = pd.read_csv(params['test_csv'])

        except Exception as err:
            print('[ERROR] Error while reading from csv file: %s' % err)
            return 1

        return 0

    def _create_report_dataframe(self):
        """Create report DataFrame based on test DataFrame."""
        # Get KEYs
        source_keys = [x['source_label'] for x in self.keys]
        target_keys = [x['target_label'] for x in self.keys]

        # Tailer a new DataFrame by KEYs from test DataFrame
        self.df_report = self.df_test[source_keys].drop_duplicates()

        # Rename the columns of the report DataFrame if needed
        for source_key, target_key in zip(source_keys, target_keys):
            if source_key != target_key:
                self.df_report.rename(columns={source_key: target_key},
                                      inplace=True)

        # Sort the report DataFrame and reset its index
        self.df_report = self.df_report.sort_values(by=target_keys)
        self.df_report = self.df_report.reset_index().drop(columns=['index'])

        # Add the expanded KPI columns into report DataFrame
        for kpi in self.kpis:
            expansion = [
                'BASE-AVG', 'BASE-%SD', 'TEST-AVG', 'TEST-%SD', '%DIFF',
                'SIGN', 'CONCLUSION'
            ]
            for suffix in expansion:
                self.df_report.insert(len(self.df_report.columns),
                                      kpi['target_label'] + '-' + suffix, 0)

        return None

    def _get_significance(self, array1, array2, paired=False):
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
                        higher_is_better,
                        max_percent_dev=10,
                        regression_threshold=5,
                        confidence_threshold=0.95):
        """Get the conclusion of the specified KPI.

        To reach the conclusion, we need to consider the following conditions:
        1. The base %SD and test %SD should below MAX_PCT_DEV;
        2. Whether the %DIFF of the KPI beyonds REGRESSION_THRESHOLD;
        3. Whether the Significance beyonds CONFIDENCE_THRESHOLD.

        Args:
            base_pct_dev: float, the base %SD;
            test_pct_dev: float, the test %SD;
            pct_diff: float, the %DIFF of the KPI;
            significance: float [0, 1], the Significance;
            higher_is_better: flag, used to adjust improvment or regression.
            max_percent_dev: int [0, 100], threshold for the maxium %SD.
            regression_threshold: int [0, 100], threshold for the regression.
            confidence_threshold: float [0, 1], threshold for the confidence.

        Returns:
            'Data Invalid':         the input data is invalid;
            'Variance Too Large':   the %SD beyonds MAX_PCT_DEV;
            'No Difference':        the %DIFF is zero;
            'No Significance':      the Significance less than the
                                    CONFIDENCE_THRESHOLD;
            'Major Improvement' and 'Major Regression':
                the Significance beyonds CONFIDENCE_THRESHOLD and %DIFF
                beyonds REGRESSION_THRESHOLD;
            'Minor Improvement' and 'Minor Regression':
                the Significance beyonds CONFIDENCE_THRESHOLD but %DIFF
                is below REGRESSION_THRESHOLD;

        """
        MAX_PCT_DEV = max_percent_dev
        REGRESSION_THRESHOLD = regression_threshold
        CONFIDENCE_THRESHOLD = confidence_threshold

        if np.isnan(base_pct_dev) or np.isnan(test_pct_dev) or np.isnan(
                pct_diff) or np.isnan(significance):
            return 'Data Invalid'

        if base_pct_dev > MAX_PCT_DEV or test_pct_dev > MAX_PCT_DEV:
            return 'Variance Too Large'

        if pct_diff == 0:
            return 'No Difference'

        if significance < CONFIDENCE_THRESHOLD:
            return 'No Significance'

        if (higher_is_better and pct_diff > 0) or (not higher_is_better
                                                   and pct_diff < 0):
            if abs(pct_diff) >= REGRESSION_THRESHOLD:
                return 'Major Improvement'
            else:
                return 'Minor Improvement'
        else:
            if abs(pct_diff) >= REGRESSION_THRESHOLD:
                return 'Major Regression'
            else:
                return 'Minor Regression'

    def _calculate_kpi_and_fill_series(self, series, df_base, df_test, label,
                                       source_label, higher_is_better,
                                       max_percent_dev, regression_threshold,
                                       confidence_threshold):
        """Calculate the statistics and fill the Series for specified KPI."""
        # Calculate and fill the average and %SD of the base and test samples
        series[label + '-BASE-AVG'] = df_base[source_label].mean()
        series[label + '-BASE-%SD'] = df_base[source_label].std(
            ddof=1) / series[label + '-BASE-AVG'] * 100
        series[label + '-TEST-AVG'] = df_test[source_label].mean()
        series[label + '-TEST-%SD'] = df_test[source_label].std(
            ddof=1) / series[label + '-TEST-AVG'] * 100

        # Calculate and fill the %DIFF of the test samples againest base
        series[label + '-%DIFF'] = (
            series[label + '-TEST-AVG'] -
            series[label + '-BASE-AVG']) / series[label + '-BASE-AVG'] * 100

        # Calculate and fill the Significance
        series[label + '-SIGN'] = self._get_significance(
            df_base[source_label], df_test[source_label])

        # Calculate and fill the Conclusion
        series[label + '-CONCLUSION'] = self._get_conclusion(
            series[label + '-BASE-%SD'], series[label + '-TEST-%SD'],
            series[label + '-%DIFF'], series[label + '-SIGN'],
            higher_is_better, max_percent_dev, regression_threshold,
            confidence_threshold)

        return None

    def _complete_report_dataframe(self):
        """Complete the report DataFrame."""
        # Go through each series from the report DataFrame, get correlated
        # data from the test and base DataFrames, calculate the KPIs and
        # fill the results into report DataFrame.
        for (index, series) in self.df_report.iterrows():
            # Get correlated DataFrames
            sub_test = self.df_test
            sub_base = self.df_base

            # Filter the DataFrames by the KEYs
            for key in self.keys:
                source_label = key['source_label']
                target_label = key['target_label']
                target_value = series[target_label]

                # Update the DataFrames
                sub_test = sub_test[sub_test[source_label] == target_value]
                sub_base = sub_base[sub_base[source_label] == target_value]

            # Calculate KPIs
            for kpi in self.kpis:
                self._calculate_kpi_and_fill_series(
                    series, sub_base, sub_test, kpi['target_label'],
                    kpi['source_label'], kpi['higher_is_better'],
                    kpi['max_percent_dev'], kpi['regression_threshold'],
                    kpi['confidence_threshold'])

            # Show current series
            print(series)

            # Save current series
            self.df_report.iloc[index] = series

        return None

    def _format_report_dataframe(self):
        """Format the report DataFrame."""
        self.df_report = self.df_report.round(4)
        self.df_report = self.df_report.fillna('N/A')

        # Add units to the columns
        for key in self.keys:
            if key['target_unit'] is not None:
                pre_label = key['target_label']
                post_label = '{0}({1})'.format(pre_label, key['target_unit'])
                self.df_report.rename(columns={pre_label: post_label},
                                      inplace=True)

        for kpi in self.kpis:
            if kpi['target_unit'] is not None:
                for suffix in ('BASE-AVG', 'TEST-AVG'):
                    pre_label = '{0}-{1}'.format(kpi['target_label'], suffix)
                    post_label = '{0}({1})'.format(pre_label,
                                                   kpi['target_unit'])
                    self.df_report.rename(columns={pre_label: post_label},
                                          inplace=True)

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
            print('[ERROR] Missing required params: params[report_csv]')
            return 1

        # Write the report to the csv file
        try:
            print('[NOTE] Dumping data into csv file "%s"...' %
                  params['report_csv'])
            content = self.df_report.to_csv()
            with open(params['report_csv'], 'w') as f:
                f.write(content)
            print('[NOTE] Finished!')

        except Exception as err:
            print('[ERROR] Error while dumping to csv file: %s' % err)
            return 1

        return 0


def generate_flent_benchmark_report(base_csv, test_csv, report_csv):
    """Generate flent benchmark report."""
    flentbenchreporter = FlentBenchmarkReporter()

    # Load base and test samples
    return_value = flentbenchreporter.load_samples({
        'base_csv': base_csv,
        'test_csv': test_csv
    })
    if return_value:
        exit(1)

    # Generate benchmark report
    flentbenchreporter.generate_report()

    # Dump the report as CSV file
    return_value = flentbenchreporter.report_to_csv({'report_csv': report_csv})
    if return_value:
        exit(1)

    exit(0)


@click.command()
@click.option('--base_csv',
              type=click.Path(exists=True),
              help='Specify the CSV file of the base samples.')
@click.option('--test_csv',
              type=click.Path(exists=True),
              help='Specify the CSV file of the test samples.')
@click.option('--report_csv',
              type=click.Path(),
              help='Specify the CSV file to store the benchmark report.')
def cli(base_csv, test_csv, report_csv):
    """Command Line Interface."""
    # Parse and check the parameters
    if not base_csv or not test_csv or not report_csv:
        print('[ERROR] Missing parameter, use "--help" to check the usage.')
        exit(1)

    # Generate flent benchmark report
    generate_flent_benchmark_report(base_csv, test_csv, report_csv)


if __name__ == '__main__':
    cli()
