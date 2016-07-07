import unittest
import shutil
import importlib
from pathlib import Path 
from types import FunctionType

import pandas as pd 
import numpy as np
from pandas.util.testing import assert_frame_equal, assert_series_equal

from gtfsrtk.utilities import *
from gtfsrtk.main import *


# Load some feeds
DATA_DIR = Path('data')
FEEDS = []
for path in (DATA_DIR/'test_gtfsr_trip_updates').iterdir():
    with path.open() as src:
        FEEDS.append(json.load(src))

class TestMain(unittest.TestCase):

    def test_build_get_feed(self):
        f = build_get_feed('bingo', {}, {})
        # Should be a function
        self.assertIsInstance(f, FunctionType)

    def test_get_timestamp(self):
        # Null feed should yield None
        self.assertEqual(get_timestamp(None), None)
        # Timestamp should be a string
        self.assertIsInstance(get_timestamp(FEEDS[0]), str)

    def test_extract_delays(self):
        for feed in [None, FEEDS[0]]:
            delays = extract_delays(feed)
            # Should be a data frame
            self.assertIsInstance(delays, pd.DataFrame)
            # Should have the correct columns
            expect_cols = ['route_id', 'trip_id', 'stop_id',
              'stop_sequence', 'arrival_delay', 'departure_delay']
            self.assertEqual(set(delays.columns), set(expect_cols))

    def test_combine_delays(self):
        delays_list = [extract_delays(f) for f in FEEDS]
        f = combine_delays(delays_list)
        # Should be a data frame
        self.assertIsInstance(f, pd.DataFrame)
        # Should have the correct columns
        expect_cols = ['route_id', 'trip_id', 'stop_id',
          'stop_sequence', 'arrival_delay', 'departure_delay']
        self.assertEqual(set(f.columns), set(expect_cols))

    def test_build_augmented_stop_times(self):
        gtfsr_dir = DATA_DIR/'test_gtfsr_trip_updates'
        path = DATA_DIR/'auckland_gtfs_20160519.zip'
        gtfs_feed = gt.read_gtfs(path, dist_units_in='km')
        date = '20160519'
        f = build_augmented_stop_times(gtfsr_dir, gtfs_feed, date)
        # Should be a data frame
        self.assertIsInstance(f, pd.DataFrame)
        # Should have the correct columns
        st = gt.get_stop_times(gtfs_feed, date)
        expect_cols = st.columns.tolist() + ['arrival_delay', 
          'departure_delay']
        self.assertEqual(set(f.columns), set(expect_cols))
        # Should have the correct number of rows
        self.assertEqual(f.shape[0], st.shape[0])

    def test_interpolate_delays(self):
        gtfsr_dir = DATA_DIR/'test_gtfsr_trip_updates'
        path = DATA_DIR/'auckland_gtfs_20160519.zip'
        gtfs_feed = gt.read_gtfs(path, dist_units_in='km')
        date = '20160519'
        ast = build_augmented_stop_times(gtfsr_dir, gtfs_feed, date)
        f = interpolate_delays(ast, dist_threshold=1)
        # Should be a data frame
        self.assertIsInstance(f, pd.DataFrame)
        # Should have the correct columns
        self.assertEqual(set(f.columns), set(ast.columns))
        # Should have the correct number of rows
        self.assertEqual(f.shape[0], ast.shape[0])
        # For each trip, delays should be all nan or filled
        for __, group in f.groupby('trip_id'):
            n = group.shape[0]
            for col in ['arrival_delay', 'departure_delay']:
                k = group[col].count()
                self.assertTrue(k == 0 or k == n)


if __name__ == '__main__':
    unittest.main()