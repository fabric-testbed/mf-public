import os
import sys
import logging
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Input, Output, State, callback
import pandas as pd
import load_data as data_loader
import graph

# If using this on the public metrics site, a few changes are needed. Set the following variable to True
public_metrics_site = True

'''
Usage:
python app.py <path/to/config/file/dir>


Requirements:
Save the following inside a directory (default = "./confs")
-----------
influxdb.conf
  org = <org name>
  host = <host url> 
  database = <bucket name>
  language = <for v3, it should be sql>
  token = <influxDB token>

sites.csv: site, lon, lat (for all sites)
slice.csv: site, ip_address, node_name

'''

logger = logging.getLogger()
# Setting the threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)


############ Config data paths and InfluxDB Version ##############

# InfluxDB version
influxdb_version = 'v2'  # local ('v2') or cloud ('v3')

# Get the config files path from environment variable (for remote node) or command line argument
conf_files = os.environ.get("LATENCY_CONFIG_DIR")

if not conf_files:
    if len(sys.argv) == 1:
        print("Usage: python app.py <path/to/config/file/dir>. \nExisting ...")
        sys.exit()
    conf_files = sys.argv[1]


db_conf_path = os.path.join(conf_files, 'influxdb.conf') 
sites_f_path  = os.path.join(conf_files, 'sites.csv')
slice_f_path = os.path.join(conf_files, 'slice.csv')

# Create one Dataframe with all the geo-location information
sites_df = data_loader.get_geoloc_df(sites_f_path, slice_f_path)


logger.debug(sites_df)


############   Layout  #################
if public_metrics_site:
    url_base_pathname = '/latency/'  # MUST Change here for public metrics site
else:
    url_base_pathname = '/' 

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], url_base_pathname=url_base_pathname)

if public_metrics_site:
    app_server = app.server

# TODO: Move the style to CSS

controls = dbc.Card(
    [
        html.Div(
            [
                dbc.Label("Node 1"),
                dbc.Select(
                    id="src-node",
                    options=[
                        {"label": i, "value": i} for i in sites_df['site'].tolist()
                    ],
                    #value="STAR",
                ),
            ],
            style={'marginBottom': 2, 
                    'marginTop': 20, 
                    'marginLeft': 5, 
                    'marginRight':5},
        ),
        html.Div(
            [
                dbc.Label("Node 2"),
                dbc.Select(
                    id="dst-node",
                    options=[
                        {"label": i, "value": i} for i in sites_df['site'].tolist()
                    ],
                    #value="STAR",
                ),
            ],
            style={'marginBottom': 2, 
                    'marginTop': 20, 
                    'marginLeft': 5, 
                    'marginRight':5}
        ),
        html.Div(
            [
                dbc.Label("Duration"),
                dbc.Select(
                    id="duration2",
                    options=[
                        {"label": i, "value": i} for i in \
                        ['5 minutes', '15 minutes', '30 minutes', \
                         '1 hour', '3 hours', '6 hours', '12 hours', '24 hours']
                    ],
                    value="5 minutes",
                ),
            ],
            style={'marginBottom': 2, 
                    'marginTop': 20, 
                    'marginLeft': 5, 
                    'marginRight':5}
        ),
        html.Div(
            [
                dbc.Button("Submit", id='submit-button-state', 
                            n_clicks=0, outline=True, color="primary", className="me-md-2"),
                dbc.Button("Download CSV", id='btn-csv', 
                            n_clicks=0, outline=True, color="primary", className="me-md-2"),
                dcc.Download(id="download-csv"),
            ], 
            style={'marginBottom': 25, 
                    'marginTop': 20, 
                    'marginLeft': 10}
        ),
        #html.Div(
        #    [
        #        dbc.Button("Download CSV", id='btn-csv', 
        #                    n_clicks=0, outline=True, color="primary"),
        #        dcc.Download(id="download-csv"),
        #    ], 
        #    style={'marginBottom': 25, 
        #            'marginTop': 20, 
        #            'marginLeft': 10}
        #),
    ],
)


app.layout = dbc.Container(
    [
        html.H2("FABRIC Latency Monitor"),
        html.Hr(),
        dbc.Row(
                
            [
                dbc.Col(dcc.Graph(id='map-fig'), lg=8),
                dbc.Col(controls, lg=4),
            ],
            align="center",
        ),
        dbc.Row(dcc.Graph(id='single-latency-fwd')),
        dbc.Row(dcc.Graph(id='single-latency-rev')),
    ],
    fluid=True,
)


