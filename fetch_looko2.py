#!/usr/bin/python3.5

# -*- coding: utf-8 -*-
import requests
import logging
import argparse
from influxdb import InfluxDBClient
from pprint import pprint

"""Python bridge between LookO2 API and InfluxDB."""
"""This code is meant to be started by crond every 10 minutes."""

parser = argparse.ArgumentParser(description='Fetches air quality data from\
 LookO2 sensor and pushes them into InfluxDB')
parser.add_argument("--verbose",
                    help='Set verbosity level',
                    choices=['DEBUG', 'INFO', 'WARNING', 'CRITICAL'],
                    default='CRITICAL'
                    )
parser.add_argument('--LookO2_device',
                    help='''LookO2 sensor ID,
                    fetch it from http://www.looko2.com/heatmap.php,
                    for example:
                    http://looko2.com/tracker.php?lan=&search=**A020A6036868**''',
                    required=True
                    )
parser.add_argument('--LookO2_token',
                    help='''LookO2 API access token,
                        get it by writing an e-mail to kontakt@looko2.com''',
                    required=True
                    )
parser.add_argument('--LookO2_url',
                    help='LookO2 API URL',
                    default='http://api.looko2.com/'
                    )
parser.add_argument('--InfluxDB_host', default='localhost')
parser.add_argument('--InfluxDB_port', default='8086')
parser.add_argument('--InfluxDB_user', default='root')
parser.add_argument('--InfluxDB_password', default='root')
parser.add_argument('--InfluxDB_database', required=True)

args = parser.parse_args()
if args.verbose:
    logging.basicConfig(level=args.verbose)


def get_LookO2(LookO2_device, LookO2_token, LookO2_url):
    payload = {
        'id': LookO2_device,
        'token': LookO2_token,
        'method': 'GetLOOKO'
    }
    logging.debug('Requesting JSON from ' + LookO2_url)
    response = requests.get(LookO2_url, params=payload)
    LookO2_json = response.json()
    logging.debug('Received PM1: ' + LookO2_json['PM1'])
    logging.debug('Received PM2.5: ' + LookO2_json['PM25'])
    logging.debug('Received PM10: ' + LookO2_json['PM10'])
    return {
        'PM1': LookO2_json['PM1'],
        'PM25': LookO2_json['PM25'],
        'PM10': LookO2_json['PM10']
    }


def wite_to_InfluxDB(InfluxDB_host,
                     InfluxDB_port,
                     InfluxDB_user,
                     InfluxDB_password,
                     InfluxDB_database,
                     PM1,
                     PM25,
                     PM10):
    client = InfluxDBClient()
    client = InfluxDBClient(
        host=InfluxDB_host,
        port=InfluxDB_port,
        username=InfluxDB_user,
        password=InfluxDB_password,
        database=InfluxDB_database
    )
    logging.debug('Connected to InfluxDB')
    json_body = [
        {
            "measurement": "AirQualityMeasures",
            # "time": timestamp,
            "fields": {
                "PM1": int(PM1),
                "PM25": int(PM25),
                "PM10": int(PM10)
            }
        }
    ]
    logging.debug(json_body)
    client.write_points(points=json_body, time_precision='ms')
    logging.info('Sent metrics to InfluxDB')


values = get_LookO2(args.LookO2_device, args.LookO2_token, args.LookO2_url)
wite_to_InfluxDB(InfluxDB_host=args.InfluxDB_host,
                 InfluxDB_port=args.InfluxDB_port,
                 InfluxDB_user=args.InfluxDB_user,
                 InfluxDB_password=args.InfluxDB_password,
                 InfluxDB_database=args.InfluxDB_database,
                 PM1=int(values['PM1']),
                 PM25=int(values['PM25']),
                 PM10=int(values['PM10'])
                 )
