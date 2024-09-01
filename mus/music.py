from mutagen import File, id3
import customtkinter as ctk
from pathlib import Path
from PIL import Image
from mus.util import GEOMETRY, TITLE, PlayerState
import tkinter as tk
import tempfile
import pygame
import asyncio
from mus.topbar import TopBar
from mus.playlist import PlaylistFrame
from mus.control import ControlBar
from mus.cover_art import CoverArtFrame
from mus.progress import BottomFrame

ctk.set_default_color_theme("theme.json")


class MusicPlayer(ctk.CTk):
    def __init__(self: ctk.CTk):
        super().__init__()

        # CONFIG
        self.geometry(GEOMETRY)
        self.title(TITLE)

        # STATE
        self.playlist = []
        self.STATE = PlayerState.STOPPED
        self.current_folder = ""
        self.playlist_index = 0
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.update_loop()

        # SETUP PYGAME
        self.initialize_pygame()

        # ICONS
        self.setup_icons()

        # FRAMES
        self.topbar = TopBar(self, self.folder_icon, self.music_icon)
        self.control_bar = ControlBar(
            self,
            self.pause_icon,
            self.play_icon,
            self.prev_icon,
            self.next_icon,
            self.play_next_song,
        )
        self.playlist_frame = PlaylistFrame(self)
        self.bottom_frame = BottomFrame(self)
        self.cover_art_frame = CoverArtFrame(self)

        # BINDINGS AND EVENTS
        self.setup_bindings()

        # WIDGET PLACEMENT
        self.topbar.pack(side=tk.TOP, fill=tk.X)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.control_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.playlist_frame.pack(side=tk.RIGHT)
        self.cover_art_frame.pack(side=tk.LEFT)

    def load_and_play_song(self, index):

        # MUSIC
        self.music.unload()
        self.music.stop()
        self.music.load(self.playlist[index])
        self.music.play()
        self.STATE = PlayerState.PLAYING
        self.playlist_index = index

        # CHANGE INFO
        cover_image = self.get_album_cover(self.playlist[index])
        self.cover_art_frame.cover_art_label.configure(image=cover_image)

        self.control_bar.set_music_title(self.get_song_title(self.playlist[index]))
        self.control_bar.update_play_button(self.STATE)

        self.bottom_frame.start_progress_bar(self.get_song_length(self.playlist[index]))

    def play_next_song(self, event=None):
        if not self.playlist:
            return

        # PLAY FROM BEGINING
        elif self.playlist_index >= len(self.playlist) - 1:
            self.playlist_index = 0
        else:
            self.playlist_index += 1
        self.load_and_play_song(self.playlist_index)

        # UPDATE SELECTION
        self.playlist_frame.song_list.selection_clear(0, tk.END)
        self.playlist_frame.song_list.select_set(self.playlist_index)

    def get_song_length(self, file_path):
        audio = File(file_path)
        if audio is not None and audio.info is not None:
            return audio.info.length
        else:
            return 0

    def get_song_title(self, file_path):
        try:
            # NO TITLE METADATA
            if not file_path.endswith(".mp3"):
                return Path(file_path).stem
            else:
                audio = id3.ID3(file_path)
                return audio["TIT2"].text[0]
        except:
            return ""

    def get_album_cover(self, file_path):
        if not file_path.endswith(".mp3"):
            return None
        else:
            try:
                audio_file = id3.ID3(file_path)
                cover_data = None

                # APIC TAG FOR IMAGE DATA
                for tag in audio_file.getall("APIC"):
                    if tag.mime == "image/jpeg" or tag.mime == "image/png":
                        cover_data = tag.data
                        break
                if cover_data:

                    # TEMP STORE COVER
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".jpg"
                    ) as temp_file:
                        temp_file.write(cover_data)
                        temp_path = temp_file.name

                    return ctk.CTkImage(Image.open(temp_path), size=(250, 250))
                return None
            except:
                return None

    # WIP
    def get_artist(self, filepath):
        pass

    def get_song_position(self):
        return pygame.mixer.music.get_pos() / 1000

    def initialize_pygame(self):
        pygame.init()
        pygame.mixer.init()
        self.music = pygame.mixer.music

        # CREATE USEREVENT WHEN MUSIC ENDS
        pygame.mixer.music.set_endevent(pygame.USEREVENT)

    # AUTOPLAY NEXT SONG AFTER SONG ENDS
    def check_for_events(self):
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:
                self.play_next_song()

    def setup_icons(self):
        self.play_icon = ctk.CTkImage(Image.open("pic/play_arrow.png"))
        self.pause_icon = ctk.CTkImage(Image.open("pic/pause.png"))
        self.prev_icon = ctk.CTkImage(Image.open("pic/skip_prev.png"))
        self.next_icon = ctk.CTkImage(Image.open("pic/skip_next.png"))
        self.folder_icon = ctk.CTkImage(Image.open("pic/folder.png"))
        self.music_icon = ctk.CTkImage(Image.open("pic/music.png"))

    def setup_bindings(self):
        self.bind("<F10>", self.play_next_song)
        self.bind("<F8>", self.control_bar.play_previous)
        self.bind("<F9>", self.control_bar.play_pause)
        self.bind("<space>", self.control_bar.play_pause)

    def update_loop(self):
        self.loop.call_soon(self.loop.stop)
        self.loop.run_forever()
        self.after(100, self.update_loop)


if __name__ == "__main__":
    music_player = MusicPlayer()
    music_player.mainloop()