########## Callbacks #########


@callback(
    Output('single-latency-fwd', 'figure'),
    Output('single-latency-rev', 'figure'),
    Output('map-fig', 'figure'),
    Input('submit-button-state', 'n_clicks'),
    State('src-node', 'value'),
    State('dst-node', 'value'), 
    State('duration2', 'value'), prevent_initial_call=True)
def update_figure(n, src, dst, duration):
    '''
    Returns 3  graph figures
    '''
    #### Line graphs #####

    src_ip = sites_df.loc[sites_df['site'].str.contains(src), 'ip_address'].item()
    dst_ip = sites_df.loc[sites_df['site'].str.contains(dst), 'ip_address'].item()

    # debugging
    logger.debug("%s %s", src_ip, dst_ip)

    # Forward graph data
    if influxdb_version == 'v3':
        latency_fwd = data_loader.download_influx_data(
                            conf_path=db_conf_path, 
                            duration=duration, 
                            outfile=None,
                            src_dst=(src_ip, dst_ip))
    elif influxdb_version == 'v2':
        latency_fwd = data_loader.download_influx_data_local(
                            conf_path=db_conf_path,
                            duration=duration, 
                            outfile=None,
                            src_dst=(src_ip, dst_ip))

    logger.debug(latency_fwd)
    line_fig_fwd = graph.generate_line_graph(sites_df, src, dst, latency_fwd)

    # Reverse graph data
    if influxdb_version == 'v3':
        latency_rev = data_loader.download_influx_data(
                            conf_path=db_conf_path, 
                            duration=duration, 
                            outfile=None,
                            src_dst=(dst_ip, src_ip))

    elif influxdb_version == 'v2':
        latency_rev = data_loader.download_influx_data_local(
                            conf_path=db_conf_path,
                            duration=duration, 
                            outfile=None,
                            src_dst=(dst_ip, src_ip))

    logger.debug(latency_rev)
    line_fig_rev = graph.generate_line_graph(sites_df, dst, src, latency_rev)


    #####  Map graph ######
    map_fig = graph.generate_map(sites_df, src, dst)

    return line_fig_fwd, line_fig_rev, map_fig



@callback(
    Output("download-csv", "data"),
    Input("btn-csv", "n_clicks"),
    State('src-node', 'value'),
    State('dst-node', 'value'), 
    State('duration2', 'value'), prevent_initial_call=True)
def download_fwd_data(n_clicks, src, dst, duration):

    src_ip = sites_df.loc[sites_df['site'].str.contains(src), 'ip_address'].item()
    dst_ip = sites_df.loc[sites_df['site'].str.contains(dst), 'ip_address'].item()

    # Forward graph data
    if influxdb_version == 'v3':
        latency_fwd = data_loader.download_influx_data(
                            conf_path=db_conf_path, 
                            duration=duration, 
                            outfile=None,
                            src_dst=(src_ip, dst_ip))
    elif influxdb_version == 'v2':
        latency_fwd = data_loader.download_influx_data_local(
                            conf_path=db_conf_path,
                            duration=duration, 
                            outfile=None,
                            src_dst=(src_ip, dst_ip))


    # Reverse graph data
    if influxdb_version == 'v3':
        latency_rev = data_loader.download_influx_data(
                            conf_path=db_conf_path, 
                            duration=duration, 
                            outfile=None,
                            src_dst=(dst_ip, src_ip))

    elif influxdb_version == 'v2':
        latency_rev = data_loader.download_influx_data_local(
                            conf_path=db_conf_path,
                            duration=duration, 
                            outfile=None,
                            src_dst=(dst_ip, src_ip))

   
    latency_df = pd.concat([latency_fwd, latency_rev], ignore_index=True)
    logger.debug(latency_df)
    
    return dcc.send_data_frame(latency_df.to_csv, "latency.csv", index=False)
    


if __name__ == "__main__":
    if public_metrics_site:
        app.run(host='0.0.0.0',debug=False, use_reloader=False)
    else:
        app.run_server(debug=False, use_reloader=False)
   

