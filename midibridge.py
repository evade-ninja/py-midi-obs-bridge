#MIDI Bridge
#A bridge between a MIDI control device and obs-websockets

#With ideas borrowed from the examples of obs-websocket-py and Mido

import json
import mido
from obswebsocket import obsws, events
import time

config = {}

def on_obsevent(message):
    print(u"Message Received from OBS:{}".format(message))

def on_obspreviewswitch(message):
    print(u"Preview Scene changed to {}".format(message.getSceneName()))

def on_obstransition(message):
    print(u"Transition from {} to {}".format(message.getFromScene(), message.getToScene()))

def on_midi_msg(message):
    print(u"MidiMessage:{}".format(message))

def on_obs_ignore(message):
    #do nothing
    return

def midi_send(msg, device):
    print()


#First, load the config file
with open('config.json') as c:
    config = json.load(c)

#print(config)
#print(config['midi_input'])

midin = mido.open_input(config['midi_input'], callback=on_midi_msg)
midout = mido.open_output(config['midi_output'])

#now we connect to OBS
obs = obsws(config['server'], config['port'], config['password'])
#obs.register(on_obsevent)
obs.register(on_obspreviewswitch, events.PreviewSceneChanged)
obs.register(on_obstransition, events.TransitionBegin)
obs.register(on_obs_ignore, events.TransitionEnd)
obs.register(on_obs_ignore, events.TransitionDurationChanged)

obs.connect()

try:
    time.sleep(100)
except KeyboardInterrupt:
        pass

obs.disconnect()
midin.close()
midout.close()


