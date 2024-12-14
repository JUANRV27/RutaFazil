import os
import pandas as pd
import networkx as nx
import json

# Ruta a los archivos CSV
def load_data():
    current_dir = os.path.dirname(__file__)
    lima_streets_nodes = os.path.join(current_dir, '..', 'data', 'lima_streets_nodes.csv')
    lima_streets_nodes_classified = os.path.join(current_dir, '..', 'data', 'lima_streets_nodes_classified.csv')
    lima_streets_edges_2 = os.path.join(current_dir, '..', 'data', 'lima_streets_edges_2.csv')

    try:
        # Cargar los CSV
        nodes_ids_df = pd.read_csv(lima_streets_nodes)
        nodes_types_df = pd.read_csv(lima_streets_nodes_classified)
        edges_df = pd.read_csv(lima_streets_edges_2)
    except FileNotFoundError as e:
        return {"error": f"Error al cargar los datos: {e}"}

    # Asegúrate de que la columna 'type' existe y asigna un valor por defecto en caso de que falte
    nodes_ids_df['type'] = nodes_types_df['type'].fillna('desconocido')

    # Crear el grafo de NetworkX
    G = nx.Graph()

    # Agregar nodos y aristas al grafo
    for _, row in nodes_ids_df.iterrows():
        G.add_node(row['node_id'], pos=(row['x'], row['y']), type=row['type'])

    for _, row in edges_df.iterrows():
        G.add_edge(row['u'], row['v'], weight=row['length'])

    # Retornar los datos necesarios para Dash en formato JSON
    pos = nx.get_node_attributes(G, 'pos')
    return {"nodes": pos, "edges": edges_df.to_dict(orient='records'), "message": "Datos cargados correctamente"}

def handler(request):
    # Aquí podrías manejar la solicitud de obtener los datos
    data = load_data()
    return json.dumps(data)
