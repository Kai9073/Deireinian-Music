import configparser
import os
import time
from tkinter import *
from tkinter import filedialog
import tkinter.ttk as ttk
import pygame
from mutagen.mp3 import MP3

AssetsDir = os.path.join(os.path.dirname(__file__), "assets")
ImagesDir = os.path.join(AssetsDir, "images")
TracksDir = os.path.join(os.path.dirname(__file__), "tracks", "")
config = configparser.ConfigParser()
config.read(os.path.join(AssetsDir, "config.ini"))


def get_photoimage(name): return PhotoImage(
    file=os.path.join(ImagesDir, config["ImagePaths"][name]))


root = Tk()
root.title("Deireinian Music")
root.iconbitmap(get_photoimage("icon"))
root.geometry("500x300")

# Init Pygame Mixer
pygame.mixer.init()

global paused
global stopped
paused = stopped = False

# Functions


def play_time():
    if stopped:
        return

    current_time = pygame.mixer.music.get_pos() / 1000
    strf_current_time = time.strftime('%M:%S', time.gmtime(current_time))

    track = tracks_box.get(ACTIVE)
    track_meta = MP3(track)

    global track_length
    track_length = track_meta.info.length

    strf_track_length = time.strftime('%M:%S', time.gmtime(track_length))

    current_time += 1

    if int(slider.get()) == int(track_length):
        status_bar.config(
            text=f'Time Elapsed: {strf_track_length} of {strf_track_length}')
    elif paused:
        pass
    elif int(slider.get()) == int(current_time):
        slider_pos = int(track_length)
        slider.config(to=slider_pos, value=int(current_time))
    else:
        slider_pos = int(track_length)
        slider.config(to=slider_pos, value=int(slider.get()))
        strf_current_time = time.strftime(
            '%M:%S', time.gmtime(int(slider.get())))
        status_bar.config(
            text=f'Time Elapsed: {strf_current_time} of {strf_track_length}')
        new_time = int(slider.get()) + 1
        slider.config(value=new_time)

    status_bar.after(1000, play_time)


def add_track():
    track_file = filedialog.askopenfilename(
        initialdir=TracksDir, title="Choose A Song", filetypes=(("MP3 Audio Files", "*.mp3"), ))
    track_filename = os.path.splitext(os.path.basename(track_file))[0]
    tracks_box.insert(END, track_file)


def add_multiple_tracks():
    track_files = filedialog.askopenfilenames(
        initialdir=TracksDir, title="Choose Songs", filetypes=(("MP3 Audio Files", "*.mp3"), ))
    for file in track_files:
        track_filename = os.path.splitext(os.path.basename(file))[0]
        tracks_box.insert(END, file)


def update_volume_img():

    current_volume = pygame.mixer.music.get_volume() * 100

    if int(current_volume) < 1:
        volume_meter.config(image=vol_images[0])
    elif int(current_volume) <= 25:
        volume_meter.config(image=vol_images[1])
    elif int(current_volume) <= 50:
        volume_meter.config(image=vol_images[2])
    elif int(current_volume) <= 75:
        volume_meter.config(image=vol_images[3])
    elif int(current_volume) <= 100:
        volume_meter.config(image=vol_images[4])


def play():
    global stopped
    stopped = False
    track = tracks_box.get(ACTIVE)

    pygame.mixer.music.load(track)
    pygame.mixer.music.play(loops=0)

    play_time()
    update_volume_img()


def stop():
    status_bar.config(text="")
    slider.config(value=0)

    pygame.mixer.music.stop()
    tracks_box.selection_clear(ACTIVE)

    status_bar.config(text="")

    global stopped
    stopped = True

    update_volume_img()


def pause():
    global paused

    if paused:
        pygame.mixer.music.unpause()
        paused = False
    else:
        pygame.mixer.music.pause()
        paused = True


def move_track(step):
    status_bar.config(text="")
    slider.config(value=0)

    current_track_pos = tracks_box.curselection()[0]
    target_track_pos = current_track_pos + step

    track = tracks_box.get(target_track_pos)
    pygame.mixer.music.load(track)
    pygame.mixer.music.play(loops=0)

    tracks_box.selection_clear(0, END)
    tracks_box.activate(target_track_pos)
    tracks_box.selection_set(target_track_pos, last=None)


