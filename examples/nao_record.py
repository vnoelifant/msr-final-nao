import time
from naoqi import ALProxy
from os.path import expanduser
import os
import sys
from os.path import expanduser
import os
import time

ROBOT_IP = "169.254.126.202"

CHANNELS = [0, 0, 1, 0]

ar = ALProxy("ALAudioRecorder", ROBOT_IP, 9559)
ap = ALProxy("ALAudioPlayer", ROBOT_IP, 9559)

def record_sound():
	AUDIO_FILE = '/home/nao/test.wav'
	ar.startMicrophonesRecording(AUDIO_FILE,"wav", 16000, CHANNELS)
	print "Audio recorder started recording"
	time.sleep(10)

	ar.stopMicrophonesRecording()
	print "Audio recorder stopped recording"
	fileId = ap.post.playFile(AUDIO_FILE)


if __name__ == "__main__":

	record_sound()

