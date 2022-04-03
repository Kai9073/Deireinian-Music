import configparser
import errno
import os
import time
import tkinter.ttk as ttk
from tkinter import *
from tkinter import filedialog

import dill
import mutagen
import pygame
from mutagen.mp3 import MP3
from PIL import Image, ImageTk

AssetsDir = os.path.join(os.path.dirname(__file__), "assets")

config = configparser.ConfigParser()
config.read(os.path.join(AssetsDir, "config.ini"))

ImagesDir = os.path.join(os.path.dirname(
    __file__), config["ImagePaths"]["MainDir"])
TracksDir = os.path.join(os.path.dirname(__file__), "tracks", "")
SavesDir = os.path.join(os.path.dirname(__file__), config["Saves"]["dir"])


def get_photoimage(name):
    return ImageTk.PhotoImage(
        Image.open(os.path.join(ImagesDir, config["ImagePaths"][name]))
    )


def check_permssions(path):
    try:
        with open(path) as f:
            f.read()
            return True
    except IOError as x:
        if x.errno == errno.ENOENT:
            print(f"[ENOENT] {path} - File does't exist, skipping...")
        elif x.errno == errno.EACCES:
            print(f'[EACCES] {path} - Permission denied, skipping...')
        else:
            print(f'[ERR {x.errno}] {path} - Could not read file')
        return False
    except UnicodeDecodeError:
        return True

# Classes


class GUI:
    def __init__(self):
        global player
        self.player = player

        # Root #

        self.root = Tk()
        self.root.title("Deireinian Music")
        self.root.iconphoto(False, get_photoimage("icon"))
        self.root.geometry("500x450")

        # Menu #

        self.menu = Menu(self.root)
        self.menu_add = Menu(self.menu)
        self.menu_add.add_command(
            label="Add One Song To Playlist",
            command=lambda: player.add_track(multiple=False)
        )
        self.menu_add.add_command(
            label="Add Multiple Songs To Playlist",
            command=lambda: player.add_track(multiple=True)
        )
        self.menu_rmv = Menu(self.menu)
        self.menu_rmv.add_command(
            label="Delete A Song From Playlist",
            command=player.del_track
        )
        self.menu_rmv.add_command(
            label="Delete All Songs From Playlist",
            command=player.del_all_tracks
        )

        self.menu.add_cascade(label="Add Songs", menu=self.menu_add)
        self.menu.add_cascade(label="Remove Songs", menu=self.menu_rmv)

        self.root.config(menu=self.menu)

        # Main Frame #

        self.frame = Frame(self.root)
        self.frame.pack(pady=20)

        # Tracks Box #

        self.tracks_box = Listbox(
            self.frame, fg="black", width=60,
            selectbackground="gray", selectforeground="black"
        )
        self.tracks_box.grid(row=0, column=0)

        # Track Info

        self.track_info_frame = Frame(self.frame)
        self.track_info_frame.grid(row=1, column=0, pady=(20, 0))

        self.track_title = Label(
            master=self.track_info_frame,
            text="",
            font=('Helvetica', '20')
        )
        self.track_artist = Label(
            master=self.track_info_frame,
            text="",
            font=('Helvetica', '12'))
        self.track_title.grid(row=0, column=0)
        self.track_artist.grid(row=1, column=0)

        # Controls #

        self.controls_frame = Frame(self.frame)
        self.controls_frame.grid(row=2, column=0, pady=20)

        self.volume_frame = LabelFrame(self.controls_frame, text="Volume")
        self.volume_frame.grid(row=0, column=5, padx=(30, 5))

        self.slider = ttk.Scale(self.frame, from_=0, to=100,
                                orient=HORIZONTAL, value=0,
                                command=self.slide, length=360)
        self.slider.grid(row=3, column=0)

        self.volume_slider = ttk.Scale(master=self.volume_frame, from_=0,
                                       to=1, orient=HORIZONTAL, value=1,
                                       command=self.volume, length=125)
        self.volume_slider.pack(padx=10, pady=3)

        self.status = Label(self.root, text="", bd=1, relief=GROOVE, anchor=E)
        self.status.pack(fill=X, side=BOTTOM, ipady=2)

        self.images = {
            "backward": get_photoimage("BtnBackward"),
            "forward": get_photoimage("BtnForward"),
            "play": get_photoimage("BtnPlay"),
            "pause": get_photoimage("BtnPause"),
            "stop": get_photoimage("BtnStop")
        }

        self.buttons = [
            Button(self.controls_frame, image=self.images["backward"],
                   command=lambda:player.move_current_pos(-1)),
            Button(self.controls_frame, image=self.images["forward"],
                   command=lambda:player.move_current_pos(1)),
            Button(self.controls_frame, image=self.images["play"],
                   command=player.play),
            Button(self.controls_frame, image=self.images["pause"],
                   command=player.toggle_pause),
            Button(self.controls_frame, image=self.images["stop"],
                   command=player.stop)
        ]

        for i, button in enumerate(self.buttons):
            button.grid(row=0, column=i, ipadx=5, ipady=5, padx=2)

    @property
    def current_track_sel_pos(self):
        selection = self.tracks_box.curselection()
        return selection[0] if selection else None

    def update_progress(self):
        if self.player.stopped:
            return

        track = self.player.current_track

        if self.player.paused:
            pass
        elif int(self.slider.get()) >= int(track.length):
            self.status.config(
                text='Time Elapsed: {0} / {0}'.format(track.strf_length)
            )
            self.player.move_current_pos(1)
        else:
            slider_length = int(track.length)
            self.slider.config(to=slider_length, value=int(
                self.player.current_time))
            self.status.config(
                text='Time Elapsed: {} / {}'.format(
                    player.strf_current_time,
                    player.current_track.strf_length
                )
            )
        self.status.after(1000, self.update_progress)

    def update_track_info(self):
        info = self.player.current_track.details
        self.track_title.config(text=info.title)
        self.track_artist.config(text=info.artist)

    def slide(self, x):
        self.player.go_to(int(self.slider.get()))

    def volume(self, x):
        self.player.set_volume(self.volume_slider.get())


