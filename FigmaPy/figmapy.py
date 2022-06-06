import requests
import json
from .models import *


class FigmaPy:
    def __init__(self, token, oauth2=False):
        self.api_uri = 'https://api.figma.com/v1/'
        self.token_uri = 'https://www.figma.com/oauth'
        self.api_token = token
        self.oauth2 = oauth2

    # -------------------------------------------------------------------------
    # FIGMA API
    # -------------------------------------------------------------------------
    '''
    Request Figma API
    '''
    def api_request(self, endpoint, method='get', payload=None):
        method = method.lower()

        if payload is None:
            payload = ''

        if self.oauth2:
            header = {'Authorization': 'Bearer {0}'.format(self.api_token)}
        else:
            header = {'X-Figma-Token': '{0}'.format(self.api_token)}

        header['Content-Type'] = 'application/json'

        try:
            if method == 'head':
                response = requests.head('{0}{1}'.format(self.api_uri, endpoint), headers=header)
            elif method == 'delete':
                response = requests.delete('{0}{1}'.format(self.api_uri, endpoint), headers=header)
            elif method == 'get':
                response = requests.get('{0}{1}'.format(self.api_uri, endpoint), headers=header, data=payload)
            elif method == 'options':
                response = requests.options('{0}{1}'.format(self.api_uri, endpoint), headers=header)
            elif method == 'post':
                response = requests.post('{0}{1}'.format(self.api_uri, endpoint), headers=header, data=payload)
            elif method == 'put':
                response = requests.put('{0}{1}'.format(self.api_uri, endpoint), headers=header, data=payload)
            else:
                response = None
            if response.status_code == 200:
                return json.loads(response.text)
            else:
                return None
        except (Exception, requests.HTTPError, requests.exceptions.SSLError) as e:
            print('Error occurred attpempting to make an api request. {0}'.format(e))
            return None

    # -------------------------------------------------------------------------
    # OAUTH2
    # -------------------------------------------------------------------------
    """
    Create token from client_id, client_secret, code
    """
    def create_token(self, client_id, client_secret, redirect_uri, code):
        payload = {
            'client_id': '{0}'.format(client_id),
            'client_secret': '{0}'.format(client_secret),
            'grant_type': 'authorization_code',
            'redirect_uri': '{0}'.format(redirect_uri),
            'code': '{0}'.format(code)
        }
        try:
            response = requests.post(self.token_uri, data=payload)
            print(response.text)
            if response.status_code == 200:
                token_data = json.loads(response.text)
                return [token_data['access_token'], token_data['expires_in']]
            else:
                return None
        except requests.HTTPError:
            print('HTTP Error occurred while trying to generate access token.')
            return None

    # -------------------------------------------------------------------------
    # SCOPE: FILES
    # -------------------------------------------------------------------------
    # https://www.figma.com/developers/api#get-files-endpoint
    def get_file(self, file_key, geometry=None, version=None):
        """
        Get the JSON file contents for a file.
        """
        optional_data = ''
        if geometry is not None or version is not None:
            optional_data = '?'
            if geometry is not None:
                optional_data += str(geometry)
                if version is not None:
                    optional_data += '&{0}'.format(str(version))
            elif version is not None:
                optional_data += str(version)

        data = self.api_request('files/{0}{1}'.format(file_key, optional_data), method='get')
        if data is not None:
            return File(data['name'], data['document'], data['components'], data['lastModified'], data['thumbnailUrl'],
                        data['schemaVersion'], data['styles'], file_key=file_key, pythonParent=self)

    # https://www.figma.com/developers/api#get-file-nodes-endpoint
    def get_file_nodes(self, file_key, ids, version=None, depth=None, geometry=None, plugin_data=None):
        """
        file_key: String, File to export JSON from
        ids: List of strings, A comma separated list of node IDs to retrieve and convert
        version: String, A specific version ID to get. Omitting this will get the current version of the file
        depth: Number, Positive integer representing how deep into the document tree to traverse. For example, setting this to 1 returns only Pages, setting it to 2 returns Pages and all top level objects on each page. Not setting this parameter returns all nodes
        geometry: String, Set to "paths" to export vector data
        plugin_data: String, A comma separated list of plugin IDs and/or the string "shared". Any data present in the document written by those plugins will be included in the result in the `pluginData` and `sharedPluginData` properties.
        """
        optional_data = ''
        if depth:
            optional_data += f'&depth={depth}'
        if version:
            optional_data += f'&version={version}'
        if geometry:
            optional_data += f'&geometry={geometry}'
        if plugin_data:
            optional_data += f'&plugin_data={plugin_data}'

        id_array = []
        for id in ids:
            id_array.append(id)
        id_list = ','.join(id_array)

        data = self.api_request(f'files/{file_key}/nodes?ids={id_list}{optional_data}', method='get')
        return data
        # get partial JSON, only relevant data for the node. includes parent data.
        # nodes data can be accessed with data['nodes']

     # https://www.figma.com/developers/api#get-images-endpoint
    def get_file_images(self, file_key, ids, scale=None, format=None, version=None):
        """
        Get urls for server-side rendered images from a file.
        If the node is not an image, a rasterized version of the node will be returned.
        """
        optional_data = ''
        if scale is not None or format is not None or version is not None:
            if scale is not None:
                optional_data += '&scale={0}'.format(str(scale))
            if format is not None:
                optional_data += '&format={0}'.format(str(format))
            if version is not None:
                optional_data += '&version={0}'.format(str(version))
        id_array = []
        for id in ids:
            id_array.append(id)
        id_list = ','.join(id_array)
        data = self.api_request('images/{0}?ids={1}{2}'.format(file_key, id_list, optional_data), method='get')
        if data is not None:
            return FileImages(data['images'], data['err'])

    # https://www.figma.com/developers/api#get-image-fills-endpoint
    def get_image_fills(self, file_key):
        """
        Get urls for source images from a file. a fill is a user provided image
        """
        data = self.api_request(f'files/{file_key}/images', method='get')
        if data is not None:
            return data

    """
    Get the version history of a file.
    """
    def get_file_versions(self, file_key):
        data = self.api_request('files/{0}/versions'.format(file_key), method='get')
        if data is not None:
            return FileVersions(data['versions'], data['pagination'])

    """
    Get all comments on a file.
    """
    def get_comments(self, file_key):
        data = self.api_request('files/{0}/comments'.format(file_key), method='get')
        if data is not None:
            return Comments(data['comments'])

    """
    Create a comment on a file.
    """
    def post_comment(self, file_key, message, client_meta=None):
        print(client_meta)
        if client_meta is not None:
            payload = '{{"message":"{0}","client_meta":{1}}}'.format(message.title(), client_meta)
        else:
            payload = "{{'message':'{0}'}}".format(message)
        data = self.api_request('files/{0}/comments'.format(file_key), method='post', payload=payload)
        if data is not None:
            return Comment(data['id'], data['file_key'], data['parent_id'], data['user'], data['created_at'],
                           data['resolved_at'], data['message'], data['client_meta'], data['order_id'])


    # -------------------------------------------------------------------------
    # SCOPE: TEAMS
    # -------------------------------------------------------------------------
    """
    Get all projects for a team
    """
    def get_team_projects(self, team_id):
        data = self.api_request('teams/{0}/projects'.format(team_id), method='get')
        if data is not None:
            return TeamProjects(data['projects'])

    # -------------------------------------------------------------------------
    # SCOPE: PROJECTS
    # -------------------------------------------------------------------------
    """
    Get all files for a project
    """
    def get_project_files(self, project_id):
        data = self.api_request('projects/{0}/files'.format(project_id))
        if data is not None:
            return ProjectFiles(data['files'])
