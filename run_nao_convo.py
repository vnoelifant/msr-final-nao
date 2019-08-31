###########################################################
# Main program to converse with Nao
# Syntax
#    python scriptname --pip <ip> --pport <port>
# 
#    --pip <ip>: specify the ip of your robot (without specification it will use NAO_IP variable defined
# in main program)

###########################################################
import os
import json
from optparse import OptionParser
import naoqi
import numpy as np
import time
import sys
import wave
from os.path import join, dirname
import json
from naoqi import ALProxy
from naoqi import ALBroker
from nao_recorder import SoundReceiverModule
from nao_dialogue import Transcriber,Dialogue
import traceback


NAO_IP = "169.254.126.202" 

def main():
    """ Main entry point
    """
    # Configure initial Naoqi argument options
    parser = OptionParser()
    parser.add_option("--pip",
        help="Parent broker port. The IP address or your robot",
        dest="pip")
    parser.add_option("--pport",
        help="Parent broker port. The port NAOqi is listening to",
        dest="pport",
        type="int")
    parser.set_defaults(
        pip=NAO_IP,
        pport=9559)

    (opts, args_) = parser.parse_args()
    pip   = opts.pip
    pport = opts.pport

    # We need this broker to be able to construct NAOqi modules and subscribe to other modules
    # The broker must stay alive until the program exists
    myBroker = ALBroker("myBroker",
       "0.0.0.0",   # listen to anyone
       0,           # find a free port and use it
       pip,         # parent broker IP
       pport)       # parent broker port


    # Warning: SoundReceiver must be a global variable
    global SoundReceiver
    SoundReceiver = SoundReceiverModule("SoundReceiver", pip)
    
    # configure Naoqi to convert text to speech via Nao TTS
    tts = ALProxy("ALTextToSpeech", "169.254.126.202", 9559)

    # Nao wants to know what you did today
    nao_response = "Hello, what did you do today?"
    tts.say(nao_response)
    print("Please say something into NAO's microphone\n")
    
    # subscribe to Naoqi and begin recording speech
    SoundReceiver.start_recording() 

    try:
        # waiting while recording in progress
        while True:
            time.sleep(1)
            
            # initialize dialogue settings
            convo_turn_count = 0
            start_dialogue = False  
            detect_intent = True
            detect_entity = True
            print "keep intent",detect_intent
            print "detect_entity",detect_entity
            keep_emotion = False
            tone_hist = []
            misunderstood = False  
            
            # instantiate conversation state intent and entity.
            # every new loop indicates a new conversation turn with potentially
            # new state information or the state is maintained via flags. 
            my_intent = Dialogue()
            my_entity = Dialogue()            
            
            # start transcribing speech to text
            while not start_dialogue: 
                if SoundReceiver.recording == False: 
                    print "stopped recording, ready to transcribe"
                    print "dialogue boolean",start_dialogue
                    print "convo turn loop count",convo_turn_count
        
                    for utterance in range(1,10):
                        print "utterance number: ",utterance
                
                        try:
                            
                            my_speech = Transcriber('myspeech.wav')
                            user_speech_text = my_speech.transcribe_audio()

                            if user_speech_text:
                                start_dialogue = True

                        except:
                            traceback.print_exc()
                            print "error in speech detection"
                            nao_response = "Hmm. I couldn't understand you. Try telling me what's going on again."
                            #tts.say(nao_response) 
                            continue
                        
                        print "user speech text",user_speech_text

                        print "start intent and entity detection"
                        intent_state = my_intent.get_intent_response(user_speech_text)
                        entity_state = my_entity.get_entity_response(user_speech_text,intent_state)
                 
                        print "detected intent",intent_state
                        print "detected entity",entity_state
                            
                        # start dialogue with Nao
                        while start_dialogue:
                            try: 
                                # dialogue flow based on first detected intent maintained 
                                # throughout conversation turn or not maintained
                                if detect_intent:
                                    print "looking for intents"
                                    res_int = my_intent.state_response(my_intent.int_res_list,intent_state)
                                    print "first detected intent: ",intent_state
                                    try:
                                        tts.say(next(res_int))
                                        detect_intent = False
                                    except StopIteration: 
                                        pass


                                elif not detect_intent:
                                    print "moving on to detect entities for same intent"
                                    pass
                            except:
                                traceback.print_exc()
                                print "can't find intent, try again"
                                nao_response = "Hmm. I couldn't understand your intent.Try telling me it again."
                                #tts.say(nao_response) 
                                continue

                            try: 
                                if detect_entity:
                                    print "looking for entities"
                                    res_ent = my_entity.state_response(my_entity.ent_res_list,entity_state)
                                    try:
                                        print(next(res_ent))
                                        detect_entity = False
                                        print "detect entity",detect_entity
                                    except StopIteration: 
                                        pass
                                          
                                elif not detect_entity:
                                            
                                    print "continue with same entity response generation"
                                    print "detected entity",entity_state
                                    try:
                                        print(next(res_ent))
                                    except StopIteration: 
                                        pass
                            
                            except:
                                traceback.print_exc()
                                print "can't find entity, go on"
                                pass
                    
                            start_dialogue = False
                            print "ending current convo turn"
                            print "start_dialogue",start_dialogue

                        print "going to new conversation turn round"
                        convo_turn_count += 1
                        SoundReceiver.resume_recording()  
    
    except KeyboardInterrupt:
        # closing
        myBroker.shutdown()
        print("disconnected")
        sys.exit(0)
  
if __name__ == "__main__":
    main()