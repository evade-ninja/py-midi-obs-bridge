#MIDI Bridge
#A bridge between a MIDI control device and obs-websockets

#With ideas borrowed from the examples of obs-websocket-py and Mido

import json
import mido
from obswebsocket import obsws, events

config = {}

def on_obsevent(message):
    print(u"Message Received from OBS:{}".format(message))

def on_obsswitch(message):
    print(u"Scene changed to {}".format(message.getSceneName()))
9
def on_midi_msg(message):
    print(u"MidiMessage:{}".format(message))

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










midin.close()
midout.close()


