#MIDI Bridge
#A bridge between a MIDI control device and obs-websockets

#With ideas borrowed from the examples of obs-websocket-py and Mido

import json
import mido
from obswebsocket import obsws, events, requests
import time
import hashlib

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

L_CONNECT = 18
L_STREAM = 19
L_RECSTAT = 20

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
    obs.call(requests.SetPreviewScene(scenes[message.note]))

def on_obs_scenes(message):
    print("Scenes Changed:\n {}".format(message.getScenes()))

def on_obs_ignore(message):
    #do nothing
    return



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
#obs.register(on_obs_scenes, events.SceneCollectionChanged)

obs.connect()

#get all the scenes
allscenes = obs.call(requests.GetSceneList())
for s in allscenes.getScenes():
    sname = s['name']
    scenes.append(sname)

#get the current scene
cs = obs.call(requests.GetCurrentScene())
lastScene = scenes.index(cs.getName())
midi_send(lastScene, RED)

ps = obs.call(requests.GetPreviewScene())
lastPreview = scenes.index(ps.getName())
midi_send(lastPreview, GREEN)

ss = obs.call(requests.GetStreamingStatus())



try:
    while 1:
        time.sleep(100)
except KeyboardInterrupt:
        pass

obs.disconnect()
midin.close()
midout.close()


