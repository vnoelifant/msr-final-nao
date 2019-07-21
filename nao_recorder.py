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
import naoqi
import numpy as np
import time
import sys
import os
import wave
from os.path import join, dirname
import json


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

# TODO: 
# add new stub functions
# add silence detection and peak sound variables to know when to stop recording
class SoundReceiverModule(naoqi.ALModule):
    """
    Custom Module to access the microphone data from Nao. Module inherited from Naoqi ALModule.
    """
    def __init__(self, strModuleName, strNaoIp):
        try:
            naoqi.ALModule.__init__(self, strModuleName );
            self.BIND_PYTHON( self.getName(),"processRemote");
            self.strNaoIp = strNaoIp;
            self.outfile = None;
            self.aOutfile = [None]*(4-1); # ASSUME max nbr channels = 4
            self.wavfile = None;
            self.recording = False
        except BaseException, err:
            print( "ERR: SoundReceiverModule: loading error: %s" % str(err) );

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
        audio = naoqi.ALProxy( "ALAudioDevice", self.strNaoIp, 9559);
        nNbrChannelFlag = 0; # ALL_Channels: 0,  AL::LEFTCHANNEL: 1, AL::RIGHTCHANNEL: 2; AL::FRONTCHANNEL: 3  or AL::REARCHANNEL: 4.
        nDeinterleave = 0;
        nSampleRate = 48000;
        audio.setClientPreferences(self.getName(),  nSampleRate, nNbrChannelFlag, nDeinterleave); 
        audio.subscribe(self.getName() );
        print( "SoundReceiver: started!" );

    # stop recording and unsubscribe from Naoqi
    def stop_recording(self): 
        print( "INF: SoundReceiver: stopping..." );
        audio = naoqi.ALProxy( "ALAudioDevice", self.strNaoIp, 9559);
        audio.unsubscribe( self.getName());    
        print( "INF: SoundReceiver: stopped!" );
        # get audio in wav format
        self.rawToWav('test')
        #if( self.wavfile != None ):
            #self.wavfile.close();
        # clear audio buffer 
        self.clear_sound_buffer()
        # set recording to stop
        self.recording = False



    def rawToWav(self,filename):
        #print("self.outfile",self.outfile)
        rawfile = filename + ".raw"
        if not os.path.isfile(rawfile):
            return
        self.wavfile = wave.open(filename + ".wav", "wb")
        self.wavfile.setframerate(48000) # from Naoqi ALAudioDevice API
        self.wavfile.setnchannels(1)
        self.wavfile.setsampwidth(2)
        # number of frames is 1024. 4 bytes per frame = 4096 = block size
        f = open(rawfile, "rb")
        sample = f.read(4096)
        #print 'writing file: ' + (self.wavfile);
        print 'writing file: ' + filename + '.wav'
        while sample != "":
            self.wavfile.writeframes(sample)
            sample = f.read(4096)
        #os.remove(rawfile)
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
        aSoundData = np.reshape(aSoundDataInterlaced, (nbOfChannels, nbrOfSamplesByChannel), 'F');
        # save to file
        if(self.outfile == None):
            strFilenameOut = "test20.raw";
            print( "Writing sound to '%s'" % strFilenameOut);
            self.outfile = open( strFilenameOut, "wb");
     
            for nNumChannel in range( 1, nbOfChannels ):
                strFilenameOutChan = strFilenameOut.replace(".raw", "_%d.raw"%nNumChannel);
                self.aOutfile[nNumChannel-1] = open( strFilenameOutChan, "wb" );
                print( "Writing other channel sound to '%s'" % strFilenameOutChan );
            
        #tofile: Write array to a file as text or binary (default).
        # aSoundDataInterlaced.tofile(self.outfile ); # write 4 channels
        aSoundData[0].tofile(self.outfile); # write only one channel
          
        for nNumChannel in range( 1, nbOfChannels ):
            aSoundData[nNumChannel].tofile(self.aOutfile[nNumChannel-1]); 
        
        # condition on detecting speech to be transcribed
        speech_detected = self.speech_detected()
        if speech_detected:
            # trim silence on both ends of data
            self.trim_silence()
            # add detected speech to sound buffer
            self.add_to_buffer()
            # stop recording 
            self.stop_recording()

    def speech_detected():
        pass

    def trim_silence():
        pass

    def add_to_buffer():
        pass

    def clear_audio_buffer():
        pass



       

        
    


    