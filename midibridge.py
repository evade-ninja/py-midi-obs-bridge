#MIDI Bridge
#A bridge between a MIDI control device and obs-websockets

#With ideas borrowed from the examples of obs-websocket-py and Mido

import json
import threading
import mido
from obswebsocket import obsws, events, requests
import time
import hashlib
from threading import Thread, Timer

config = {}
scenes = []
lastScene = 0
lastPreview = 0
streaming = False
connected = False

#First, load the config file
with open('config.json') as c:
    config = json.load(c)

COLOR_OFF = 0
RED = 1
YELLOW = 2
GREEN = 3
TEAL = 4
BLUE = 5
PURPLE = 6
PINK = 7
ORANGE = 8
LIME = 9

L_CONNECT = 18
L_STREAM = 19
L_RECSTAT = 20

B_TRANSITION = 17
B_STAR = 16
B_LEFT = 14
B_RIGHT = 15
B_TITLE = 16
B_NEXT = 15
B_PREV = 14

MAX_CAM = 14 #highest number of scenes (was 14)

def on_obsevent(message):
    print(u"Message Received from OBS:{}".format(message))

def on_obspreviewswitch(message):
    global lastPreview
    global lastScene
    print(u"Preview Scene changed to {}".format(message.datain['sceneName']))
    sn = message.datain['sceneName']
    if sn in scenes:            
        if(lastPreview == lastScene):
            if lastPreview < MAX_CAM:
                midi_send(lastPreview, RED)
            lastPreview = scenes.index(sn)
            if scenes.index(sn) < MAX_CAM:
                midi_send(scenes.index(sn), GREEN)
        elif(lastScene == scenes.index(sn)):
            if lastPreview < MAX_CAM:
                midi_send(lastPreview, COLOR_OFF)
            lastPreview = scenes.index(sn)
            if scenes.index(sn) < MAX_CAM:
                midi_send(scenes.index(sn), RED)
        else:
            if lastPreview < MAX_CAM:
                midi_send(lastPreview, COLOR_OFF)
            lastPreview = scenes.index(sn)
            if scenes.index(sn) < MAX_CAM:
                midi_send(scenes.index(sn), GREEN)
    else:
        print("cant find scene {}".format(sn))

def midi_send(ch, color):
    midout.send(mido.Message('control_change', channel=0, control=ch, value=color))

def alive_thread():
    while(1):
        send_alive()
        time.sleep(4)

def send_alive():
    midout.send(mido.Message('program_change', channel=0, program=1))
    print("keepalive!")

def on_obstransition(message):
    print(u"Transition to {}".format(
        message.datain['sceneName']))
    global lastScene
    sn = message.datain['sceneName']
    if sn in scenes:
        if lastScene < MAX_CAM:
            midi_send(lastScene, COLOR_OFF)
        if scenes.index(sn) < MAX_CAM:
            midi_send(scenes.index(sn), RED)
        lastPreview = scenes.index(sn)
        lastScene = scenes.index(sn)
    else:
        print("cant find scene {}".format(sn))

def on_midi_msg(message):
    if(message.type == "note_off"):
        return

    print(u"MidiMessage:{}".format(message))

    if(message.type != "note_on"):
        print("not a button press!")
        return
    print(message.note)

    if message.note < MAX_CAM:
        obs.call(requests.SetCurrentPreviewScene(sceneName=scenes[message.note]))
        return
    
    if message.note == 12:
        obs.call(requests.TriggerHotkeyBySequence(keyId="OBS_KEY_F17", keyModifiers=""))
        return

    if message.note == 13:
        obs.call(requests.TriggerHotkeyBySequence(keyId="OBS_KEY_F16", keyModifiers=""))
        #obs.call(requests.TriggerHotkeyByName(
        #    hotkeyName="A_SWITCH_1"))
        return

    if message.note == B_TRANSITION:
        obs.call(requests.TriggerStudioModeTransition())
        return
    
    if message.note == B_TITLE:
        #obs.call(requests.TriggerHotkeyBySequence(keyId="OBS_KEY_F13", keyModifiers=""))
        #obs.call(requests.TriggerHotkeyByName(
        #    hotkeyName="A_SWITCH_1"))
        obs.call(requests.CallVendorRequest(vendorName="obs-browser",
                 requestType="emit_event", requestData={'event_name': 'otfShow', 'event_data':'hotkey'}))
        return
    
    if message.note == B_NEXT:
        #keyboard.send("F15")
        #obs.call(requests.TriggerHotkeyByName("hotkeyLyricSwitch1"))
        obs.call(requests.CallVendorRequest(vendorName="obs-browser",
                 requestType="emit_event", requestData={'event_name': 'lyr_next', 'event_data': 'hotkey'}))
        print("next!")
        return

    if message.note == B_PREV:
        obs.call(requests.CallVendorRequest(vendorName="obs-browser",
                 requestType="emit_event", requestData={'event_name': 'lyr_prev', 'event_data': 'hotkey'}))
        return


