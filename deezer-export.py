# -*- coding: utf-8 -*-
""" Export your Deezer playlists as JSON

This module spins up a server to perform authentication to a
Deezer app (see Readme) through oauth2 protocol and then uses
the official Deezer API to retrieve
and save as JSON file all your playlists.
"""

import os
import time
import webbrowser
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import requests

APP_ID = os.environ.get("APP_ID")
APP_SECRET = os.environ.get("APP_SECRET")



def get_playlist(token, playlist_id):
    """
    Use Deezer API to get a playlist from its id.
    The only information returned about each playlist is the name and tracklist (a track is described
    by the name of the artist/band, the name of the album and the title.

    Args:
        token (string): The token given by Deezer to authenticate requests
        playlist_id (string): The id of the playlist to get

    Returns:
        A dictionary representing the playlist 
    """
    req = requests.get("https://api.deezer.com/playlist/{}&access_token={}".format(playlist_id, token))
    playlist_item = req.json()
    playlist = dict([('name', playlist_item['title']), ('songs', list())])
    for title in playlist_item['tracks']['data']:
        song = dict(
            [
                ('title', title['title']),
                ('artist', title['artist']['name']),
                ('album', title['album']['title'])
            ]
        )
        playlist['songs'].append(song)

    return playlist

def save_all_playlists(token):
    """
    Use Deezer API to get all user playlists and save each one in its own file as JSON.
    The only information saved about each playlist is the name and tracklist (a track is described
    by the name of the artist/band, the name of the album and the title.

    Args:
        token (string): The token given by Deezer to authenticate requests

    Returns:
        None
    """
    req = requests.get("https://api.deezer.com/user/me/playlists&access_token={}".format(token))
    playlists = list()

    for item_playlist in req.json()['data']:
        playlist_id = item_playlist['id']
        playlist = get_playlist(token, playlist_id)
        
        playlists.append(playlist)

    directory = 'playlists_{}'.format(time.time())
    if not os.path.exists(directory):
        os.makedirs(directory)

    for index, playlist in enumerate(playlists):
        filename = os.path.join(directory, '{}.json'.format(index))
        with open(filename, 'w') as file_descriptor:
            json.dump(playlist, file_descriptor)
            file_descriptor.close()


class Server(BaseHTTPRequestHandler):
    """Basic HTTP Server to serve as redirection URI and obtain the token from Deezer
    """
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):

        if self.path.startswith('/authfinish?code='):
            code = self.path.split('=')[1]
            print("Found code: {}".format(code))
            print('Attempting to obtain token...')
            endpoint = "https://connect.deezer.com" + \
            "/oauth/access_token.php?app_id={}&secret={}&code={}".format(APP_ID, APP_SECRET, code)

            print(endpoint)
            time.sleep(5)
            req = requests.get(endpoint)
            time.sleep(5)
            print(req.text)
            token = req.text.split('=')[1].split('&')[0]
            save_all_playlists(token)

        self._set_headers()
        self.wfile.write(
            "<html><body><h1>hi!</h1>" \
            "<script>alert('You can now close this page')</script></body></html>".encode()
        )

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        # Doesn't do anything with posted data
        self._set_headers()
        self.wfile.write("<html><body><h1>POST!</h1></body></html>".encode())

def run(port=7766):
    """ Run a HTTP server and listen
    Args:
        port (int): The port on which to listen. Should match the port in your Deezer app config.
    """
    server_address = ('', port)
    httpd = HTTPServer(server_address, Server)
    print('Starting httpd...')
    httpd.serve_forever()


if __name__ == "__main__":

    if not APP_ID or not APP_SECRET:
        raise Exception(
            "APP_ID and APP_SECRET environement variables must be defined!" \
            "- See Readme for more information on this issue."
        )
    HTTP_SERVER = Thread(target=run, daemon=True)
    HTTP_SERVER.start()
    URL = "https://connect.deezer.com" \
          "/oauth/auth.php?app_id={}&redirect_uri=http://127.0.0.1:7766/" \
          "authfinish&perms=basic_access,email".format(APP_ID)
    webbrowser.open(URL)
    HTTP_SERVER.join()
