import configparser
import os
import time
from tkinter import *
from tkinter import filedialog
import tkinter.ttk as ttk
import pygame
from mutagen.mp3 import MP3
from PIL import ImageTk, Image

AssetsDir = os.path.join(os.path.dirname(__file__), "assets")
ImagesDir = os.path.join(AssetsDir, "images")
TracksDir = os.path.join(os.path.dirname(__file__), "tracks", "")
config = configparser.ConfigParser()
config.read(os.path.join(AssetsDir, "config.ini"))


def get_photoimage(name):
    return ImageTk.PhotoImage(
        Image.open(os.path.join(ImagesDir, config["ImagePaths"][name]))
    )

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

        # Controls #

        self.controls_frame = Frame(self.frame)
        self.controls_frame.grid(row=1, column=0, pady=20)

        self.volume_frame = LabelFrame(self.frame, text="Volume")
        self.volume_frame.grid(row=0, column=1, padx=30)

        self.slider = ttk.Scale(self.frame, from_=0, to=100,
                                orient=HORIZONTAL, value=0, command=self.slide, length=360)
        self.slider.grid(row=2, column=0, pady=10)

        self.volume_slider = ttk.Scale(self.volume_frame, from_=0, to=1,
                                       orient=VERTICAL, value=1, command=self.volume, length=125)
        self.volume_slider.pack(pady=10)

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
            Button(
                self.controls_frame, image=self.images["backward"], command=lambda:player.move_current_pos(-1)),
            Button(
                self.controls_frame, image=self.images["forward"], command=lambda:player.move_current_pos(1)),
            Button(
                self.controls_frame, image=self.images["play"], command=player.play),
            Button(
                self.controls_frame, image=self.images["pause"], command=player.toggle_pause),
            Button(
                self.controls_frame, image=self.images["stop"], command=player.stop)
        ]

        for i, button in enumerate(self.buttons):
            button.grid(row=0, column=i+1, ipadx=5, ipady=5, padx=2)

    @property
    def current_track_sel_pos(self):
        selection = self.tracks_box.curselection()
        return selection[0] if selection else None

    def update_progress(self):
        if self.player.stopped:
            return

        track = self.player.current_track

        if int(self.slider.get()) == int(track.length):
            self.status.config(
                text='Time Elapsed: {strf_length} / {strf_length}'.format(
                    track)
            )
        elif self.player.paused:
            pass
        elif int(self.slider.get()) == int(self.player.current_time):
            slider_pos = int(track.length)
            self.slider.config(to=slider_pos, value=int(
                self.player.current_time))
        else:
            slider_pos = int(track.length)
            self.slider.config(to=slider_pos, value=int(self.slider.get()))
            self.status.config(
                text=f'Time Elapsed: {player.current_time} / {player.current_track.length}'
            )
            self.slider.config(value=int(self.slider.get())+1)
        self.status.after(1000, self.update_progress)

    def slide(self, x):
        self.player.go_to(int(self.slider.get()))

    def volume(self, x):
        self.player.set_volume(self.volume_slider.get())


class Track:
    def __init__(self, path):
        self.abspath = path
        self.filename = os.path.splitext(os.path.basename(path))[0]
        self.meta = MP3(path)
        self.length = self.meta.info.length
        self.strf_length = time.strftime('%M:%S', time.gmtime(self.length))


class Player:
    def __init__(self):
        pygame.mixer.init()
        self.paused = False
        self.stopped = False
        self._tracks = []
        self.music = pygame.mixer.music
        self._current_track = None
        self._GUI = None

    @property
    def current_time(self) -> float:
        return self.music.get_pos() / 1000 + 1

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
    def current_track_pos(self) -> int:
        if self.current_track and not self.stopped:
            return self.tracks.index(self.current_track)
        return self.GUI.current_track_sel_pos

    @property
    def tracks(self) -> list[Track]:
        return self._tracks

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
            self.GUI.tracks_box.insert(END, track.abspath)
            self.tracks.append(track)

    def play(self):
        selection_pos = self.GUI.current_track_sel_pos

        if self.paused:
            if selection_pos != None and selection_pos != self.current_track_pos:
                pass
            else:
                return self.toggle_pause()
        if not self.current_track:
            return

        self.stopped = False

        if selection_pos == None:
            self.music.load(self.current_track.abspath)
        else:
            self.music.load(self.tracks[selection_pos].abspath)

        self.music.play(loops=0)
        self.GUI.update_progress()

    def stop(self):
        if self.stopped:
            return
        self.GUI.status.config(text="")
        self.GUI.slider.config(value=0)
        self.music.stop()
        self.GUI.tracks_box.selection_clear(ACTIVE)
        self.stopped = True

    def toggle_pause(self):
        self.music.unpause() if self.paused else self.music.pause()
        self.paused = not self.paused
        return self.paused

    def move_current_pos(self, step):
        self.GUI.status.config(text="")
        self.GUI.slider.config(value=0)
        target_track_pos = self.current_track_pos + step
        track = self.tracks[target_track_pos]
        self.music.load(track.abspath)
        self.music.play(loops=0)

        self.GUI.tracks_box.select_clear(0, END)
        self.GUI.tracks_box.activate(target_track_pos)
        self.GUI.tracks_box.selection_set(target_track_pos, last=None)

    def del_track(self):
        self.stop()
        self.GUI.tracks_box.delete(ANCHOR)

    def del_all_tracks(self):
        self.stop()
        self.GUI.tracks_box.delete(0, END)

    def go_to(self, start):
        self.music.load(self.current_track.abspath)
        self.music.play(loops=0, start=start)

    def set_volume(self, volume):
        self.music.set_volume(volume)

# Main


player = Player()
window = GUI()
player.GUI = window
window.root.mainloop()
