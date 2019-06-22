from flask import Flask, jsonify, request, Response
import requests
from collections import defaultdict
import json

class SpotifyAPI:

	def setAccessToken(self, access_token):
		self.access_token = access_token

	def createHeaders(self):
		headers = {'Authorization': 'Bearer %s'% (self.access_token)}
		return headers   

	def getUserPlaylists(self):
		url = 'https://api.spotify.com/v1/me/playlists?limit=5'
		buildPlaylist = []
		while url:
			response = requests.get(url, headers=self.createHeaders())
			url = response.json()['next']
			buildPlaylist += response.json()['items']
		return buildPlaylist

	def getPlaylistTracks(self, playlistID):
		url = 'https://api.spotify.com/v1/playlists/' + playlistID + '/tracks?limit=100'
		buildTracks = []
		while url:          
			response = requests.get(url, headers=self.createHeaders())
			url = response.json()['next']
			buildTracks += filter(lambda x: x['track']['id'] is not None, response.json()['items'])
		return buildTracks 

	def getTrackFeatures(self, track):
		url = 'https://api.spotify.com/v1/audio-features/' + track['id']
		response = requests.get(url, headers=self.createHeaders())
		return response.json()
	
	def getAccessToken(self, code):
		client_id = 'f6f25ab872f9497f8ee10574b4c3b9ef'
		client_secret = '2d9cc2fcc3b745e6bf2a292713e8d5e1'
		url = 'https://accounts.spotify.com/api/token'
		form = {}
		form = {
			'code': code,
			'redirect_uri': 'http://localhost:3000/main',
			'grant_type': 'authorization_code',
			'client_id' : client_id,
			'client_secret' : client_secret
		}
		response = requests.post(url, data=form)
		return response.json()

app = Flask(__name__)
api = SpotifyAPI()

#Playlist Dictionary {PlaylistID {TrackID, TrackItems}}
playlists_dictionary = defaultdict(dict)

#Feature Data Dictionary {Playlist ID {Track ID, FeatureData}}
raw_feature_data = defaultdict(dict)

@app.route('/')
def hello_world():
	return 'Welcome to Playlist Exploder!'

#Rename this endpoint + function
@app.route('/main')
def buildDictionaries():
																																																																																						   
	print 'Playlist Exploder started!'
														  
	#PlaylistID Dictionary {PlaylistID, PlaylistObject}
	playlistIDs = defaultdict(dict)

	global playlists_dictionary
	
	global raw_feature_data

	#Averages Dictionary {PlaylistID {Metrics : x}}
	averages = {}
	
	#Get User's playlists, build playlistsID dictionary
	for playlist in api.getUserPlaylists():
		playlistIDs[playlist['id']] = playlist
	print 'playlistIDs created'
		
	#Iterate through playlistID to get tracks and add to playlist_dictionary
	#Currently limit to 10, remove limit later
	for playlistID in playlistIDs.keys()[:5]:  
		for item in api.getPlaylistTracks(playlistID):                          
			track = item['track'] 
			playlists_dictionary[playlistID][track['id']] = track
			
	print 'playlist_dictionary created'

	#Go through playlist_dictionary, get track for given playlist_id, for all tracks, build  feature dictionary
	for (playlist_id, tracks) in playlists_dictionary.items():
		print '# of tracks in playlist: %s. PlaylistID: %s. PlaylistName: %s' % (str(len(tracks)), playlist_id, playlistIDs[playlist_id]['name'])

		#Add track features metrics to raw_feature_data dictionary
		for (trackID, track) in tracks.items():
			raw_feature_data[playlist_id][track['id']] = api.getTrackFeatures(track)

		#Initialize variables
		average_tempo = 0
		average_acousticness = 0
		average_danceability = 0
		average_energy = 0
		average_instrumentalness = 0
		average_liveness = 0
		average_loudness = 0
		average_speechiness = 0
		average_valence = 0
		average_popularity = 0
		average_length = 0 
		final_playlist_tracks = 0

		#Add up values
		for (trackID, feature) in raw_feature_data[playlist_id].items():
			average_tempo += feature['tempo']
			average_acousticness += feature['acousticness']
			average_danceability += feature['danceability']
			average_energy += feature['energy']
			average_instrumentalness += feature['instrumentalness']
			average_liveness += feature['liveness']
			average_loudness += feature['loudness']
			average_speechiness += feature['speechiness']
			average_valence += feature['valence']
			average_popularity += playlists_dictionary[playlist_id][trackID]['popularity']
			average_length += feature['duration_ms']

		#Calculate averages
		final_playlist_tempo = float(average_tempo)/len(tracks)
		final_playlist_acousticness = float(average_acousticness)/len(tracks)
		final_playlist_danceability = float(average_danceability)/len(tracks)
		final_playlist_energy = float(average_energy)/len(tracks)
		final_playlist_instrumentalness = float(average_instrumentalness)/len(tracks)
		final_playlist_liveness = float(average_liveness)/len(tracks)
		final_playlist_loudness = float(average_loudness)/len(tracks)
		final_playlist_speechiness = float(average_speechiness)/len(tracks)
		final_playlist_valence = float(average_valence)/len(tracks)
		final_playlist_popularity = float(average_popularity)/len(tracks)
		final_playlist_length = float(average_length)/len(tracks)
		final_playlist_tracks = len(tracks)

		#Add averages to average Dictionary
		averages[playlist_id] = {
			'playlist_name' : playlistIDs[playlist_id]['name'],
			'average_tempo' : final_playlist_tempo,
			'average_acousticness' : final_playlist_acousticness,
			'average_danceability' : final_playlist_danceability,
			'average_energy' : final_playlist_energy,
			'average_instrumentalness' : final_playlist_instrumentalness,
			'average_liveness' : final_playlist_liveness,
			'average_loudness' : final_playlist_loudness,
			'average_speechiness' : final_playlist_speechiness,
			'average_valence' : final_playlist_valence,
			'average_popularity' : final_playlist_popularity,
			'average_length' : final_playlist_length,
			'number_of_tracks' : final_playlist_tracks,

		}

	print averages

	resp = app.make_response(jsonify(averages))
	resp.headers['Access-Control-Allow-Origin'] = '*'

	return resp

@app.route('/explode/<playlistID>')
def explodePlaylist(playlistID):
	finalTable = {}
	for trackID in playlists_dictionary[playlistID]:
		track = playlists_dictionary[playlistID][trackID]
		trackData = {}
		trackData.update(raw_feature_data[playlistID][trackID])
		trackData.update({
			'trackname':track['name'],
			'artist':', '.join([artist['name'] for artist in track['artists']]),
			'album':track['album']['name'],
			'year':track['album']['release_date'][:4]
      	})

		finalTable[trackID]= trackData

	resp = app.make_response(jsonify(finalTable))
	resp.headers['Access-Control-Allow-Origin'] = '*'
	return resp

@app.route('/code',methods = ['POST'])
def code():
	AuthData = api.getAccessToken(json.loads(request.data).get('code'))

	api.setAccessToken(AuthData['access_token'])

	resp = Response()
	resp.headers['Access-Control-Allow-Origin'] = '*'
	return resp

@app.route('/callback')
def storeAccessToken():
	pass