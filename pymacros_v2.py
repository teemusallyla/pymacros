import threading
import time
from tkinter import *
import time
import json
from pynput.keyboard import Key, Controller, Listener
import os

keyboard = Controller()
key_map = {}
for key in list(Key):
    key_map[key.name] = key

modifier_keys = ["alt", "alt_l", "alt_r", "cmd", "cmd_r",
                 "ctrl", "ctrl_l", "ctrl_r", "shift", "shift_r"]

is_playing = False
is_recording = False
play_key = "P"
record_key = "R"
wait_time = 5
stop_playing = threading.Event()

def clear_playing():
    global is_playing
    playtext.set("Play ({})".format(play_key))
    is_playing = False

def play_recording(events):
    global is_playing
    global stop_playing
            
    for x in range(wait_time, 0, -1):
        if stop_playing.is_set():
            stop_playing.clear()
            clear_playing()
            return
        playtext.set(x)
        time.sleep(1)
    playtext.set("Playing...")

    keys_down = []

    for event in events:
        key = event[0]
        if key == "":
            pass
        else:
            kkey = None
            if len(key) != 1:
                kkey = key_map[key]

            key = key.lower()
                
            modifiers = [key_map[name] for name in keys_down if name in modifier_keys]
            with keyboard.pressed(*modifiers):
                keyboard.touch(kkey or key, key in keys_down)

            if key in keys_down:
                keys_down.remove(key)
            else:
                keys_down.append(key)


        if len(event) > 1:
            if stop_playing.is_set():
                for key in keys_down:
                    kkey = None
                    if len(key) != 1:
                        kkey = key_map[key]
                    keyboard.release(kkey or key)
                stop_playing.clear()
                clear_playing()
                return
            else:
                time.sleep(event[1])

    clear_playing()

def play_pressed():
    global is_playing

    if is_recording:
        record_pressed()
    if is_playing:
        stop_playing.set()
        playtext.set("Stopping...")
        is_playing = False
    else:
        stop_playing.clear()
        is_playing = True
        with open("last_record.txt") as f:
            events = json.load(f)
        th = threading.Thread(target=play_recording, args=(events,))
        th.start()


def on_event(key):
    global events
    global last_event_fired
    cur_time = time.time()

    if events == []:
        events.append([""])
    
    events[-1].append(cur_time - last_event_fired)
    try:
        events.append([key.name])
    except AttributeError:
        events.append([key.char])

    last_event_fired = cur_time

recording_thread = None
stop_recording = threading.Event()

def record():
    global events
    global last_event_fired
    events = []
    for x in range(wait_time, 0, -1):
        if stop_recording.is_set(): return
        recordtext.set(x)
        time.sleep(1)
    recordtext.set("Recording...")
    last_event_fired = time.time()
    recording_thread = Listener(on_press=on_event, on_release=on_event)
    recording_thread.start()
    stop_recording.wait()
    recording_thread.stop()
    with open("last_record.txt", "w+") as f:
        json.dump(events, f)

    if playbtn["state"] == "disabled":
        playbtn["state"] = "normal"
    

def record_pressed():
    global is_recording

    if is_playing:
        play_pressed()
    if is_recording:
        stop_recording.set()
        is_recording = False
        recordtext.set("Record ({})".format(record_key))
    else:
        is_recording = True
        stop_recording.clear()
        th = threading.Thread(target=record)
        th.start()
        

root = Tk()
root.title("Pymacros")
mainframe = Frame(root)
mainframe.grid(row=0, column=0, sticky=(N,S,W,E))

playtext = StringVar()
recordtext = StringVar()

playtext.set("Play ({})".format(play_key))
recordtext.set("Record ({})".format(record_key))

playbtn = Button(mainframe, textvariable=playtext)
playbtn["command"] = play_pressed
recordbtn = Button(mainframe, textvariable=recordtext)
recordbtn["command"] = record_pressed

if not "last_record.txt" in os.listdir():
    playbtn["state"] = "disabled"

playbtn.grid(column=0, row=0, sticky=(N,S,W,E))
recordbtn.grid(column=1, row=0, sticky=(N,S,E,W))

playbtn["width"] = recordbtn["width"] = 10
playbtn["height"] = 4

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
mainframe.columnconfigure(0, weight=1)
mainframe.columnconfigure(1, weight=1)
mainframe.rowconfigure(0, weight=1)



root.bind("<Key-p>", lambda x: playbtn.invoke())
root.bind("<Key-r>", lambda x: recordbtn.invoke())

root.mainloop()
