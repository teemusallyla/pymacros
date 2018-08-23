import threading
import time
from tkinter import *
import time
import json
from pynput.keyboard import Key, Controller, Listener
import os
from Vkmap import Vkmap

# Windows specific libraries
import win32api
import win32con

keyboard = Controller()
key_map = {}
for key in list(Key):
    key_map[key.name] = key

modifier_keys = ["alt", "alt_l", "alt_r", "cmd", "cmd_r",
                 "ctrl", "ctrl_l", "ctrl_r", "shift", "shift_l", "shift_r"]

is_playing = False
is_recording = False
play_key = "P"
record_key = "R"
wait_time = 3
stop_playing = threading.Event()
record_file = "recording.txt"

def windows_keydown(vk):
    win32api.keybd_event(vk, win32api.MapVirtualKey(vk, 0), 0, 0)

def windows_keyup(vk):
    win32api.keybd_event(vk, win32api.MapVirtualKey(vk, 0), win32con.KEYEVENTF_KEYUP, 0)

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

    for x in range(50):
        keys_down = []
        windows_keys_down = []

        for event in events:
            if not "key" in event:
                pass
            else:
                key = event["key"]
                kkey = None
                if len(key) != 1:
                    kkey = key_map[key]

                key = key.lower()

                # modifiers are special keys and therefore handled by the win32api
                #modifiers = [key_map[name] for name in keys_down if name in modifier_keys]
                #with keyboard.pressed(*modifiers):
                #    keyboard.touch(kkey or key, key in keys_down)

                if event["direction"] == "release":
                    if kkey:
                        windows_keyup(kkey.value.vk)
                        windows_keys_down.remove(kkey.value.vk)
                    else:
                        if Vkmap.has(key):
                            windows_keyup(Vkmap.get_vk(key))
                            windows_keys_down.remove(Vkmap.get_vk(key))
                        else:
                            keyboard.release(key)
                            keys_down.remove(key)
                elif event["direction"] == "press":
                    if kkey:
                        windows_keydown(kkey.value.vk)
                        windows_keys_down.append(kkey.value.vk)
                    else:
                        if Vkmap.has(key):
                            windows_keydown(Vkmap.get_vk(key))
                            windows_keys_down.append(Vkmap.get_vk(key))
                        else:
                            keyboard.press(key)
                            keys_down.append(key)


            if "wait" in event:
                if stop_playing.is_set():
                    for key in keys_down:
                        keyboard.release(key)
                    for key in windows_keys_down:
                        windows_keyup(key)
                    stop_playing.clear()
                    clear_playing()
                    return
                else:
                    time.sleep(event["wait"])

        if repeat_playing.is_set():
            for x in range(wait_time, 0, -1):
                if stop_playing.is_set(): break
                playtext.set("Repeating in: " + str(x))
                time.sleep(1)
        if not repeat_playing.is_set() or stop_playing.is_set():
            break
        else:
            playtext.set("Playing...")

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
        with open(record_file) as f:
            events = json.load(f)
        th = threading.Thread(target=play_recording, args=(events,))
        th.start()

def stop_recording():
    global is_recording
    is_recording = False
    to_stop_recording.set()
    recordtext.set("Record ({})".format(record_key))

def on_event(direction):
    def on_event(key):
        global events
        global last_event_fired
        global recording_keys_down
        
        cur_time = time.time()

        if events == []:
            events.append({})

        if key == Key.esc:
            stop_recording()
            return

        if direction == "press" and str(key) in recording_keys_down:
            pass
        else:    
            events[-1]["wait"] = cur_time - last_event_fired
            try:
                events.append({"key": key.name, "direction": direction})
            except AttributeError:
                events.append({"key": key.char, "direction": direction})
            if direction == "press":
                recording_keys_down.append(str(key))
            else:
                recording_keys_down.remove(str(key))

            last_event_fired = cur_time
    return on_event

to_stop_recording = threading.Event()

def record():
    global events
    global last_event_fired
    global recording_keys_down
    
    events = []
    for x in range(wait_time, 0, -1):
        if to_stop_recording.is_set(): return
        recordtext.set(x)
        time.sleep(1)
    recordtext.set("Recording...\n(ESC)")
    last_event_fired = time.time()
    recording_keys_down = []
    recording_thread = Listener(on_press=on_event("press"), on_release=on_event("release"))
    recording_thread.start()
    to_stop_recording.wait()
    recording_thread.stop()
    with open(record_file, "w+") as f:
        json.dump(events, f)

    if playbtn["state"] == "disabled":
        playbtn["state"] = "normal"
    

def record_pressed():
    global is_recording

    if is_playing:
        play_pressed()
    if is_recording:
        stop_recording()
    else:
        is_recording = True
        to_stop_recording.clear()
        th = threading.Thread(target=record)
        th.start()


repeat_playing = threading.Event()
def check_pressed():
    if repeat_playing.is_set():
        repeat_playing.clear()
    else:
        repeat_playing.set()
        
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

if not record_file in os.listdir():
    playbtn["state"] = "disabled"

playbtn.grid(column=0, row=0, sticky=(N,S,W,E))
recordbtn.grid(column=1, row=0, sticky=(N,S,E,W))

playbtn["width"] = recordbtn["width"] = 15
playbtn["height"] = 3

check_box = Checkbutton(mainframe, text="Auto replay", command=check_pressed)
check_box.grid(row=1, column=0, columnspan=2)

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
mainframe.columnconfigure(0, weight=1)
mainframe.columnconfigure(1, weight=1)
mainframe.rowconfigure(0, weight=1)



root.bind("<Key-p>", lambda x: playbtn.invoke())
root.bind("<Key-r>", lambda x: recordbtn.invoke())

root.mainloop()
