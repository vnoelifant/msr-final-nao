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
            keep_intent = True
            #print "keep intent",keep_intent
            keep_entity = True
            #print "keep_entity",keep_entity
            tone_hist = []
            misunderstood = False
            intent_list = []
            entity_list = []
            
            # instantiate conversation state intent,entity,and emotion.
            # every new loop indicates a new conversation turn with potentially
            # new state information or the state is maintained via flags. 
            my_intent = Dialogue()
            my_entity = Dialogue() 
            my_emo = Dialogue()         
            
            # start recording for speech
            while not start_dialogue: 
                
                # flag for detected speech
                if SoundReceiver.recording == False: 
                    print "stopped recording, ready to transcribe"
                    print "dialogue boolean",start_dialogue
                    print "convo turn loop count",convo_turn_count
                    
                    # start transcribing speech to text
                    try:
                            
                        my_speech = Transcriber('myspeech.wav')
                        user_speech_text = my_speech.transcribe_audio()

                        if user_speech_text:
                            start_dialogue = True
                        print "user speech text",user_speech_text
                        
                        # begin detecting intent
                        try:    
                            if keep_intent:
                                print "keep intent",keep_intent
                                print "intent list", intent_list,len(intent_list)
                                if len(intent_list) > 0:
                                    pass
                                else:
                                    print "getting intent response"
                                    intent_state = my_intent.get_intent_response(input_text) 
                                    if intent_state != None:
                                        intent_list.append(intent_state)
                                     # initialize intent response generator object
                                    res_int = my_intent.state_response(my_intent.int_res_list,intent_list)
                                    print "first detected intent: ",intent_list[0]
                                    try:
                                        print(next(res_int))
                                        #keep_intent = False
                                    except StopIteration: 
                                        pass
                                    start_dialogue = False
                                    continue

                            # detect entity  and tone based on intent
                            try:
                                print "look for entity"
                                print "intent list",intent_list,len(intent_list)
                                if len(entity_list) > 0:
                                    pass
                                else:
                                    entity_state = my_entity.get_entity_response(input_text,intent_list[0])
                                    if entity_state != None:
                                        entity_list.append(entity_state)
                                
                                # initialize entity response generator object
                                if len(entity_list) == 1 and entity_state != None:
                                    print "initializing entity response object"
                                    res_ent = my_entity.state_response(my_entity.ent_res_list,entity_list)

                                print "look for tone"
                                top_emotion,top_emo_score = my_emo.get_top_emo(input_text)
                                if top_emo_score != None:
                                            tone_hist.append({
                                                    'tone_name': top_emotion,
                                                    'score': top_emo_score
                                         })

                                print "intent list",intent_list, len(intent_list)
                                print "entity list",entity_list,len(entity_list)
                                print "tone history dict",tone_hist,len(tone_hist)

                                 # initialize tone response generator object
                                if len(tone_hist) == 1:
                                    print "initializing tone response object"
                                    res_emo = my_emo.state_response(my_emo.emo_ent_list,entity_list,top_emotion,top_emo_score,tone_hist)

                                # start dialogue with Nao
                                while start_dialogue:
                                    # dialogue flow including entities and tone based on first detected intent 
                                    # maintained throughout conversation turn or not maintained  
                                    if keep_entity:
                                        if entity_list and entity_state != None and not tone_hist:
                                            print "detected unemotional entity"
                                        # print "maintained entity",entity_list[0]
                                            print "maintained entity",entity_state
                                            try:
                                                print((next(res_ent)))
                                            except StopIteration: 
                                                pass
             
                                        if tone_hist and top_emo_score > 0.60:
                                            print "detected high emotion"
                                            try:                          
                                                print(next(res_emo))
                                                if entity_list[0] == "meeting":
                                                    keep_entity = False
                                            except StopIteration: 
                                                pass  
                                        
                                        if entity_state != None:
                                            entity_list.append(entity_state)
                                        print "entity list",entity_list,len(entity_list)
                                     
                                    if not keep_entity:
                                        print "clearing entity list"
                                        entity_list = []
                                        print "clearing tone list"
                                        tone_hist = []
                                        print "tone list",entity_list,len(entity_list)
                                        print "detect new entity"
                                        print "entity list",entity_list,len(entity_list)

                                    # start detecting for new intent, clear prior intent, entity and tone lists
                                    if "coworker" in entity_list and top_emotion == "joy":
                                        keep_intent = False
                                        print "clearing intent list"
                                        intent_list = []
                                        print "clearing entity list"
                                        entity_list = []
                                        print "clearing tone list"
                                        tone_hist = []
                                        print "tone list",entity_list,len(entity_list)
                                        print "detect new entity"
                                        print "entity list",entity_list,len(entity_list)

                                        print "ending current convo turn"
                                        start_dialogue = False
                                        keep_entity = True
                                        keep_intent = True

                            except:
                                traceback.print_exc()
                                print "bad initial entity detection"
                                tts.say("I wasn't sure of your entity, what was that again?")
                                pass

                                    
                        except:
                            traceback.print_exc()
                            print "bad initial intent detection"
                            tts.say("I wasn't sure of your intent, what was that again?")
                            pass
                        
                    except:
                        traceback.print_exc()
                        print "error in speech detection"
                        nao_response = "Oh Watson, a little rusty today in your detection eh? Sorry, user, can you repeat that?"
                        tts.say(nao_response) 
                        pass

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