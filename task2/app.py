import os
import json
import redis
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

REDIS_HOST = os.getenv("REDIS_HOST", "192.168.121.187")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_OUTPUT_KEY = os.getenv("REDIS_OUTPUT_KEY", "jeanevangelista-proj3-output")

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Plotly Dash - VM Monitoring"

app.layout = dbc.Container([
    html.H1("Serverless VM Monitoring Dashboard", className="my-3"),

    html.Div([
        html.P(f"Reading data from Redis: {REDIS_HOST}:{REDIS_PORT}, key={REDIS_OUTPUT_KEY}",
               style={"fontStyle": "italic"})
    ]),

    html.Div(id='status-msg', className="text-info mb-2"),

    dcc.Interval(
        id='interval-component',
        interval=10 * 1000,
        n_intervals=0
    ),

    dbc.Row([
        dbc.Col([
            html.H4("Network Egress (%)"),
            html.Div(id='network-egress', className="display-4 text-primary")
        ], width=3),
        dbc.Col([
            html.H4("Memory Cache (%)"),
            html.Div(id='memory-cache', className="display-4 text-success")
        ], width=3),
    ], className="my-2"),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id='cpu-chart')
        ], width=12)
    ]),

    dbc.Row([
        dbc.Col([
            html.H5("Raw Data from Redis"),
            html.Pre(id='raw-data', style={
                "backgroundColor": "#f8f9fa",
                "padding": "10px",
                "border": "1px solid #ddd"
            })
        ])
    ])
], fluid=True)


@app.callback(
    [
        Output('network-egress', 'children'),
        Output('memory-cache', 'children'),
        Output('cpu-chart', 'figure'),
        Output('raw-data', 'children'),
        Output('status-msg', 'children'),
    ],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    data_json = r.get(REDIS_OUTPUT_KEY)
    if not data_json:
        return (
            "N/A",
            "N/A",
            go.Figure(),
            "No data found in Redis.",
            "Waiting for serverless function output..."
        )

    try:
        data_dict = json.loads(data_json)
    except json.JSONDecodeError:
        return (
            "N/A",
            "N/A",
            go.Figure(),
            "Invalid JSON in Redis.",
            "Data parse error."
        )

    net_egress_val = data_dict.get("percent-network-egress", None)
    mem_cache_val = data_dict.get("percent-memory-cache", None)

    if isinstance(net_egress_val, (int, float)):
        net_egress_str = f"{net_egress_val:.2f}"
    else:
        net_egress_str = "N/A"

    if isinstance(mem_cache_val, (int, float)):
        mem_cache_str = f"{mem_cache_val:.2f}"
    else:
        mem_cache_str = "N/A"

    cpu_keys = [k for k in data_dict.keys() if k.startswith("avg-util-cpu")]
    x_vals = []
    y_vals = []
    for ck in sorted(cpu_keys):
        cpu_number = ck.split('-')[2]
        x_vals.append(cpu_number)
        y_vals.append(data_dict[ck])

    cpu_fig = go.Figure()
    if x_vals and y_vals:
        cpu_fig.add_trace(go.Bar(
            x=x_vals,
            y=y_vals,
            marker_color='blue'
        ))
        cpu_fig.update_layout(
            title="CPU 60-sec Moving Averages (%)",
            xaxis_title="CPU",
            yaxis_title="Usage (%)",
            yaxis_range=[0, 100]
        )

    raw_text = json.dumps(data_dict, indent=2)

    status_message = f"Last updated from Redis key: {REDIS_OUTPUT_KEY}"

    return (
        net_egress_str,
        mem_cache_str,
        cpu_fig,
        raw_text,
        status_message
    )

server = app.server
if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8501)
