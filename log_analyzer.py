#!/usr/bin/env python


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import gzip
import os
import sys
import re

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "/home/kgm/Dropbox/otus/homework/reports",
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

        for l in logfile.readlines():
            data = re.search(lineformat, l)
            print("read line")
            print(data)
            if data:
                datadict = data.groupdict()
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

        
    

if __name__ == "__main__":
    main()
