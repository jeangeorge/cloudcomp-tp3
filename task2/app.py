import os
import json
import redis
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import datetime

REDIS_HOST = os.getenv("REDIS_HOST", "192.168.121.187")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_OUTPUT_KEY = os.getenv("REDIS_OUTPUT_KEY", "jeanevangelista-proj3-output")
INTERVAL_SECONDS = 5 * 1000  # 10 seconds

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
cpu_history = {}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Project 3: Serverless Computing and Monitoring Dashboard"

def create_header():
    return html.H1("Project 3: Serverless Computing and Monitoring Dashboard", className="my-3")

def create_status():
    return html.Div(id="status-msg", className="text-info mb-2")

def create_interval_component():
    return dcc.Interval(id="interval-component", interval=INTERVAL_SECONDS, n_intervals=0)

def create_metrics_row():
    return dbc.Row([
        dbc.Col([html.H4("Outgoing Traffic Bytes (%)"), html.Div(id="network-egress", className="display-4 text-primary")], width=3),
        dbc.Col([html.H4("Memory Caching Content (%)"), html.Div(id="memory-cache", className="display-4 text-success")], width=3),
    ], className="my-2")

def create_charts_row():
    return dbc.Row([
        dbc.Col([dcc.Graph(id="cpu-line-chart")], width=12),
        dbc.Col([dcc.Graph(id="cpu-chart")], width=12),
    ])

def create_raw_data_block():
    return dbc.Row([
        dbc.Col([
            html.H5("Raw Data from Redis"),
            html.Pre(id="raw-data", style={
                "backgroundColor": "#f8f9fa",
                "padding": "10px",
                "border": "1px solid #ddd"
            })
        ])
    ])

app.layout = dbc.Container([
    create_header(),
    html.Div([html.P(f"Reading data from Redis: {REDIS_HOST}:{REDIS_PORT}, key={REDIS_OUTPUT_KEY}", style={"fontStyle": "italic"})]),
    create_status(),
    create_interval_component(),
    create_metrics_row(),
    create_charts_row(),
    create_raw_data_block(),
], fluid=True)

def fetch_data_from_redis():
    data_json = r.get(REDIS_OUTPUT_KEY)
    return json.loads(data_json) if data_json else None

def calculate_chart_y_range(values, padding=5):
    if not values:
        return [0, 100]
    return [max(0, min(values) - padding), max(values) + padding]

def build_bar_chart(cpu_data):
    x_vals = [f"cpu{cpu_num}" for cpu_num, _ in cpu_data]
    y_vals = [val for _, val in cpu_data]
    y_range = calculate_chart_y_range(y_vals)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=x_vals, y=y_vals, marker_color="blue"))
    fig.update_layout(
        title="CPU Moving Averages over the Last Minute (%)",
        xaxis_title="CPU",
        yaxis_title="Usage (%)",
        yaxis_range=y_range
    )
    return fig

def build_line_chart():
    global cpu_history
    all_values = []
    fig = go.Figure()
    for label in sorted(cpu_history.keys()):
        times = [pt[0] for pt in cpu_history[label]]
        values = [pt[1] for pt in cpu_history[label]]
        all_values.extend(values)
        fig.add_trace(go.Scatter(x=times, y=values, mode="lines", name=label))
    y_range = calculate_chart_y_range(all_values)
    fig.update_layout(
        title="CPU Usage Over Time",
        xaxis_title="Timestamp",
        yaxis_title="Usage (%)",
        yaxis_range=y_range
    )
    return fig

def append_to_cpu_history(cpu_data, timestamp):
    global cpu_history
    for cpu_num, usage_val in cpu_data:
        label = f"cpu{cpu_num}"
        if label not in cpu_history:
            cpu_history[label] = []
        cpu_history[label].append((timestamp, usage_val))

@app.callback(
    [
        Output("network-egress", "children"),
        Output("memory-cache", "children"),
        Output("cpu-chart", "figure"),
        Output("cpu-line-chart", "figure"),
        Output("raw-data", "children"),
        Output("status-msg", "children"),
    ],
    [Input("interval-component", "n_intervals")]
)
def update_dashboard(n):
    data_dict = fetch_data_from_redis()
    if not data_dict:
        return (
            "N/A", "N/A", go.Figure(), go.Figure(),
            "No data found in Redis.", "Waiting for serverless function output..."
        )

    network_egress = f"{data_dict.get('percent-network-egress', 0.0):.2f}"
    memory_cache = f"{data_dict.get('percent-memory-cache', 0.0):.2f}"

    cpu_keys = [k for k in data_dict.keys() if k.startswith("avg-util-cpu")]
    cpu_data = [(int(k.split('-')[2][3:]), data_dict[k]) for k in cpu_keys]
    cpu_data.sort(key=lambda x: x[0])

    timestamp = datetime.datetime.fromisoformat(data_dict.get("timestamp", datetime.datetime.now().isoformat()).replace("Z", ""))
    append_to_cpu_history(cpu_data, timestamp)

    bar_chart = build_bar_chart(cpu_data)
    line_chart = build_line_chart()
    raw_data = json.dumps(data_dict, indent=2)
    status_message = f"Last updated from Redis key: {REDIS_OUTPUT_KEY}"

    return network_egress, memory_cache, bar_chart, line_chart, raw_data, status_message

server = app.server

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8501)