class TrackInfo:
    def __init__(self, meta, path):
        self.meta = meta
        self.path = path
        self.details = mutagen.File(path, None, True)

    @property
    def album(self):
        if 'album' in self.details and len(self.details["album"]) > 0:
            return self.details["album"][0]
        else:
            return None

    @property
    def title(self):
        if 'title' in self.details and len(self.details["title"]) > 0:
            return self.details["title"][0]
        else:
            return None

    @property
    def artist(self):
        if 'artist' in self.details and len(self.details["artist"]) > 0:
            return " / ".join(self.details["artist"])
        else:
            return None


class Track:
    def __init__(self, path: str):
        self.readable = check_permssions(path)
        if not self.readable:
            return
        self.abspath = path
        self.filename = os.path.splitext(os.path.basename(path))[0]
        self.meta = MP3(path)
        self.length = self.meta.info.length
        self.strf_length = time.strftime('%M:%S', time.gmtime(self.length))
        self.details = TrackInfo(self.meta, self.abspath)


class Player:
    def __init__(self):
        pygame.mixer.init()
        self.paused = False
        self.stopped = False
        self.track_pos_offset = 0
        self._tracks = []
        self.music = pygame.mixer.music
        self._current_track = None
        self._GUI = None

    @property
    def current_time(self) -> float:
        return self.music.get_pos() / 1000 + 1 + self.track_pos_offset

    @property
    def strf_current_time(self) -> str:
        return time.strftime('%M:%S', time.gmtime(self.current_time))

    @property
    def current_track(self) -> Track | None:
        if self._current_track:
            return self._current_track
        elif self.tracks:
            return self.tracks[0]
        else:
            return None

    @property
    def current_track_pos(self) -> int | None:
        if self.current_track and not self.stopped and self.tracks:
            return self.tracks.index(self.current_track)
        return self.GUI.current_track_sel_pos

    @property
    def tracks(self) -> list[Track]:
        return self._tracks

    @tracks.setter
    def tracks(self, tracks: list[Track]):
        for track in tracks:
            if not track.readable:
                continue
            self.GUI.tracks_box.insert(END, track.filename)
            self._tracks.append(track)

    @current_track.setter
    def current_track(self, track: Track) -> Track:
        self._current_track = track
        return self._current_track

    @property
    def GUI(self) -> GUI | None:
        return None if not self._GUI else self._GUI

    @GUI.setter
    def GUI(self, GUI: GUI) -> GUI:
        self._GUI = GUI
        return self._GUI

    def add_track(self, multiple=False) -> list[Track]:
        if multiple:
            tracks = map(
                lambda file: Track(file),
                filedialog.askopenfilenames(
                    initialdir=TracksDir,
                    title="Choose Songs",
                    filetypes=(("MP3 Audio Files", "*.mp3"), )
                )
            )
        else:
            tracks = [
                Track(
                    filedialog.askopenfilename(
                        initialdir=TracksDir,
                        title="Choose A Song",
                        filetypes=(("MP3 Audio Files", "*.mp3"), ))
                )
            ]

        for track in tracks:
            if not track.readable:
                continue
            self.GUI.tracks_box.insert(END, track.filename)
            self._tracks.append(track)

        self.save()

    def play(self):
        selection_pos = self.GUI.current_track_sel_pos

        if self.paused:
            if (selection_pos is not None
                    and selection_pos != self.current_track_pos):
                pass
            else:
                return self.toggle_pause()
        if not self.current_track:
            return

        self.stopped = False

        self.track_pos_offset = 0
        if selection_pos is None:
            self.music.load(self.current_track.abspath)
            if self.current_track_pos is not None:
                current_pos = self.current_track_pos
                self.GUI.tracks_box.selection_clear(0, END)
                self.GUI.tracks_box.selection_set(current_pos, last=None)
                self.GUI.tracks_box.activate(current_pos)
        else:
            self.music.load(self.tracks[selection_pos].abspath)
            self.current_track = self.tracks[selection_pos]

        self.music.play(loops=0)
        self.GUI.update_track_info()
        self.GUI.update_progress()

    def stop(self):
        if self.stopped:
            return
        self.GUI.status.config(text="")
        self.GUI.slider.config(value=0)
        self.music.stop()
        self.stopped = True

    def toggle_pause(self):
        self.music.unpause() if self.paused else self.music.pause()
        self.paused = not self.paused
        return self.paused

    def move_current_pos(self, step):
        current_track_pos = (self.current_track_pos
                             if self.current_track_pos is not None
                             else -1)
        target_track_pos = current_track_pos + step
        if ((target_track_pos < 0) | (target_track_pos > len(self.tracks)-1)):
            target_track_pos = 0
        self.stop()
        print('target', target_track_pos)
        self.GUI.tracks_box.selection_clear(0, END)
        self.GUI.tracks_box.selection_set(target_track_pos, last=None)
        self.GUI.tracks_box.activate(target_track_pos)
        self.GUI.update_track_info()
        self.play()

    def del_track(self):
        self.stop()
        self.GUI.tracks_box.delete(ANCHOR)

    def del_all_tracks(self):
        self.stop()
        self.GUI.tracks_box.delete(0, END)

    def go_to(self, start):
        self.track_pos_offset = start
        self.music.play(loops=0, start=start)

    def set_volume(self, volume):
        self.music.set_volume(volume)

    def save(self):
        save_file = config["Saves"]["filename"]
        with open(os.path.join(AssetsDir, save_file), "wb") as f:
            dill.dump(self._tracks, f)

    def load(self):
        save_file = config["Saves"]["filename"]
        with open(os.path.join(SavesDir, save_file), "rb") as f:
            try:
                self.tracks = dill.load(f)
            except Exception as e:
                print("No saved data found / Could not load saved data:")
                print(e)


# Main


player = Player()
window = GUI()
player.GUI = window
player.load()
window.root.mainloop()
