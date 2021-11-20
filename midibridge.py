#MIDI Bridge
#A bridge between a MIDI control device and obs-websockets

#With ideas borrowed from the examples of obs-websocket-py and Mido

import json
import threading
import mido
from obswebsocket import obsws, events, requests
import time
import hashlib
#import threading
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

def on_obsevent(message):
    print(u"Message Received from OBS:{}".format(message))

def on_obspreviewswitch(message):
    global lastPreview
    global lastScene
    print(u"Preview Scene changed to {}".format(message.getSceneName()))
    sn = message.getSceneName()
    if sn in scenes:            
        if(lastPreview == lastScene):
            midi_send(lastPreview, RED)
            lastPreview = scenes.index(sn)
            midi_send(scenes.index(sn), GREEN)
        elif(lastScene == scenes.index(sn)):
            midi_send(lastPreview, COLOR_OFF)
            lastPreview = scenes.index(sn)
            midi_send(scenes.index(sn), RED)
        else:
            midi_send(lastPreview, COLOR_OFF)
            lastPreview = scenes.index(sn)
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
    print(u"Transition from {} to {}".format(message.getFromScene(), message.getToScene()))
    global lastScene
    sn = message.getToScene()
    if sn in scenes:
        midi_send(lastScene, COLOR_OFF)
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

    if message.note < 8:
        obs.call(requests.SetPreviewScene(scenes[message.note]))
        return
    
    if message.note == B_TRANSITION:
        obs.call(requests.TransitionToProgram())
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

midin = mido.open_input(config['midi_input'], callback=on_midi_msg)
midout = mido.open_output(config['midi_output'])

#print(config)
#print(config['midi_input'])



#now we connect to OBS
obs = obsws(config['server'], config['port'], config['password'])
#obs.register(on_obsevent)
obs.register(on_obspreviewswitch, events.PreviewSceneChanged)
obs.register(on_obstransition, events.TransitionBegin)
obs.register(on_obs_ignore, events.TransitionEnd)
obs.register(on_obs_ignore, events.TransitionDurationChanged)
obs.register(on_obs_scenes, events.ScenesChanged)
obs.register(on_obs_recstarted, events.RecordingStarted)
obs.register(on_obs_recpaused, events.RecordingPaused)
obs.register(on_obs_recstopped, events.RecordingStopped)
obs.register(on_obs_streamstarted, events.StreamStarted)
obs.register(on_obs_streamstopped, events.StreamStopped)

#obs.register(on_obs_scenes, events.SceneCollectionChanged)

obs.connect()

#get all the scenes
allscenes = obs.call(requests.GetSceneList())
for s in allscenes.getScenes():
    sname = s['name']
    scenes.append(sname)

#get the current scene
ps = obs.call(requests.GetPreviewScene())
lastPreview = scenes.index(ps.getName())
midi_send(lastPreview, GREEN)

cs = obs.call(requests.GetCurrentScene())
lastScene = scenes.index(cs.getName())
midi_send(lastScene, RED)

#get recording/streaming statuses
ss = obs.call(requests.GetStreamingStatus())
if(ss.getStreaming()):
    midi_send(L_STREAM, GREEN)
else:
    midi_send(L_STREAM, PURPLE)

if(ss.getRecording()):
    midi_send(L_RECSTAT, RED)
else:
    midi_send(L_RECSTAT, COLOR_OFF)

#midi_send(L_CONNECT, BLUE)
midi_send(B_TRANSITION, ORANGE)
midi_send(8, TEAL)
midi_send(9, YELLOW)
midi_send(10, PINK)
midi_send(11, LIME)



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


