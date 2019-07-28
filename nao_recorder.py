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
from raw_to_wav import rawToWav


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
        self.wavfile = None
        self.recording = False
        self.paused = False
        self.silenceBuff = []
        self.threshold = 1400 # threshold to detect speech
        self.speech = []# initialize speech buffer to send for transcription
        self.filename = '' # name of soeech data file
        

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
        self.recording = True
        nNbrChannelFlag = 0; # ALL_Channels: 0,  AL::LEFTCHANNEL: 1, AL::RIGHTCHANNEL: 2; AL::FRONTCHANNEL: 3  or AL::REARCHANNEL: 4.
        nDeinterleave = 0;
        self.nSampleRate = 48000;
        self.CHUNK = 4096
        self.SILENCE_LIMIT = 5 # seconds of silence duration
        self.PREV_AUDIO = 0.5
        self.sub_chunk = self.nSampleRate/self.CHUNK 
        self.silenceBuff = deque(maxlen=self.SILENCE_LIMIT * self.sub_chunk)
        self.ALAudioDevice.setClientPreferences(self.getName(), self.nSampleRate, nNbrChannelFlag, nDeinterleave); # setting same as default generate a bug !?!
        self.ALAudioDevice.subscribe(self.getName());
        print( "SoundReceiver: started!" )

    # resume recording from Naoqi
    def resume_recording(self):
        self.recording = True
        self.paused = False
        print( "SoundReceiver: resuming..." );
    
    # pause recording from Naoqi
    def pause_and_transcribe(self,data): 
        print( "SoundReceiver: pausing..." );
        self.paused = True
        #self.ALAudioDevice.unsubscribe(self.getName()) 
        # convert list to np array
        data = np.asarray(data, dtype=np.int16, order=None)
        self.speech_to_file(data)
        # set recording to stop
        self.recording = False
        # print "reset"
        self.reset()

    def speech_to_file(self,data):
        self.filename = 'output_'+str(int(time.time()))
        outfile = open(self.filename + ".raw", "wb")
        data.tofile(outfile)
        outfile.close()
        print "get to wav format"
        self.rawToWav(self.filename)

    def rawToWav(self,filename):
        rawfile = filename + ".raw"
        if not os.path.isfile(rawfile):
            return

        self.wavfile = wave.open(filename + ".wav", "wb")
        self.wavfile.setframerate(48000)
        self.wavfile.setnchannels(1)
        self.wavfile.setsampwidth(2)

        f = open(rawfile, "rb")
        sample = f.read(4096)
        print 'writing file: ' + filename + '.wav'

        while sample != "":
            outfile.writeframes(sample)
            sample = f.read(4096)

        return self.wavfile
 
    """
    This is the method that receives all the sound buffers from the "ALAudioDevice" module
    """
    def processRemote(self, nbOfChannels, nbrOfSamplesByChannel, aTimeStamp, buffer):
        if self.paused == False:

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
            
            self.silenceBuff.extend(self.audioBuffer)
            # set boolean for whether speech is detected 
            speech_detected = self.is_speech_detected(self.silenceBuff)
            # speech is detected
            if speech_detected:
                # add audio over threshold value to speech buffer
                self.speech.extend(self.audioBuffer)
                # average out volume of sound data
                self.avg_volume(self.speech)
                # pausing recording and getting ready to transcribe
                self.pause_and_transcribe(self.speech)


    def is_speech_detected(self,data):
        "Returns 'True' if speech is detected"
        # True if at least one value of sound detected within silence window
        return (sum([sound > self.threshold for sound in data]) > 0)     
    
    def avg_volume(self,data):
        pass
   
    def reset(self):
        # clear buffers
        self.speech = []
        self.silenceBuff = deque(maxlen=self.SILENCE_LIMIT * self.sub_chunk)
      
    

    
 





       

        
    


    