def next_track():
    move_track(1)


def prev_track():
    move_track(-1)


def del_track():
    stop()
    tracks_box.delete(ANCHOR)
    pygame.mixer.music.stop()


def del_all():
    stop()
    tracks_box.delete(0, END)
    pygame.mixer.music.stop()


def slide(x):
    track = tracks_box.get(ACTIVE)
    pygame.mixer.music.load(track)
    pygame.mixer.music.play(loops=0, start=int(slider.get()))


def volume(x):
    pygame.mixer.music.set_volume(volume_slider.get())
    update_volume_img()


master_frame = Frame(root)
master_frame.pack(pady=20)


# Create Track List Box
tracks_box = Listbox(master_frame, bg="black", fg="green", width=60,
                     selectbackground="gray", selectforeground="black")
tracks_box.grid(row=0, column=0)


PhotoImages = {
    "backward": get_photoimage("BtnBackward"),
    "forward": get_photoimage("BtnForward"),
    "play": get_photoimage("BtnPlay"),
    "pause": get_photoimage("BtnPause"),
    "stop": get_photoimage("BtnStop"),
    "vol0": get_photoimage("vol0"),
    "vol1": get_photoimage("vol1"),
    "vol2": get_photoimage("vol2"),
    "vol3": get_photoimage("vol3"),
    "vol4": get_photoimage("vol4")
}

global vol_images
vol_images = (PhotoImages["vol0"], PhotoImages["vol1"],
              PhotoImages["vol2"], PhotoImages["vol3"], PhotoImages["vol4"])


# Create Ctrl Frame
controls_frame = Frame(master_frame, height=10)
controls_frame.grid(row=1, column=0, pady=20)

volume_meter = Label(master_frame, image=vol_images[0])
volume_meter.grid(row=1, column=1, padx=10)

volume_frame = LabelFrame(master_frame, text="Volume")
volume_frame.grid(row=0, column=1, padx=30)

# Create Ctrl Btns
backward_btn = Button(
    controls_frame, image=PhotoImages["backward"], command=prev_track)
forward_btn = Button(
    controls_frame, image=PhotoImages["forward"], command=next_track)
play_btn = Button(controls_frame, image=PhotoImages["play"], command=play)
pause_btn = Button(controls_frame, image=PhotoImages["pause"], command=pause)
stop_btn = Button(controls_frame, image=PhotoImages["stop"], command=stop)

backward_btn.grid(row=0, column=0, ipadx=5, ipady=5)
forward_btn.grid(row=0, column=1, ipadx=5, ipady=5)
play_btn.grid(row=0, column=2, ipadx=5, ipady=5)
pause_btn.grid(row=0, column=3, ipadx=5, ipady=5)
stop_btn.grid(row=0, column=4, ipadx=5, ipady=5)

menu = Menu(root)
root.config(menu=menu)

add_track_menu = Menu(menu)
menu.add_cascade(label="Add Songs", menu=add_track_menu)
add_track_menu.add_command(label="Add One Song To Playlist", command=add_track)
add_track_menu.add_command(
    label="Add Multiple Songs To Playlist", command=add_multiple_tracks)

remove_song_menu = Menu(menu)
menu.add_cascade(label="Remove Songs", menu=remove_song_menu)
remove_song_menu.add_command(
    label="Delete A Song From Playlist", command=del_track)
remove_song_menu.add_command(
    label="Delete All Songs From Playlist", command=del_all)

status_bar = Label(root, text='', bd=1, relief=GROOVE, anchor=E)
status_bar.pack(fill=X, side=BOTTOM, ipady=2)

slider = ttk.Scale(master_frame, from_=0, to=100,
                   orient=HORIZONTAL, value=0, command=slide, length=360)
slider.grid(row=2, column=0, pady=10)

volume_slider = ttk.Scale(volume_frame, from_=0, to=1,
                          orient=VERTICAL, value=1, command=volume, length=125)
volume_slider.pack(pady=10)

root.mainloop()
