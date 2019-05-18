import unittest
import log_analyzer

log = [
    ({'url': '/api/v2/banner/25019354', 'time': 0.390}, 1)
]

class TestLogAnalyzer(unittest.TestCase):

    def test_calculate_statistic(self):
        expected_table_json = []
        expected_line = {
            'count': 1,
            'time_avg': 0.39,
            'time_max': 0.39,
            'time_sum': 0.39,
            'url': '/api/v2/banner/25019354',
            'time_med': 0.39,
            'time_perc': 100.0,
            'count_perc': 100.0
        }
        expected_table_json.append(expected_line)
        table_json = log_analyzer.calculate_statistic(log)
        self.assertSequenceEqual(table_json, expected_table_json)


    # def test_get_url_counts(self):
    #     url_counts = log_analyzer.get_url_counts(log)
    #     self.assertEqual(len(url_counts), 3)
    #     self.assertEqual(url_counts['/api/v2/banner/1717161'], 2)
    #     self.assertEqual(url_counts['/api/v2/banner/25020545'], 1)
    #
    # def test_get_url_percents(self):
    #     url_counts = log_analyzer.get_url_counts(log)
    #     url_percents = log_analyzer.get_url_percents(url_counts, len(log))
    #     self.assertEqual(len(url_percents), 3)
    #     self.assertEqual(url_percents['/api/v2/banner/1717161'], 50.0)
    #     self.assertEqual(url_percents['/api/v2/banner/25019354'], 25.0)
    #
    # def test_get_url_time_sums(self):
    #     url_time_sums = log_analyzer.get_url_time_sums(log)
    #     self.assertEqual(len(url_time_sums), 3)
    #     self.assertEqual(url_time_sums['/api/v2/banner/1717161'], 0.276)
    #     self.assertEqual(url_time_sums['/api/v2/banner/25019354'], 0.39)
    #
    # def test_get_request_common_time(self):
    #     url_time_sums = log_analyzer.get_url_time_sums(log)
    #     request_common_time = log_analyzer.get_request_common_time(url_time_sums)
    #     self.assertEqual(int(request_common_time*10), 14)
    #
    # def test_get_url_time_percents(self):
    #     url_time_sums = log_analyzer.get_url_time_sums(log)
    #     request_common_time = log_analyzer.get_request_common_time(url_time_sums)
    #     url_time_percents = log_analyzer.get_url_time_percents(url_time_sums, request_common_time)
    #     self.assertEqual(len(url_time_percents), 3)
    #     self.assertEqual(int(url_time_percents['/api/v2/banner/1717161']), 19)
    #     self.assertEqual(int(url_time_percents['/api/v2/banner/25019354']), 27)
    #
    # def test_get_url_avg_times(self):
    #     url_time_sums = log_analyzer.get_url_time_sums(log)
    #     url_counts = log_analyzer.get_url_counts(log)
    #     url_avg_times = log_analyzer.get_url_avg_times(url_time_sums, url_counts)
    #     self.assertEqual(len(url_avg_times), 3)
    #     self.assertEqual(url_avg_times['/api/v2/banner/1717161'], 0.138)
    #
    # def test_get_url_time_max(self):
    #     url_time_max = log_analyzer.get_url_time_max(log)
    #     self.assertEqual(url_time_max['/api/v2/banner/1717161'], 0.138)
    #
    # def test_get_url_time_medians(self):
    #     url_time_medians = log_analyzer.get_url_time_medians(log)
    #     self.assertEqual(url_time_medians['/api/v2/banner/1717161'], 0.138)


if __name__ == '__main__':
    unittest.main()