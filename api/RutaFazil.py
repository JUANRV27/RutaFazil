import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

# Cargar datos
try:
    nodes_ids_df = pd.read_csv('lima_streets_nodes.csv')  # Datos de los nodos con id
    nodes_types_df = pd.read_csv('lima_streets_nodes_classified.csv')  # Datos de los nodos con tipo
    edges_df = pd.read_csv('lima_streets_edges_2.csv')  # Datos de las aristas
except FileNotFoundError as e:
    print(f"Error al cargar los datos: {e}")
    raise

# Asegúrate de que la columna 'type' existe y asigna un valor por defecto en caso de que falte
nodes_ids_df['type'] = nodes_types_df['type'].fillna('desconocido')

# Crear grafo y clasificar nodos principales
G = nx.Graph()

# Agregar nodos al grafo con el atributo 'type' y posición
for _, row in nodes_ids_df.iterrows():
    G.add_node(row['node_id'], pos=(row['x'], row['y']), type=row['type'])

# Agregar aristas al grafo con la distancia como peso
for _, row in edges_df.iterrows():
    G.add_edge(row['u'], row['v'], weight=row['length'])

# Extraer posiciones de nodos para usarlas en los gráficos
pos = nx.get_node_attributes(G, 'pos')

# Filtrar nodos según su tipo
x_nodes_main = [pos[n][0] for n in G.nodes() if G.nodes[n].get('type') == 'principal']
y_nodes_main = [pos[n][1] for n in G.nodes() if G.nodes[n].get('type') == 'principal']
x_nodes_secondary = [pos[n][0] for n in G.nodes() if G.nodes[n].get('type') == 'secundario']
y_nodes_secondary = [pos[n][1] for n in G.nodes() if G.nodes[n].get('type') == 'secundario']

# Crear las capas de trazado de nodos principales y secundarios
main_nodes_trace = go.Scattermapbox(
    mode='markers',
    lon=x_nodes_main,
    lat=y_nodes_main,
    marker=dict(size=10, color='blue'),
    text=[n for n in G.nodes if G.nodes[n].get('type') == 'principal'],
    hoverinfo='text',
    name="Nodos Principales"
)

secondary_nodes_trace = go.Scattermapbox(
    mode='markers',
    lon=x_nodes_secondary,
    lat=y_nodes_secondary,
    marker=dict(size=6, color='green'),
    text=[n for n in G.nodes if G.nodes[n].get('type') == 'secundario'],
    hoverinfo='text',
    name="Nodos Secundarios"
)

# Crear la aplicación Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout de la aplicación con opciones de selección y el toggle de grafo completo
app.layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("Visualización del Grafo de Calles de Lima"), width=12, className="container")
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id='map-graph', config={'scrollZoom': True}), width=12, className="graph-container")
        ]),

        dbc.Row([

            dbc.Col(html.Div([
                html.Label("Selecciona el nodo de inicio:"), 
                dcc.Dropdown(
                    id='start-node', 
                    options=[{'label': str(node), 'value': node} for node in G.nodes], 
                    placeholder="Selecciona el nodo de inicio"
                )
            ], className="dropdown-container"), width=6),

            dbc.Col(html.Div([
                html.Label("Selecciona el nodo de destino:", className="node-label"),
                dcc.Dropdown(
                    id='end-node', 
                    options=[{'label': str(node), 'value': node} for node in G.nodes],
                    placeholder="Selecciona el nodo de destino" 
                )
            ], className="dropdown-container"), width=6)
        ], className="row"),

        dbc.Row([
            dbc.Col(dcc.Checklist(
                id='toggle-graph',
                options=[{'label': 'Mostrar grafo completo', 'value': 'show_graph'}],
                value=[],
                inline=True,
            ), width=12, className="container")
        ]),

        dbc.Row([
            dbc.Col(dcc.Graph(id='shortest-path-graph', config={'scrollZoom': True}), width=12, className="graph-container")
        ])
    ])
])

# Callback para calcular el camino más corto y actualizar los gráficos
@app.callback(
    Output('map-graph', 'figure'),
    [Input('toggle-graph', 'value')],
    [Input('map-graph', 'relayoutData')]
)
def update_map(toggle_value, relayout_data):
    """
    Callback para actualizar el mapa de nodos según el toggle y el nivel de zoom/movimiento del mapa.
    """
    # Configuración inicial: usar valores por defecto si no hay interacción
    zoom_level = 10
    center = dict(lon=-77.03, lat=-12.04)

    # Actualizar con relayoutData si disponible
    if relayout_data is not None:
        zoom_level = relayout_data.get('mapbox.zoom', zoom_level)
        center = relayout_data.get('mapbox.center', center)

    # Mostrar nodos principales y secundarios según el toggle
    data_main = []
    if 'show_graph' in toggle_value:
        data_main = [main_nodes_trace, secondary_nodes_trace]  # Ambos nodos
    else:
        data_main = [main_nodes_trace]  # Solo secundarios (por defecto)

    # Construir el gráfico
    fig_main = go.Figure(
        data=data_main,
        layout=go.Layout(
            title='Mapa de Calles de Lima',
            mapbox=dict(
                style="open-street-map",
                center=center,
                zoom=zoom_level
            ),
            margin=dict(b=0, l=0, r=0, t=40)
        )
    )

    return fig_main


@app.callback(
    Output('shortest-path-graph', 'figure'),
    [Input('start-node', 'value'),
     Input('end-node', 'value')]
)
def update_shortest_path(start_node, end_node):
    if start_node is None or end_node is None:
        return go.Figure(
            layout=go.Layout(
                title='Camino Más Corto',
                mapbox=dict(
                    style="open-street-map",
                    center=dict(lon=-77.03, lat=-12.04),
                    zoom=12
                ),
                margin=dict(b=0, l=0, r=0, t=40)
            )
        )

    try:
        shortest_path = nx.shortest_path(G, source=start_node, target=end_node, weight='weight')
        path_x = [pos[node][0] for node in shortest_path]
        path_y = [pos[node][1] for node in shortest_path]

        path_trace = go.Scattermapbox(
            mode='markers+lines',
            lon=path_x,
            lat=path_y,
            line=dict(width=4, color='red'),
            marker=dict(size=10, color='red'),
            text=shortest_path,
            hoverinfo='text',
            name='Camino Más Corto'
        )

        return go.Figure(
            data=[path_trace],
            layout=go.Layout(
                title='Camino Más Corto',
                mapbox=dict(
                    style="open-street-map",
                    center=dict(
                        lon=path_x[len(path_x) // 2],
                        lat=path_y[len(path_y) // 2]
                    ),
                    zoom=14
                ),
                margin=dict(b=0, l=0, r=0, t=40)
            )
        )
    except nx.NetworkXNoPath:
        return go.Figure(
            layout=go.Layout(
                title='Camino Más Corto (No hay conexión)',
                mapbox=dict(
                    style="open-street-map",
                    center=dict(lon=-77.03, lat=-12.04),
                    zoom=12
                ),
                margin=dict(b=0, l=0, r=0, t=40)
            )
        )

if __name__ == '__main__':
    app.run_server(debug=True)
