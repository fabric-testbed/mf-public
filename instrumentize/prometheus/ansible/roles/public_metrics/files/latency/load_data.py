import os
import configparser
import pandas as pd
from influxdb_client_3 import InfluxDBClient3
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pyarrow as pa


def get_geoloc_df(sites_file, slice_file):
    all_sites_df = pd.read_csv(sites_file)
    slice_df = pd.read_csv(slice_file)
    slice_df = slice_df.merge(all_sites_df)

    return slice_df



def download_influx_data(conf_path, duration='15 minute', outfile=None,
                          src_dst=None):
    '''
    Input:
        duration(str): '1 minute', '5 minutes', '3 hours', '2 days' etc.
        outfile(str): None or 'path/to/out.csv'
        src_dst(tuple): (<str>, <str>) example: ("10.0.0.1", "10.0.1.1")

    Output:
        Dataframe: (['latency', 'received', 'receiver', 'sender', 'seq_n', 'time'])
    '''

    # Read InfluxDB conf
    config = configparser.ConfigParser()
    config.read(conf_path)

    host = config['InfluxDB']['host']
    token = config['InfluxDB']['token']
    org = config['InfluxDB']['org']
    database = config['InfluxDB']['database']
    language = config['InfluxDB']['language']

    #print(f'host {host}, token: {token}, org: {org}, database: {database}, \
    #    language: {language}')

    client = InfluxDBClient3(host=host, token=token, org=org)

    query = f'''SELECT *
    FROM "owl"
    WHERE
    time >= now() - interval '{duration}'
    AND
    ("latency" IS NOT NULL OR "received" IS NOT NULL)'''


    if src_dst:
        path_filter = f''' AND "sender" IN ('{src_dst[0]}')
                        AND "receiver" IN ('{src_dst[1]}')'''

        query += path_filter

    print(query)

    table = client.query(query=query,
                        database=database,
                        language=language, mode="all")

    if outfile:
        write_options = pa.csv.WriteOptions(include_header=False)
        pa.csv.write_csv(table, outfile, write_options=write_options )

    # Convert pyarrow.Table to Pandas Dataframe
    latency_df = table.to_pandas()

    # Convert Unix epoch time to datetime64 type
    latency_df['received'] = pd.to_datetime(latency_df['received'], unit='s')

    return latency_df


def download_influx_data_local(conf_path, duration='5 minutes', outfile=None,
                          src_dst=('10.0.0.1', '10.0.0.2')):
    '''
    Input:
        duration(str): '1 minute', '5 minutes', '3 hours', '2 days' etc.
        outfile(str): None or 'path/to/out.csv'
        src_dst(tuple): (<str>, <str>) example: ("10.0.0.1", "10.0.1.1")

    Output:
        Dataframe: (['latency', 'received', 'receiver', 'sender', 'seq_n', 'time'])
    '''

    # Read InfluxDB conf
    config = configparser.ConfigParser()
    config.read(os.path.join(conf_path))

    host = config['InfluxDB']['host']
    token = config['InfluxDB']['token']
    org = config['InfluxDB']['org']
    database = config['InfluxDB']['database']

    print(f'host {host}, token: {token}, org: {org}, database: {database}')

    client = InfluxDBClient(url=host, token=token, org=org)



    query_api = client.query_api()

    time_conversion = {'5 minutes': '-5m',
                       '15 minutes': '-15m',
                       '30 minutes': '-30m',
                       '1 hour': '-1h',
                       '3 hours': '-3h',
                       '6 hours': '-6h',
                       '12 hours': '-12h',
                       '24 hours': '-24h'}

    converted_duration = time_conversion[duration]
    print(f"querying {converted_duration}")

    query = f"""from(bucket: "{database}")
     |> range(start: {converted_duration})
     |> filter(fn: (r) => r._measurement == "owl")
     |> filter(fn: (r) => r._field == "latency" or r._field == "received" or r._field == "seq_n")
     |> filter(fn: (r) => r.sender == "{src_dst[0]}")
     |> filter(fn: (r) => r.receiver =="{src_dst[1]}")
     |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")"""

    print(query)

    #tables = query_api.query(query, org="fabric")
    #
    #for table in tables:
    #  for record in table.records:
    #    print(record)


    df = query_api.query_data_frame(query, org=org)

    latency_df = df[['latency', 'received', 'receiver', 'sender', 'seq_n', '_time']]
    # Convert Unix epoch time to datetime64 type
    latency_df['received'] = pd.to_datetime(latency_df['received'], unit='s')

    if outfile:
        latency_df.to_csv(outfile, index=True)


    print(latency_df)


    return latency_df