def on_obs_scenes(message):
    print("Scenes Changed:\n {}".format(message.getScenes()))

def on_obs_ignore(message):
    #do nothing
    return

def on_obs_recstarted(message):
    midi_send(L_RECSTAT, RED)

def on_obs_recpaused(message):
    midi_send(L_RECSTAT, PURPLE)

def on_obs_recstopped(message):
    midi_send(L_RECSTAT, COLOR_OFF)

def on_obs_streamstarted(message):
    midi_send(L_STREAM, GREEN)

def on_obs_streamstopped(message):
    midi_send(L_STREAM, PURPLE)

def on_exit(message):
    quit()

midin = mido.open_input(config['midi_input'], callback=on_midi_msg)
midout = mido.open_output(config['midi_output'])

#now we connect to OBS
obs = obsws(config['server'], config['port'], config['password'])
#obs.register(on_obsevent)
obs.register(on_obspreviewswitch, events.CurrentPreviewSceneChanged)
obs.register(on_obstransition, events.CurrentProgramSceneChanged)
obs.register(on_obs_ignore, events.TransitionEnd)
obs.register(on_obs_ignore, events.TransitionDurationChanged)
obs.register(on_obs_scenes, events.ScenesChanged)
obs.register(on_obs_recstarted, events.RecordingStarted)
obs.register(on_obs_recpaused, events.RecordingPaused)
obs.register(on_obs_recstopped, events.RecordingStopped)
obs.register(on_obs_streamstarted, events.StreamStarted)
obs.register(on_obs_streamstopped, events.StreamStopped)
#obs.register(on_exit, events.Exiting)

#obs.register(on_obs_scenes, events.SceneCollectionChanged)

obs.connect()

#get all the scenes
allscenes = obs.call(requests.GetSceneList())
thescenes = allscenes.datain['scenes']
thescenes.reverse()
for s in thescenes:
    sname = s['sceneName']
    scenes.append(sname)
#allscenes.datain['scenes'][0]
#get the current program & preview scenes
lastPreview = scenes.index(allscenes.datain['currentPreviewSceneName'])
midi_send(lastPreview, GREEN)

lastScene = scenes.index(allscenes.datain['currentProgramSceneName'])
midi_send(lastScene, RED)

#get recording/streaming statuses
ss = obs.call(requests.GetStreamStatus())
if(ss.datain['outputActive']):
    midi_send(L_STREAM, GREEN)
else:
    midi_send(L_STREAM, PURPLE)

sr = obs.call(requests.GetRecordStatus())
if(sr.datain['outputActive']):
    midi_send(L_RECSTAT, RED)
else:
    midi_send(L_RECSTAT, COLOR_OFF)

#midi_send(L_CONNECT, BLUE)
#default colors:

midi_send(B_TRANSITION, ORANGE)
midi_send(12, TEAL)
midi_send(13, YELLOW)
midi_send(B_NEXT, LIME)
midi_send(B_PREV, PINK)
midi_send(B_TITLE, BLUE)

print(obs.call(requests.GetHotkeyList()))

#t = threading.Thread(target=alive_thread)
#t.start()

try:
    while 1:
        time.sleep(1)
        midout.send(mido.Message('program_change', channel=0, program=1))
        #midi_send(50, COLOR_OFF)
        #print("keepalive")
except KeyboardInterrupt:
        pass

obs.disconnect()
midin.close()
midout.close()


