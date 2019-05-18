#!/usr/bin/env python


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import gzip
import os
import re
from string import Template
import statistics
import argparse
import json
import logging
from collections import namedtuple
from datetime import datetime

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "ANALYZER_LOG": ""
}
LOG_PARSING_ERROR_PER = 50
REPORT_TEMPLATE_PATH = 'template/report.html'
line_format = re.compile(r"""(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) -  - \[(\d{2}\/[a-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] ((\"(GET|POST|DELETE|PATCH|PUT) )(?P<url>.+)(http\/1\.1")) (\d{3}) (\d+) (["]-["]) (["]((\-)|(.+))["]) (["]-["]) (["]((\-)|(.+))["]) (["]((\-)|(.+))["]) ((?P<time>(\-)|(.+)))""", re.IGNORECASE)
log_nginx_format = re.compile(r"""nginx-access-ui.log-(?P<date>\d[0-9]+)(.gz|$)""")


def get_last_log(log_dir):
    LogFile = namedtuple('LogFile', ['path', 'date', 'extension'])
    last_log = None
    for file_name in os.listdir(log_dir):
        match = re.search(log_nginx_format, file_name)
        if match is None:
            continue
        date_str = match.groupdict()['date']
        date = datetime.strptime(date_str, '%Y%m%d')
        path = os.path.join(log_dir, file_name)
        extension = 'gz' if 'gz' == file_name[-2:] else ''
        if last_log:
            if last_log.date < date:
                last_log = LogFile(path, date, extension)
        else:
            last_log = LogFile(path, date, extension)
    return last_log


def is_processed(date, report_dir):
    report_name = 'report_{}.html'.format(date.strftime('%Y%m%d'))
    return os.path.exists(report_dir + '/' + report_name)


def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', dest='config', type=str, default='config/config.txt')
    args = parser.parse_args()
    config_file_path = args.config
    global config
    if os.stat(config_file_path).st_size == 0:
        return config
    with open(config_file_path) as config_file:
        config_json = json.load(config_file)
    result = {}
    if 'LOG_DIR' in config_json:
        result['LOG_DIR'] = config_json['LOG_DIR']
    else:
        result['LOG_DIR'] = config['LOG_DIR']
    if 'REPORT_DIR' in config_json:
        result['REPORT_DIR'] = config_json['REPORT_DIR']
    else:
        result['REPORT_DIR'] = config['REPORT_DIR']
    if 'REPORT_SIZE' in config_json:
        result['REPORT_SIZE'] = config_json['REPORT_SIZE']
    else:
        result['REPORT_SIZE'] = config['REPORT_SIZE']
    if 'ANALYZER_LOG' in config_json:
        result['ANALYZER_LOG'] = config_json['ANALYZER_LOG']
    elif config['ANALYZER_LOG']:
        result['ANALYZER_LOG'] = config['ANALYZER_LOG']
    else:
        result['ANALYZER_LOG'] = None
    return result


def parse_log(last_log, report_dir):
    if last_log is False:
        raise Exception('there is not log file in the log dir')
    elif is_processed(last_log.date, report_dir):
        raise Exception('log already processed')
    with (gzip.open(last_log.path, mode='rt', encoding='utf-8') if 'gz' == last_log.extension else\
                                                open(last_log.path, encoding='utf-8')) as logfile:
        unhandled_line_count = 0
        for idx, line in enumerate(logfile.readlines()):
            log_size = idx + 1
            data = re.search(line_format, line)
            if data:
                yield data.groupdict(), log_size
            else:
                unhandled_line_count += 1
                if unhandled_line_count / log_size * 100 > LOG_PARSING_ERROR_PER:
                    raise Exception("more than {}% lines with parsing errors".format(LOG_PARSING_ERROR_PER))


def calculate_statistic(log):
    url_list = []
    request_counts = {}
    request_time_amounts = {}
    request_time_peaks = {}
    request_time_lists = {}
    for line, log_size in log:
        url = line['url']
        time = line['time']
        if url in url_list:
            request_counts[url] += 1
            request_time_amounts[url] += float(time)
            request_time_lists[url].append(float(time))
            if time > request_time_peaks[url]:
                request_time_peaks[url] = time
        else:
            url_list.append(url)
            request_counts[url] = 1
            request_time_amounts[url] = float(time)
            request_time_peaks[url] = time
            request_time_lists[url] = []
            request_time_lists[url].append(float(time))

    common_request_time = sum(request_time_amounts.values())
    request_time_medians = {}
    request_count_percents = {}
    request_time_percents = {}
    average_request_times = {}
    table_json = []
    for url in url_list:
        request_time_medians[url] = statistics.median(request_time_lists[url])
        request_count_percents[url] = request_counts[url]/log_size * 100
        request_time_percents[url] = request_time_amounts[url]/common_request_time * 100
        average_request_times[url] = request_time_amounts[url]/request_counts[url]
        line = {
            'count': request_counts[url],
            'time_avg': average_request_times[url],
            'time_max': request_time_peaks[url],
            'time_sum': request_time_amounts[url],
            'url': url,
            'time_med': request_time_medians[url],
            'time_perc': request_time_percents[url],
            'count_perc': request_count_percents[url]
        }
        table_json.append(line)
    return table_json


def main():
    config_data = get_config()
    logging.basicConfig(format='[%(asctime)s] %(levelname).1s %(message)s', level=logging.INFO,
                        datefmt='%Y.%m.%d %H:%M:%S', filename=config_data['ANALYZER_LOG'])

    last_log = get_last_log(config_data['LOG_DIR'])
    data = parse_log(last_log, config_data['REPORT_DIR'])
    table_json = calculate_statistic(data)

    with open(REPORT_TEMPLATE_PATH, 'r', encoding='utf-8') as template_file:
        report_template = template_file.read()
    template = Template(report_template)
    report = template.safe_substitute(table_json=table_json)
    if os.path.exists(config_data['REPORT_DIR']) is False:
        os.mkdir(config_data['REPORT_DIR'])
    report_path = config_data['REPORT_DIR'] + '/' + 'report_' + last_log.date.strftime('%Y%m%d') + '.html'
    with open(report_path, 'w') as report_file:
        report_file.write(report)
    logging.info('analyze completed successfully')


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(e)
        logging.info('analysis aborted')


