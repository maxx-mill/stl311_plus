"""
GeoServer client service for St. Louis 311 Service Integration.
Handles publishing spatial data to GeoServer for web mapping services.
"""

import requests
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class GeoServerClient:
    """
    Professional GeoServer client for publishing spatial data.
    Handles workspace, datastore, and layer management.
    """
    
    def __init__(self):
        self.base_url = os.getenv('GEOSERVER_URL', 'http://localhost:8080/geoserver')
        self.username = os.getenv('GEOSERVER_USERNAME', 'admin')
        self.password = os.getenv('GEOSERVER_PASSWORD', 'geoserver')
        self.workspace = os.getenv('GEOSERVER_WORKSPACE', 'stl311')
        self.namespace = os.getenv('GEOSERVER_NAMESPACE', 'http://stl311.org')
        
        # Session for authenticated requests
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def test_connection(self):
        """
        Test the GeoServer connection.
        """
        try:
            response = self.session.get(f"{self.base_url}/rest/about/status")
            response.raise_for_status()
            return {
                'status': 'success',
                'message': 'GeoServer connection successful',
                'version': response.json().get('about', {}).get('resource', {}).get('version')
            }
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'message': f'GeoServer connection failed: {e}'
            }
    
    def create_workspace(self):
        """
        Create a workspace in GeoServer if it doesn't exist.
        """
        try:
            # Check if workspace exists
            response = self.session.get(f"{self.base_url}/rest/workspaces/{self.workspace}")
            if response.status_code == 200:
                logger.info(f"Workspace {self.workspace} already exists")
                return {'status': 'success', 'message': 'Workspace already exists'}
            
            # Create workspace
            workspace_data = {
                "workspace": {
                    "name": self.workspace
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/rest/workspaces",
                json=workspace_data
            )
            response.raise_for_status()
            
            logger.info(f"Created workspace: {self.workspace}")
            return {'status': 'success', 'message': 'Workspace created'}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating workspace: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def create_postgis_datastore(self, datastore_name, database_config):
        """
        Create a PostGIS datastore in GeoServer.
        """
        try:
            # Create workspace first
            workspace_result = self.create_workspace()
            if workspace_result['status'] != 'success':
                return workspace_result
            
            # Check if datastore exists
            response = self.session.get(
                f"{self.base_url}/rest/workspaces/{self.workspace}/datastores/{datastore_name}"
            )
            if response.status_code == 200:
                logger.info(f"Datastore {datastore_name} already exists")
                return {'status': 'success', 'message': 'Datastore already exists'}
            
            # Create datastore
            datastore_data = {
                "dataStore": {
                    "name": datastore_name,
                    "type": "PostGIS",
                    "enabled": True,
                    "connectionParameters": {
                        "entry": [
                            {"@key": "host", "$": database_config.get('host', 'localhost')},
                            {"@key": "port", "$": str(database_config.get('port', 5432))},
                            {"@key": "database", "$": database_config.get('database', 'stl311_db')},
                            {"@key": "schema", "$": database_config.get('schema', 'public')},
                            {"@key": "user", "$": database_config.get('username', 'postgres')},
                            {"@key": "passwd", "$": database_config.get('password', 'password')},
                            {"@key": "dbtype", "$": "postgis"}
                        ]
                    }
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/rest/workspaces/{self.workspace}/datastores",
                json=datastore_data
            )
            response.raise_for_status()
            
            logger.info(f"Created PostGIS datastore: {datastore_name}")
            return {'status': 'success', 'message': 'Datastore created'}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating datastore: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def publish_layer(self, layer_name, datastore_name='stl311_db'):
        """
        Publish a layer from PostGIS to GeoServer.
        """
        try:
            # Create workspace and datastore
            datastore_result = self.create_postgis_datastore(datastore_name, {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', 5432),
                'database': os.getenv('DB_NAME', 'stl311_db'),
                'username': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'password')
            })
            
            if datastore_result['status'] != 'success':
                return datastore_result
            
            # Check if layer already exists
            response = self.session.get(
                f"{self.base_url}/rest/layers/{layer_name}"
            )
            if response.status_code == 200:
                logger.info(f"Layer {layer_name} already exists")
                return {'status': 'success', 'message': 'Layer already exists'}
            
            # Publish layer
            layer_data = {
                "featureType": {
                    "name": layer_name,
                    "nativeName": "service_requests",
                    "title": "St. Louis 311 Service Requests",
                    "description": "Real-time 311 service requests for the City of St. Louis",
                    "enabled": True,
                    "srs": "EPSG:3857",
                    "nativeBoundingBox": {
                        "minx": -10060000,
                        "maxx": -10020000,
                        "miny": 4600000,
                        "maxy": 4700000,
                        "crs": "EPSG:3857"
                    },
                    "latLon": {
                        "minx": -90.4,
                        "maxx": -90.1,
                        "miny": 38.5,
                        "maxy": 38.8,
                        "crs": "EPSG:4326"
                    }
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/rest/workspaces/{self.workspace}/datastores/{datastore_name}/featuretypes",
                json=layer_data
            )
            response.raise_for_status()
            
            logger.info(f"Published layer: {layer_name}")
            return {
                'status': 'success',
                'message': 'Layer published successfully',
                'layer_name': layer_name,
                'wms_url': f"{self.base_url}/{self.workspace}/wms",
                'wfs_url': f"{self.base_url}/{self.workspace}/wfs"
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error publishing layer: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def update_layer_style(self, layer_name, style_name='point'):
        """
        Update the style for a published layer.
        """
        try:
            # Set default style
            style_data = {
                "layer": {
                    "defaultStyle": {
                        "name": style_name
                    }
                }
            }
            
            response = self.session.put(
                f"{self.base_url}/rest/layers/{layer_name}",
                json=style_data
            )
            response.raise_for_status()
            
            logger.info(f"Updated style for layer: {layer_name}")
            return {'status': 'success', 'message': 'Style updated'}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating layer style: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_layer_info(self, layer_name):
        """
        Get information about a published layer.
        """
        try:
            response = self.session.get(f"{self.base_url}/rest/layers/{layer_name}")
            response.raise_for_status()
            
            layer_info = response.json()
            return {
                'status': 'success',
                'layer_info': layer_info,
                'wms_url': f"{self.base_url}/{self.workspace}/wms",
                'wfs_url': f"{self.base_url}/{self.workspace}/wfs"
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting layer info: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def delete_layer(self, layer_name):
        """
        Delete a layer from GeoServer.
        """
        try:
            response = self.session.delete(f"{self.base_url}/rest/layers/{layer_name}")
            response.raise_for_status()
            
            logger.info(f"Deleted layer: {layer_name}")
            return {'status': 'success', 'message': 'Layer deleted'}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting layer: {e}")
            return {'status': 'error', 'message': str(e)} 