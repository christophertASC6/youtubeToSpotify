"""
Step 1: Log into YouTube with API token/key
Step 2: Request liked videos via API
Step 3: Create a new playlist using the Spotify API
Step 4: Search (index) for the song we want
Step 5: Push song into Spotify playlist (arrays?)
"""
import json
import requests
import os

from secrets import spotify_user_id
from secrets import spotify_token

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl

class CreatePlaylist:
    def __init__(self):
        self.user_id = spotify_user_id
        self.spotify_token = spotify_token
        self.youtube_client = self.get_youtube_client()
        self.all_song_info = {}

    # Step 1
    def get_youtube_client(self):
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

    # Step 2
    def get_liked_videos(self):
        request = self.youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like"
        )
        response = request.execute()

        # Collect each video to query a like
        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(item["id"])

            # Use youtube_dl to collect song & artist name
            video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)

            song_name = video["track"]
            artist = video["artist"]

            # Save info
            self.all_song_info[video_title]={
                "youtube_url": youtube_url,
                "song_name": song_name,
                "artist": artist,

            # Add the uri to get song into playlist
            "spotify_uri":self.get_spotify_uri(song_name,artist)
        }
    # Step 3
    def create_playlist(self):

        request_body = json.dumps({
            "name": "",
            "description": "All Liked YouTube Videos",
            "public": True
        })

        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.user_id)
        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )

    # Step 4
    def get_spotify_uri(self, song_name, artist):

        query = "https://api.spotify.com/v1/search?query=track%3a{}+artist%3a{}&type=track&offset=0&limit=20".format(
            song_name,
            artist
        )
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
        response_json = response.json()
        songs = response_json["tracks"]["items"]

        # Append to playlist URI
        uri = songs[0]["uri"]
        return uri

    # Step 5
    def add_song_to_playlist(self):
        # Add song dictionary
        self.get_liked_videos()

        # Collect URI
        uris = []
        for song, info in self.all_song_info.items():
            uris.append(info["spotify_uri"])

        # Create a new playlist
        playlist_id = self.create_playlist()

        # Add all songs into new playlist
        request_data = json.dumps(uris)

        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)
        response = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_token)
            }
        )
        response_json = response.json()
        return response_json