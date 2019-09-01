# -*- coding: utf-8 -*-

###########################################################
# Retrieve NAO  audio buffer
###########################################################
from optparse import OptionParser
from naoqi import ALModule, ALProxy,ALBroker
import numpy as np
import time
import sys
import os
import audioop
import math
import wave
from os.path import join, dirname
import json
import StringIO
from struct import pack
#from array import array
from optparse import OptionParser
import naoqi
from naoqi import ALModule, ALProxy, ALBroker
import numpy as np
import time
import StringIO
import sys
import os
import wave
from os.path import join, dirname
import json
from threading import Thread
import json
from ibm_watson import SpeechToTextV1, AssistantV1
import traceback
import logging
import StringIO
from collections import deque
import sys



# Reference: https://www.generationrobots.com/media/NAO%20Next%20Gen/FeaturePaper(AudioSignalProcessing)%20(1).pdf
"""

To  access  to  the  sound  data  coming  from  NAO’s  microphones,  the  user  first  has  to  create a NAOqi module 
(in C++ or Python language) which contains a callback function 
called «processSound» or «processSoundRemote» depending on whether the module is executed locally or remotly. Then,  to  start  
receiving  the    audio  buffers,  this  module  simply  has  to  call  the  subsribeLocalModule   or   subsribeRemoteModule   
function   of   the   ALAudioDevice   module (depending on whether the module is executed locally or remotely).Every  time  an  
audio  buffer  is  ready  for  processing,  the  ALAudioDevice  module  will  send  it  through  the  processSound  or  
processSoundRemote  function.  The  received  buffer  contains  the  4  16-bit  microphone  signals  sampled  at  48kHz.  
These  samples  are interleaved, that is to say that the buffer contains s1m1, s1m2, s1m3, s1m4, s2m1, s2m2, ... 
where simj is the sample number i of microphone j. The order of microphones is  as  follows:  1:  left  microphone  /  2:  
right  microphone  /  3:  front  microphone  /  4:  rear  microphone.


"""
class SoundReceiverModule(ALModule):
    """
    Custom Module to access the microphone data from Nao. Module inherited from Naoqi ALModule.
    """
    def __init__(self, strModuleName, strNaoIp):
        try:
            ALModule.__init__(self, strModuleName);
        except Exception as e:
            logging.error(str(e))
            pass
        print("connected")
        self.strNaoIp = strNaoIp;
        self.BIND_PYTHON(strModuleName,"processRemote")
        self.ALAudioDevice = ALProxy("ALAudioDevice", self.strNaoIp, 9559)
        self.audioBuffer = "" # initialize buffer to hold incoming data from Nao mic
        self.recording = True
        self.wavfile = None
        self.recording_in_progress = False
        self.silenceBuff = []
        self.threshold = 4000 # threshold to detect speech
        self.speech = []# initialize speech buffer to send for transcription
        self.avg = [] # averaged out speech buffer data
        self.maximum = 16384 # frame length for volume average
        self.num_silence = 0
        self.start_silence = False


    """
    module subscribe:
    This function allows a module which inherits from the ALSoundExtractor class to subscribe to the ALAudioDevice module. Once the module is subscribed, the function ‘process’ of the module (the module needs to contain one) will be automatically and regularly called with raw data from microphones as inputs. The call to this method can be replaced by a call to startDetection() within a NAOqi module that inherits from ALSoundExtractor.

    The callback function must be declared as follows:
    process(const int & nbOfChannels, const int & nbrOfSamplesByChannel, const AL_SOUND_FORMAT * buffer, const ALValue & timeStamp)
    Parameters: 

    module – This module must inherits from ALSoundExtractor

    module setClientPreferences:
    By using this method a module can specify the format of the signal that will be sent after subscribing to ALAudioDevice. If no call to this method is made, the default format sent to this module is 4 channels interleaved at 48000Hz. Note that for now, only the following combinations are available:

    four channels interleaved, 48000Hz, (default setting)
    four channels deinterleaved, 48000Hz
    one channels (either front, rear, left or right), 16000Hz

    This call must be made before the call to ALAudioDeviceProxy::subscribe() or startDetection() to be taken into account.

`   """
    # subscribe to NAOQI Audio device and start recording 
    def start_recording(self): 
        self.num_silence = 0
        self.recording = True
        self.recording_in_progress = False
        nNbrChannelFlag = 0; # ALL_Channels: 0,  AL::LEFTCHANNEL: 1, AL::RIGHTCHANNEL: 2; AL::FRONTCHANNEL: 3  or AL::REARCHANNEL: 4.
        nDeinterleave = 0;
        self.nSampleRate = 48000;
        self.CHUNK = 4096
        self.PADDING = 3 #3
        self.threshold = 4000
        self.maximum = 16384
        self.sub_chunk = self.nSampleRate/self.CHUNK 
        # buffer for discarding silence
        self.silenceBuff = deque(maxlen=self.CHUNK)
        # buffer for prepending and adding silence to speech buffer to not miss the start and end
        # of speech; avoids "chopped off" speech
        self.padding = deque(maxlen=self.PADDING * self.sub_chunk) 
        self.ALAudioDevice.setClientPreferences(self.getName(), self.nSampleRate, nNbrChannelFlag, nDeinterleave); # setting same as default generate a bug !?!
        self.ALAudioDevice.subscribe(self.getName());
        print( "SoundReceiver: started!" )

    # resume recording from Naoqi
    def resume_recording(self):
        print( "SoundReceiver: resuming..." );
        print "resetting"
        self.recording = True
        self.recording_in_progress = False
        self.reset()
    # pause recording from Naoqi
    def pause_and_transcribe(self): 
        print( "SoundReceiver: pausing..." );
        print "ready to transcribe, audio to wav"
        self.rawToWav()
        self.recording = False

    # convert raw audio to wav file
    def rawToWav(self):
        # get data formatted to convert to .wav audio file
        # self.avg = np.asarray(self.avg, dtype=np.int16, order=None)
        # self.avg = str(bytearray(self.avg))
        self.speech = np.asarray(self.speech, dtype=np.int16, order=None)
        self.speech = str(bytearray(self.speech))
        filename = "myspeech"
        self.wavfile = wave.open(filename + '.wav', 'wb')
        self.wavfile.setnchannels(1)
        self.wavfile.setsampwidth(2)
        self.wavfile.setframerate(48000)  
        # self.wavfile.writeframes(self.avg)
        self.wavfile.writeframes(self.speech)
        self.wavfile.close()
        return filename + '.wav'
   
    """
    This is the method that receives all the sound buffers from the "ALAudioDevice" module
    """
    def processRemote(self, nbOfChannels, nbrOfSamplesByChannel, aTimeStamp, buffer):
        # This method receives the streaming microphone data. The buffer parameter contains an 
        # array of bytes that was read from the microphone
        # get sound data  
        aSoundDataInterlaced = np.fromstring(str(buffer), dtype=np.int16);
        # reshape data
        aSoundData = np.reshape(aSoundDataInterlaced,(nbOfChannels, nbrOfSamplesByChannel), 'F');
        # add sound data to buffer
        self.audioBuffer = aSoundData[0]
        #convert buffer to list
        self.audioBuffer = self.audioBuffer.tolist()
        # throw away sound data below threshold value into a "silence" buffer
        #print "sound not over threshold"
        self.silenceBuff.extend(self.audioBuffer)
        # returns True for whether sound is detected 
        sound_detected = self.is_sound_detected(self.silenceBuff)
        # returns True for whether speech is detected
        # detected speech is sound surrounded by silence: silence, sound, silence
        speech_detected = self.is_speech_detected()

        # add audio data to speech buffer if sound data over threshold
        if sound_detected:
            #print "detected sound"
            self.num_silence = 0
            print self.num_silence
            if not self.recording_in_progress:
                print "starting record of phrase"
                self.recording_in_progress = True
            self.speech.extend(self.audioBuffer)
            self.num_silence += 1

        #speech is detected 
        elif speech_detected:
            print "detected speech, ready to transcribe"
            self.speech = list(self.padding) + (self.speech)
            self.speech.extend(list(self.padding))
            #self.avg_volume()
            print "pausing recording and getting ready to transcribe"
            self.pause_and_transcribe()

        # add sound data to silence padding to be prepended and appended to 
        # speech data
        else:
            # self.start_silence = True
            #print "sound not over threshold and adding to silence padding buffer"
            self.num_silence += 1
            print self.num_silence
            self.padding.extend(self.audioBuffer)

    def is_sound_detected(self,data):
        "Returns 'True' if sound is detected"
        # True if at least one value of sound detected within silence window
        return (sum([sound > self.threshold for sound in data]) > 0)     

    def is_speech_detected(self):
        "Returns 'True' if speech is detected"
        return self.recording_in_progress and self.num_silence >= 25 # before, 20 ok but riskier, need to wait more to speak for more accuracy
    
    def avg_volume(self):
        norm = float(self.maximum)/max(abs(sound) for sound in self.speech)

        for sound in self.speech:
            self.avg.append(int(sound*norm))
   
    def reset(self):
        self.speech = []
        self.avg = []
        self.audioBuffer = ""
        self.num_silence = 0
        nNbrChannelFlag = 0; # ALL_Channels: 0,  AL::LEFTCHANNEL: 1, AL::RIGHTCHANNEL: 2; AL::FRONTCHANNEL: 3  or AL::REARCHANNEL: 4.
        nDeinterleave = 0;
        self.silenceBuff = deque(maxlen=self.CHUNK)
        self.padding = deque(maxlen=self.PADDING * self.sub_chunk) 
        self.ALAudioDevice.setClientPreferences(self.getName(), self.nSampleRate, nNbrChannelFlag, nDeinterleave); 
        self.ALAudioDevice.subscribe(self.getName());



    
 





       

        
    


    
