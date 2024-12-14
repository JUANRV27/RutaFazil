import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import networkx as nx
import requests
import json

# Función para crear la aplicación Dash
def create_dash_app():
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    # Definir el layout de tu aplicación Dash
    app.layout = html.Div([
        dbc.Container([
            dbc.Row([dbc.Col(html.H1("Visualización del Grafo de Calles de Lima"))]),
            dbc.Row([dbc.Col(dcc.Graph(id='map-graph'))]),
            dbc.Row([
                dbc.Col(dcc.Dropdown(
                    id='start-node',
                    options=[],  # Se llenará dinámicamente
                    placeholder="Selecciona el nodo de inicio"
                )),
                dbc.Col(dcc.Dropdown(
                    id='end-node',
                    options=[],  # Se llenará dinámicamente
                    placeholder="Selecciona el nodo de destino"
                ))
            ]),
        ])
    ])

    # Callback para cargar los datos desde el endpoint de Vercel
    @app.callback(
        Output('map-graph', 'figure'),
        [Input('start-node', 'value'),
         Input('end-node', 'value')]
    )
    def update_graph(start_node, end_node):
        # Llamada al endpoint de datos
        response = requests.get("https://ruta-fazil.vercel.app/api/process_data")
        data = response.json()  # Obtener los datos procesados de Vercel

        nodes = data["nodes"]
        edges = data["edges"]

        # Crear grafo de NetworkX a partir de los datos
        G = nx.Graph()
        for node, position in nodes.items():
            G.add_node(node, pos=position)

        for edge in edges:
            G.add_edge(edge['u'], edge['v'], weight=edge['length'])

        # Crear el gráfico
        pos = nx.get_node_attributes(G, 'pos')
        x_nodes = [pos[node][0] for node in G.nodes()]
        y_nodes = [pos[node][1] for node in G.nodes()]

        trace = go.Scattermapbox(
            mode='markers',
            lon=x_nodes,
            lat=y_nodes,
            marker=dict(size=10, color='blue'),
            text=[node for node in G.nodes()],
            hoverinfo='text',
            name="Nodos"
        )

        fig = go.Figure(
            data=[trace],
            layout=go.Layout(
                title='Mapa de Calles de Lima',
                mapbox=dict(
                    style="open-street-map",
                    center=dict(lon=-77.03, lat=-12.04),
                    zoom=10
                ),
                margin=dict(b=0, l=0, r=0, t=40)
            )
        )

        return fig

    return app

# Función que maneja la solicitud en Vercel y retorna la aplicación Dash
def handler(request):
    app = create_dash_app()
    return app.server  # Retorna el servidor de la aplicación Dash

