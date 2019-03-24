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

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "/home/kgm/otus/homework/reports",
    "LOG_DIR": "/home/kgm/otus/homework/log"
}

lineformat = re.compile(r"""(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) -  - \[(?P<dateandtime>\d{2}\/[a-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] ((\"(GET|POST|DELETE|PATCH|PUT) )(?P<url>.+)(http\/1\.1")) (?P<statuscode>\d{3}) (?P<bytessent>\d+) (["]-["]) (["](?P<refferer>(\-)|(.+))["]) (["]-["]) (["](?P<useragent>(\-)|(.+))["]) (["](?P<requestid>(\-)|(.+))["]) ((?P<requesttime>(\-)|(.+)))""", re.IGNORECASE)

def main():
    for f in os.listdir(config["LOG_DIR"]):
        if f.endswith(".gz"):
            logfile = gzip.open(os.path.join(config["LOG_DIR"], f))
            print("open gz")
        else:
            logfile = open(os.path.join(config["LOG_DIR"], f))
            print("open file")
        arr = []

        for l in logfile.readlines():
            data = re.search(lineformat, l)
            print("read line")
            print(data)
            if data:
                datadict = data.groupdict()
                arr.append(datadict)
                ip = datadict["ipaddress"]
                datetimestring = datadict["dateandtime"]
                url = datadict["url"]
                bytessent = datadict["bytessent"]
                referrer = datadict["refferer"]
                useragent = datadict["useragent"]
                requestid = datadict["requestid"]
                requesttime = datadict["requesttime"]
                status = datadict["statuscode"]
                method = data.group(6)
                print("print data")
                print("ip: {}, datetime: {}, url: {}, bytessent: {}, referrer: {}, status: {}, method: {}, useragent: {}, requestid: {}, requesttime: {}".format(ip, datetimestring, url, bytessent, referrer, status, method, useragent, requestid, requesttime))

        logfile.close()
    print('#####################################################################################################################################################')
    urlCounts = {}
    for a in arr:
        if a['url'] in urlCounts:
            ++urlCounts[a['url']]
        else:
            urlCounts[a['url']] = 1

    for u in urlCounts:
        print('url: {}, count: {}'.format(u, urlCounts[u]))

    reportSize = len(arr)
    print('reportSize: {}'.format(reportSize))

    urlPercent = {}
    for c in urlCounts:
        urlPercent[c] = urlCounts[c] / reportSize

    print('#######################################################################################################################################################')

    urlTimeSum = {}
    for a in arr:
        if a['url'] in urlTimeSum:
            urlTimeSum[a['url']] += float(a['requesttime'])
        else:
            urlTimeSum[a['url']] = 0
            urlTimeSum[a['url']] += float(a['requesttime'])

    for t in urlTimeSum:
        print('url: {}, sum: {}'.format(t, urlTimeSum[t]))

    print('#######################################################################################################################################################')

    for p in urlPercent:
        print('url: {}, percent: {}'.format(p, urlPercent[p]))

    requestCommonTime = 0
    for t in urlTimeSum:
        requestCommonTime += urlTimeSum[t]

    urlTimePerc = {}
    for t in urlTimeSum:
        urlTimePerc[t] = urlTimeSum[t]/requestCommonTime

    print('#########################################################################################################################################################')
    for t in urlTimePerc:
        print('url: {}, timePerc: {}'.format(t, urlTimePerc[t]))

    urlAvgTime = {}
    for c in urlCounts:
        urlAvgTime[c] = urlTimeSum[c]/urlCounts[c]

    urlTimeMax = {}
    for a in arr:
        time = a['requesttime']
        if a['url'] not in urlTimeMax:
            urlTimeMax[a['url']] = time
        else:
            if time > urlTimeMax[a['url']]:
                urlTimeMax[a['url']] = time
    print('##########################################################################################################################################################')
    for m in urlTimeMax:
        print('url: {}, timeMax: {}'.format(m, urlTimeMax[m]))

    print('##########################################################################################################################################################')
    for a in urlAvgTime:
        print('url: {}, avgTime: {}'.format(a, urlAvgTime[a]))


    urlReqTimesList = {}
    for a in arr:
        if a['url'] in urlReqTimesList:
            urlReqTimesList[a['url']].append(float(a['requesttime']))
        else:
            urlReqTimesList[a['url']] = []
            urlReqTimesList[a['url']].append(float(a['requesttime']))

    urlTimeMed = {}
    for url in urlReqTimesList:
        urlTimeMed[url] = statistics.median(urlReqTimesList[url])

    print('#'*100)
    for m in urlTimeMed:
        print('url: {}, med: {}'.format(m, urlTimeMed[m]))

    str = open('/home/kgm/otus/homework/log-analyzer/template/report.html', 'r').read()
    table_json = []
    for url in urlCounts:
        line = {'count': urlCounts[url],
                'time_avg': urlAvgTime[url],
                'time_max': urlTimeMax[url],
                'time_sum': urlTimeSum[url],
                'url': url,
                'time_med': urlTimeMed[url],
                'time_perc': urlTimePerc[url],
                'count_perc': urlPercent[url]}
        table_json.append(line)

    t = Template(str)
    result = t.safe_substitute(table_json=table_json)
    open(config['REPORT_DIR'] + '/' + 'report_24_03_2019.html', 'w').write(result)

if __name__ == "__main__":
    main()