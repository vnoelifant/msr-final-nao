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
        self.wavfile = None
        self.recording = False
        self.silent_cnt = SILENCE_COUNT
        self.paused = False
        self.threshold = 3000 # threshold to detect speech

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

            # append buffer to audio buffer
            self.audioBuffer.write(aSoundData[0].tostring())
            
            # speech is detected
            # TODO: Update conditions
            if speech_detected:
                # average out volume of sound data
                self.avg_volume(aSoundData[0])
                # trim silence on both ends of data
                self.trim_silence(aSoundData[0])
                # get audio buffer ready
                self.audio_buffer_ready()
                # pause recording 
                "pausing recording"
                self.pause_recording()

    def is_sound(self, aSoundData):
        "Returns 'True' if sound data past sound threshold"
        return np.amax(aSoundData) > self.threshold

    def is_speech_detected(self,aSoundData):
        "Returns 'True' if speech is detected"
        # True if silence then sound then silence in audio buffer
        pass
    
    def avg_volume(self,aSoundData):
        avg = np.mean(aSoundData)
    
    def trim_silence(self,aSoundData):
        pass

    def audio_buffer_ready(self):
        # set audio data to start of file
        self.audioBuffer.seek(0)

 





       

        
    


    