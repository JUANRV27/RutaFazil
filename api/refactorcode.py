import dash
from dash import dcc, html, Input, Output, State, ctx
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import networkx as nx
from flask import Flask
from process_data import load_data


# ---------------- SERVER ----------------

server = Flask(__name__)

# ---------------- DATA ----------------

DATA = load_data()

G = nx.Graph()
NODES = {}
NODE_LONS, NODE_LATS, NODE_IDS = [], [], []

if "error" not in DATA:
    NODES = DATA["nodes"]

    for node_id, pos in NODES.items():
        node_id = str(node_id)
        G.add_node(node_id, pos=pos)
        NODE_LONS.append(pos[0])
        NODE_LATS.append(pos[1])
        NODE_IDS.append(node_id)

    for edge in DATA["edges"]:
        G.add_edge(str(edge['u']), str(edge['v']), weight=edge['length'])

# Centro dinámico
CENTER = dict(lon=-77.03, lat=-12.04)
if NODE_LONS and NODE_LATS:
    CENTER = dict(
        lon=sum(NODE_LONS) / len(NODE_LONS),
        lat=sum(NODE_LATS) / len(NODE_LATS)
    )

# ---------------- LOGIC ----------------

def calculate_route(start, end):
    path = nx.shortest_path(G, source=start, target=end, weight='weight')
    dist = nx.shortest_path_length(G, source=start, target=end, weight='weight')
    return path, dist


def build_base_map():
    return go.Scattermapbox(
        mode='markers',
        lon=NODE_LONS,
        lat=NODE_LATS,
        marker=dict(size=4, opacity=0.0, color="gray"),
        hovertemplate="Nodo %{text}<extra></extra>",
        text=NODE_IDS
    )


def marker_trace(node_id, color, label):
    return go.Scattermapbox(
        mode='markers+text',
        lon=[NODES[node_id][0]],
        lat=[NODES[node_id][1]],
        marker=dict(size=24, color=color),
        text=[label],
        textposition="middle center"
    )


def build_route_traces(path):
    p_lon = [NODES[n][0] for n in path]
    p_lat = [NODES[n][1] for n in path]

    return [
        go.Scattermapbox(
            mode='lines',
            lon=p_lon, lat=p_lat,
            line=dict(width=10, color='rgba(56,189,248,0.2)'),
            hoverinfo='skip'
        ),
        go.Scattermapbox(
            mode='lines',
            lon=p_lon, lat=p_lat,
            line=dict(width=4, color='#38bdf8')
        )
    ]


def build_result_panel(dist):
    return html.Div([
        html.Hr(),
        html.H5("Métricas de Viaje"),
        html.P(f"Distancia: {dist/1000:.2f} km"),
        html.P(f"Tiempo estimado: {max(1, int(dist/450))} min")
    ])

# ---------------- OPTIONS ----------------

MAX_NODES = 2500
opts = [{'label': f"Nodo {i}", 'value': i} for i in NODE_IDS[:MAX_NODES]]

# ---------------- UI ----------------

def create_sidebar():
    return html.Div([
        html.H2("🗺️ Ruta Fazil"),

        html.Label("Origen"),
        dcc.Dropdown(id='start-node', options=opts, placeholder="Selecciona origen"),

        html.Label("Destino"),
        dcc.Dropdown(id='end-node', options=opts, placeholder="Selecciona destino"),

        dbc.Button("Calcular Ruta", id='btn-calculate', color="primary"),
        dbc.Button("Limpiar", id='btn-clear', color="secondary", outline=True),

        html.Div(id="route-info")

    ], className="sidebar")


def create_map():
    return html.Div([
        dcc.Graph(
            id='map-graph',
            figure=go.Figure(
                data=[build_base_map()],
                layout=go.Layout(
                    mapbox=dict(
                        style="open-street-map",
                        center=CENTER,
                        zoom=13
                    ),
                    margin=dict(b=0, l=0, r=0, t=0),
                )
            ),
            style={'height': '100vh'},
            config={
                'displayModeBar': False,
                'scrollZoom': True
            }
        )
    ], className="map-area")

# ---------------- CALLBACKS ----------------

def register_callbacks(app):

    # 🔹 Selección por click
    @app.callback(
        Output('start-node', 'value'),
        Output('end-node', 'value'),
        Input('map-graph', 'clickData'),
        Input('btn-clear', 'n_clicks'),
        State('start-node', 'value'),
        State('end-node', 'value'),
        prevent_initial_call=True
    )
    def manage_selection(clickData, clear_clicks, start_val, end_val):

        if ctx.triggered_id == 'btn-clear':
            return None, None

        if ctx.triggered_id == 'map-graph' and clickData:
            point = clickData['points'][0]
            node_id = str(point.get('text'))

            if start_val is None:
                return node_id, end_val

            elif end_val is None:
                return start_val, node_id

            else:
                return node_id, None

        return start_val, end_val


    # 🔹 Render mapa + ruta
    @app.callback(
        Output('map-graph', 'figure'),
        Output('route-info', 'children'),
        Input('start-node', 'value'),
        Input('end-node', 'value'),
        Input('btn-calculate', 'n_clicks'),
        prevent_initial_call=True
    )
    def refresh_map(start_node, end_node, n_clicks):

        traces = [build_base_map()]
        result_panel = html.P("Selecciona origen y destino")

        if start_node and start_node in NODES:
            traces.append(marker_trace(start_node, "green", "START"))

        if end_node and end_node in NODES:
            traces.append(marker_trace(end_node, "red", "END"))

        if start_node and end_node:
            try:
                path, dist = calculate_route(start_node, end_node)
                traces.extend(build_route_traces(path))
                result_panel = build_result_panel(dist)
            except:
                result_panel = dbc.Alert("No hay ruta disponible", color="warning")

        fig = go.Figure(
            data=traces,
            layout=go.Layout(
                mapbox=dict(
                    style="open-street-map",
                    center=CENTER,
                    zoom=13
                ),
                margin=dict(b=0, l=0, r=0, t=0),
                uirevision=True
            )
        )

        return fig, result_panel

# ---------------- APP ----------------

def create_dash_app():
    app = dash.Dash(
        __name__,
        server=server,
        external_stylesheets=[
            dbc.themes.DARKLY,
            "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap"
        ]
    )

    app.layout = html.Div([
        create_sidebar(),
        create_map()
    ], className="main-container")

    register_callbacks(app)

    return app

# ---------------- RUN ----------------

dash_app = create_dash_app()
app = server

if __name__ == '__main__':
    dash_app.run_server(debug=True)
