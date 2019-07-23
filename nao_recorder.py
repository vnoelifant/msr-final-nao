# -*- coding: utf-8 -*-

###########################################################
# Retrieve NAO  audio buffer
# Syntax
#    python scriptname --pip <ip> --pport <port>
# 
#    --pip <ip>: specify the ip of your robot (without specification it will use NAO_IP variable defined
# in main program (nao_stt_tts.py)

###########################################################


#~ NAO_IP = "10.0.253.99" # Nao Alex Blue


from optparse import OptionParser
#import naoqi
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
# Reference: 


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
        self.wavfile = None
        self.recording = False
        self.silent_cnt = SILENCE_COUNT
        self.pause_recording = False
        self.silence = 4000 # threshold to detect silence 
        # buffer for audio sound
        
        # buffer for silence
        #self.silenceBuffer = []
        #self.silent_cnt = 0

    # __init__ - end of program
    #def __del__(self):
    #    print( "SoundReceiverModule.__del__: cleaning everything");  
    #    self.stop_recording();

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

    # start recording
    def start_recording(self): 
        self.recording = True
        nNbrChannelFlag = 0; # ALL_Channels: 0,  AL::LEFTCHANNEL: 1, AL::RIGHTCHANNEL: 2; AL::FRONTCHANNEL: 3  or AL::REARCHANNEL: 4.
        nDeinterleave = 0;
        nSampleRate = 48000;
        self.ALAudioDevice.setClientPreferences(self.getName(), nSampleRate, nNbrChannelFlag, nDeinterleave); # setting same as default generate a bug !?!
        self.ALAudioDevice.subscribe(self.getName());
        self.audioBuffer = StringIO.StringIO()
        print "audio buffer when recording",self.audioBuffer.getvalue()
        print( "SoundReceiver: started!" )

    # resume recording from Naoqi
    def resume_recording(self):
        self.pause_recording = False
        print( "SoundReceiver: resuming..." );
        #self.pause_recording = False
        #self.start_recording()
        #print "pause flag",self.pause_recording
    # pause recording from Naoqi
    def paus_recording(self): 
        print( "SoundReceiver: pausing..." );
        self.pause_recording = True
        #print "pause flag",self.pause_recording
        #self.ALAudioDevice.unsubscribe(self.getName()) # error when here
        print "convert raw audio to wav"  
        print "audio buffer before wav",self.audioBuffer
        # get audio in wav format
        self.rawToWav(self.audioBuffer)
        print "clearing audio buffer"  
        # clear audio buffer 
        self.clear_audio_buffer()
        print "reset recording flag to false"
        # set recording to stop
        self.recording = False
        #self.ALAudioDevice.unsubscribe(self.getName())
        #self.recording = True
        # put a flag on processRemote

    def rawToWav(self,data):
        #filename = 'output_'+str(int(time.time()))
        filename = "myspeech9"
        print "data type", type(data)
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
        #print "pause flag",self.pause_recording
        if self.pause_recording == False:

            # This method receives the streaming microphone data. The buffer parameter contains an 
            # array of bytes that was read from the microphone
            # get sound data
            aSoundDataInterlaced = np.fromstring(str(buffer), dtype=np.int16);
           
            # reshape data
            aSoundData = np.reshape(aSoundDataInterlaced,(nbOfChannels, nbrOfSamplesByChannel), 'F');

            print aSoundData
            print len(aSoundData)
            print type(aSoundData),aSoundData.shape
            print np.amax(aSoundData)
            
            # sound is below threshold and detected as silence
            sound_silent = self.is_silence(aSoundData)
            
            # set conditions to detect speech
            speech = False
            
            # increment silence count if silence detected
            if sound_silent:
                print "detected silence"
                print "silence speech flag", speech
                self.silent_cnt += 1
                print "silence count",self.silent_cnt
                #self.audioBuffer.write(aSoundData[0].tostring())
            # speech detected: reset silence count to zero and set speech flag to True
            else:
                print "detected speech"
                #self.silent_cnt = SILENCE_COUNT
                print "detected speech silence count",self.silent_cnt
                speech = True
                print "detected speech flag", speech
            self.audioBuffer.write(aSoundData[0].tostring())
           
            # speech is detected if sound reached peak,is surrounded by silence, and silence
            # is detected for over 10 counts
            if speech == True and self.silent_cnt >= 10:
                print "detected speech data", aSoundData[0],len(aSoundData[0]),type(aSoundData[0])
                # average out volume of sound data
                self.avg_volume(aSoundData[0])
                # trim silence on both ends of data
                self.trim_silence(aSoundData[0])
                # add detected speech to sound buffer
                self.add_to_buffer(aSoundData[0])
                # pause recording 
                "pausing recording"
                self.paus_recording()
        else:
            print "paused!!!!!!!!!!!!!!!!!"
            # 1. why printing pause?
            # 2. why does after it transcribe once does it keep transcribing
            # what could be causing this?
            # what is the data that I am getting? might need to save data across multiple process data
            # append to buffer until detect silence 
            # how long is audio sample 
            # getting different data and different sentences
            # save data from previous
            # process buffer
            # no sound sound no sound
            # keep adding sound to buffer
            # run detection on whole buffer
            # when there is a sentence save to wav file. Clear audio buffer, trimming silence
            # has a sentence been uttered
            # if yes, send to watson
            # add to buffer when something to send to watson, enough non-silence
            # 3. why index in range error?
            # blocking main thread, does main thread continue 
            # processRemote is running in background 
            # send more than 1 processRemote function


    def is_silence(self, aSoundData):
        "Returns 'True' if sound data below peak sound threshold"
        return np.amax(aSoundData) < self.silence 

    def avg_volume(self,aSoundData):
         #avg = np.mean(aSoundData, axis = 1)
         #print "avg: %s" % avg
        pass
 
    def trim_silence(self,aSoundData):
        pass

    def add_to_buffer(self,aSoundData):
        print "adding raw speech data to audio buffer"
        self.audioBuffer.write(aSoundData.tostring())
        # set data to start of file
        self.audioBuffer.seek(0)
        print "raw audio buffer contents",self.audioBuffer
    def clear_audio_buffer(self):
        print "clearing the audio buffer"
        self.audioBuffer = None
        print "audio buffer when clear",self.audioBuffer

    



       

        
    


    