import spotipy
import asyncio
import spotipy.util as util
import os
from os.path import join, dirname
from dotenv import load_dotenv
from telethon.tl.functions.account import UpdateProfileRequest
from telethon import TelegramClient
from telethon.errors import FloodWaitError


class APIHandler:
    def __init__(self):
        scope = "user-read-currently-playing"
        scope += " user-read-playback-state"
        scope += " user-read-playback-position"
        scope += " user-follow-read"
        SPOTIFY_USERNAME = os.environ.get('SPOTIFY_USERNAME')
        SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
        SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
        REDIRECT_URI = "http://localhost:8080"
        token = util.prompt_for_user_token(SPOTIFY_USERNAME,
                                           scope, client_id=SPOTIFY_CLIENT_ID,
                                           client_secret=SPOTIFY_CLIENT_SECRET,
                                           redirect_uri=REDIRECT_URI)
        self.sp = spotipy.Spotify(auth=token)

    def getCurrentTrack(self):
        current_playback = self.sp.current_playback()
        if current_playback is not None:
            return current_playback['item']['name']
        return None

    def getCurrentTrackArtist(self):
        current_playback = self.sp.current_playback()
        if current_playback:
            artist = current_playback['item']['artists'][0]
            return artist['name']
        return None

    def getCurrentPlaybackTime(self):
        current_playback = self.sp.current_playback()
        if current_playback is not None:
            progress_ms = current_playback['progress_ms']
            duration_ms = current_playback['item']['duration_ms']
            return self.__get_mins_secs(progress_ms) + \
                "/" + self.__get_mins_secs(duration_ms)
        return None

    def __get_mins_secs(self, ms):
        total_seconds = ms // 1_000
        mins, secs = divmod(total_seconds, 60)
        return "{:0>2}:{:0>2}".format(mins, secs)


async def main(client):
    handler = APIHandler()

    TELEGRAM_BIO = os.environ.get("TELEGRAM_BIO")

    while True:
        skip = False
        if handler.getCurrentTrack() is not None:
            about = "🎧" + \
                handler.getCurrentTrack() + \
                " - " + handler.getCurrentTrackArtist()
        else:
            about = TELEGRAM_BIO
        if len(about) >= 70:
            about = TELEGRAM_BIO
        print(about)
        try:
            await client(UpdateProfileRequest(about=about))
        except FloodWaitError as e:
            to_wait = e.seconds()

            skip = True
            await asyncio.sleep(int(to_wait))
        if not skip:
            await asyncio.sleep(30)

if __name__ == "__main__":
    load_dotenv(join(dirname(__file__), '.env'))
    TELEGRAM_API = os.environ.get('TELEGRAM_API')
    TELEGRAM_HASH = os.environ.get('TELEGRAM_HASH')
    client = TelegramClient('default', TELEGRAM_API, TELEGRAM_HASH)

    print("> Program has been booted.")

    with client:
        client.loop.run_until_complete(main(client))
