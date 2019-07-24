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

# set silence count for silence detection counting
SILENCE_COUNT = 0
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
        self.audioBuffer = None
        # create previous sound data to add to buffer before peak sound reached
        self.previous_sound = None
        self.wavfile = None
        self.recording = False
        self.silent_cnt = SILENCE_COUNT
        self.paused = False
        self.threshold = 14000 # threshold to detect speech

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
        nSampleRate = 48000;
        self.ALAudioDevice.setClientPreferences(self.getName(), nSampleRate, nNbrChannelFlag, nDeinterleave); # setting same as default generate a bug !?!
        self.ALAudioDevice.subscribe(self.getName());
        # create in memory buffer file
        self.audioBuffer = StringIO.StringIO()
        print( "SoundReceiver: started!" )

    # resume recording from Naoqi
    def resume_recording(self):
        self.recording = True
        # recreate in memory buffer file
        self.audioBuffer = StringIO.StringIO()
        self.paused = False
        print( "SoundReceiver: resuming..." );
        #print "pause flag",self.paused
    
    # pause recording from Naoqi
    def pause_recording(self): 
        print( "SoundReceiver: pausing..." );
        self.paused = True
        #self.ALAudioDevice.unsubscribe(self.getName()) # error when here
        # get audio in wav format
        self.rawToWav(self.audioBuffer)
        # set recording to stop
        self.recording = False

    def rawToWav(self,data):
        #filename = 'output_'+str(int(time.time()))
        filename = "myspeech16"
        data = ''.join(data)
        self.wavfile = wave.open(filename + '.wav', 'wb')
        self.wavfile.setnchannels(1)
        self.wavfile.setsampwidth(2)
        self.wavfile.setframerate(48000)  
        self.wavfile.writeframes(data)
        self.wavfile.close()
        return filename + '.wav'
  
    """
    This is the method that receives all the sound buffers from the "ALAudioDevice" module
    """
    def processRemote(self, nbOfChannels, nbrOfSamplesByChannel, aTimeStamp, buffer):
        #print "pause flag",self.paused
        if self.paused == False:

            # This method receives the streaming microphone data. The buffer parameter contains an 
            # array of bytes that was read from the microphone
            # get sound data
            aSoundDataInterlaced = np.fromstring(str(buffer), dtype=np.int16);
           
            # reshape data
            aSoundData = np.reshape(aSoundDataInterlaced,(nbOfChannels, nbrOfSamplesByChannel), 'F');

            # increment silence count if sound below threshold)
            self.silent_cnt += 1
            # create previous sound data to add to buffer before peak sound reached
            self.previous_sound = aSoundData
            # write audio data to in memory file
            self.audioBuffer.write(aSoundData[0].tostring())
            
            # detected speech (above sound threshold)
            speech_at_peak = self.is_speech_at_peak(aSoundData)
            
            # sound at peak conditions
            if speech_at_peak:
                # reset silence count
                self.silent_cnt = SILENCE_COUNT
                # add sound data to buffer before peak sound
                self.add_previous_sound(self.previous_sound)
        
            # speech is detected if silence is detected for over 10 counts
            if self.silent_cnt == 12: #and self.paused == False:
                # average out volume of sound data
                self.avg_volume(aSoundData[0])
                # trim silence on both ends of data
                self.trim_silence(aSoundData[0])
                # get audio buffer ready
                self.audio_buffer_ready()
                # pause recording 
                "pausing recording"
                self.pause_recording()
            

    def is_speech_at_peak(self, aSoundData):
        "Returns 'True' if sound data at peak"
        return np.amax(aSoundData) > self.threshold

    def add_previous_sound(self,previous_sound):
        if not previous_sound is None:
            self.audioBuffer.write(previous_sound[0].tostring())

    def avg_volume(self,aSoundData):
        avg = np.mean(aSoundData)
    
    def trim_silence(self,aSoundData):
        pass

    def audio_buffer_ready(self):
        # clear previous sound buffer
        self.previous_sound = None
        print "pre audio buffer when clear",self.previous_sound
        # set audio data to start of file
        self.audioBuffer.seek(0)
        print "raw audio buffer contents",self.audioBuffer
 





       

        
    


    