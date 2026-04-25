import os
import pandas as pd
import networkx as nx
import json
from http.server import BaseHTTPRequestHandler

# Ruta a los archivos CSV
def load_data():
    current_dir = os.path.dirname(__file__)
    data_dir = os.path.join(current_dir, '..', 'data')
    
    lima_streets_nodes = os.path.join(data_dir, 'lima_streets_nodes.csv')
    lima_streets_nodes_classified = os.path.join(data_dir, 'lima_streets_nodes_classified.csv')
    lima_streets_edges_2 = os.path.join(data_dir, 'lima_streets_edges_2.csv')

    try:
        nodes_ids_df = pd.read_csv(lima_streets_nodes)
        nodes_types_df = pd.read_csv(lima_streets_nodes_classified)
        edges_df = pd.read_csv(lima_streets_edges_2)
        
        nodes_df = pd.merge(nodes_ids_df, nodes_types_df, on=['x', 'y'], how='left')
        nodes_df['type'] = nodes_df['type'].fillna('desconocido')
        
        # Guardar posiciones con llaves de tipo STRING para evitar conflictos de tipos en JSON/Dash
        pos = {str(row['node_id']): (row['x'], row['y']) for _, row in nodes_df.iterrows()}
        
        return {
            "nodes": pos, 
            "edges": edges_df.to_dict(orient='records'), 
            "message": "Datos cargados correctamente"
        }
    except Exception as e:
        return {"error": f"Error al cargar los datos: {str(e)}"}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = load_data()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
