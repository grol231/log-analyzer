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
    "REPORT_DIR": "./cdreports",
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
        else:
            date_str = match.groupdict()['date']
            date = datetime.strptime(date_str, '%Y%m%d')
        path = log_dir + '/' + file_name
        extension = 'gz' if 'gz' == file_name[-2:] else 'plain'
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
    config_file = open(config_file_path)
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


def parse_log(path, extension):
    logfile = gzip.open(path) if 'gz' == extension else open(path)
    for l in logfile.readlines():
        if 'gz' == extension:
            yield re.search(line_format, l.decode('utf-8'))
        else:
            yield re.search(line_format, l)


def get_url_counts(log):
    url_counts = {}
    for line in log:
        if line['url'] in url_counts:
            url_counts[line['url']] += 1
        else:
            url_counts[line['url']] = 1
    return url_counts


def get_url_percents(url_counts, log_size):
    url_percent = {}
    for url in url_counts:
        url_percent[url] = url_counts[url]/log_size * 100
    return url_percent


def get_url_time_sums(log):
    url_time_sums = {}
    for line in log:
        if line['url'] in url_time_sums:
            url_time_sums[line['url']] += float(line['time'])
        else:
            url_time_sums[line['url']] = float(line['time'])
    return url_time_sums


def get_request_common_time(url_time_sums):
    request_common_time = 0
    for url in url_time_sums:
        request_common_time += url_time_sums[url]
    return request_common_time


def get_url_time_percents(url_time_sums, request_common_time):
    url_time_percents = {}
    for url in url_time_sums:
        url_time_percents[url] = url_time_sums[url]/request_common_time * 100
    return url_time_percents


def get_url_avg_times(url_time_sums, url_counts):
    url_avg_times = {}
    for url in url_counts:
        url_avg_times[url] = url_time_sums[url] / url_counts[url]
    return url_avg_times


def get_url_time_max(log):
    url_time_max = {}
    for line in log:
        if line['url'] not in url_time_max:
            url_time_max[line['url']] = line['time']
        else:
            if line['time'] > url_time_max[line['url']]:
                url_time_max[line['url']] = line['time']
    return url_time_max


def get_url_time_medians(log):
    request_times = {}
    for line in log:
        if line['url'] in request_times:
            request_times[line['url']].append(float(line['time']))
        else:
            request_times[line['url']] = []
            request_times[line['url']].append(float(line['time']))
    url_time_medians = {}
    for url in request_times:
        url_time_medians[url] = statistics.median(request_times[url])
    return url_time_medians


def process(config_data):
    last_log = get_last_log(config_data['LOG_DIR'])
    if last_log:
        if is_processed(last_log.date, config_data['REPORT_DIR']):
            logging.info('Log already processed.')
            return
        log = []
        unhandled_line_count = 0
        line_count = 0
        lines = parse_log(last_log.path, last_log.extension)
        for l in lines:
            line_count += 1
            if l:
                log.append(l.groupdict())
            else:
                unhandled_line_count += 1
    if unhandled_line_count/line_count * 100 > LOG_PARSING_ERROR_PER:
        logging.error("More than {}% lines with parsing errors.".format(LOG_PARSING_ERROR_PER))
        return
    url_counts = get_url_counts(log)
    url_percents = get_url_percents(url_counts, len(log))
    url_time_sums = get_url_time_sums(log)
    request_common_time = get_request_common_time(url_time_sums)
    url_time_percents = get_url_time_percents(url_time_sums, request_common_time)
    url_avg_times = get_url_avg_times(url_time_sums, url_counts)
    url_time_max = get_url_time_max(log)
    url_time_medians = get_url_time_medians(log)
    report_url_time_sums = sorted(url_time_sums.items(), key=lambda kv: kv[1], reverse=True)[0:1000]
    table_json = []
    for s in report_url_time_sums:
        url = s[0]
        line = {
            'count': url_counts[url],
            'time_avg': url_avg_times[url],
            'time_max': url_time_max[url],
            'time_sum': s[1],
            'url': url,
            'time_med': url_time_medians[url],
            'time_perc': url_time_percents[url],
            'count_perc': url_percents[url]
        }
        table_json.append(line)
    report_template = open(REPORT_TEMPLATE_PATH, 'r').read()
    template = Template(report_template)
    report = template.safe_substitute(table_json=table_json)
    open(config_data['REPORT_DIR'] + '/' + 'report_' + last_log.date.strftime('%Y%m%d') + '.html', 'w').write(report)


def main():
    try:
        config_data = get_config()
        logging.basicConfig(format='[%(asctime)s] %(levelname).1s %(message)s', level=logging.INFO,
                            datefmt='%Y.%m.%d %H:%M:%S', filename=config_data['ANALYZER_LOG'])
        process(config_data)
    except Exception as e:
        logging.exception(e)
        return
    logging.info('analyze completed successfully')


if __name__ == "__main__":
    main()
