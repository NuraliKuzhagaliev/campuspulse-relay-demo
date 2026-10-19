import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('prepare_ai_judges',Path(__file__).parents[1]/'scripts/prepare_ai_judges.py')
issuer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(issuer)


class OwnerClockTests(unittest.TestCase):
    def test_observed_83_second_skew_uses_server_clock(self):
        self.assertEqual(issuer.bounded_server_timestamp('1970-01-01T00:18:03+00:00',1000,1000.8),1083)

    def test_rejects_unbounded_skew_slow_response_and_naive_time(self):
        for value,start,end in [('1970-01-01T00:30:00+00:00',1000,1001),('1970-01-01T00:18:03+00:00',1000,1011),('1970-01-01T00:18:03',1000,1001)]:
            with self.subTest(value=value,end=end),self.assertRaises(ValueError):
                issuer.bounded_server_timestamp(value,start,end)
