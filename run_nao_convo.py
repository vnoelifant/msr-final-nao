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
from nao_dialogue import Transcriber,
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
            keep_intent = True
            keep_entity = True
            keep_emotion = False
            misunderstood = False
            start_dialogue = False
            intent_state = ""
            entity_state = ""
            top_emo_score = ""
            top_emotion = ""
            input_text = ""
            
            # instantiate conversation state including input speech text,
            # current top emotion and emotion score, current intent, and current entity if
            # they exist. Every new loop indicates a new conversation turn with potentially
            # new state information or the state is maintained via flags. 
            convo_state = Dialogue(input_text,top_emotion,top_emo_score,intent_state,entity_state)
            
            # start transcribing speech to text
            while not start_dialogue: 
                if SoundReceiver.recording == False: 
                    print "stopped recording, ready to transcribe"
                    print "dialogue boolean",start_dialogue
                    print "input text", convo_state.input_text
                    print "convo turn loop count: ",convo_turn_count 
                    print "current intent", convo_state.intent_state
                    print "current entity", convo_state.entity_state
                    print "current intent",keep_intent
                    print "keep entity", keep_entity
                    
                    try:
                        
                        my_speech = Transcriber('myspeech.wav')
                        convo_state.input_text = my_speech.transcribe_audio()

                        if convo_state.user_speech_text:
                            start_dialogue = True
                        
                        # start dialogue with Nao
                        while start_dialogue:
                            print "dialogue boolean",start_dialogue
                            # if tone information not to be maintained
                            print "keep emo boolean",keep_emotion
                            if not keep_emotion:
                                print "detect an emotion"
                                # send user_speech_text to Watson Tone Analyzer to be analyzed for tone
                                convo_state.top_emotion,convo_state.top_emo_score = convo_state.get_top_emo()
                                print "new convo state emotion",convo_state.top_emotion,convo_state.top_emo_score
                            # send user_speech_text to Watson Assistant to be analyzed for intents and entities 
                            # dialogue flow is based on intents,entities (maintained or not maintained), and tone
                            try:
                                # dialogue flow based on first detected intent maintained 
                                # throughout conversation turn or not maintained
                                if keep_intent:
                                    if convo_state.intent_state:
                                        pass
                                    else:
                                        print "start intent detection"
                                        convo_state.intent_state = convo_state.get_intent_response()  
                                        res_int = convo_state.state_response(convo_state.intent_state,convo_state.int_res_list)
                                        try:
                                            tts.say(next(res_int))
                                        except StopIteration: 
                                            pass
                               
                                    print "first detected intent: ",convo_state.intent_state
                                    print "detected intent: ",convo_state.intent_state
                            
                                    try: 
                                        if keep_entity:
                                            if convo_state.entity_state:
                                                pass
                                            else:
                                                print "start entity detection"
                                                convo_state.entity_state = convo_state.get_entity_response()
                                                print "detected entity",convo_state.entity_state
                                                res_ent = convo_state.state_response(convo_state.entity_state,convo_state.ent_res_list)
                                                try:
                                                    tts.say(next(res_ent))
                                                except StopIteration: 
                                                    pass
                                            print "detected entity",convo_state.entity_state
                                            print "entity bool",keep_entity
                                        
                                            if convo_state.top_emotion and convo_state.top_emo_score != None: 
                                                if convo_state.top_emo_score >= 0.65:
                                                    res_emo = convo_state.state_response(convo_state.entity_state,convo_state.emo_ent_list)

                                                    try:
                                                        tts.say(next(res_emo))
                                                        if convo_state.entity_state == "meeting":
                                                            keep_entity = False
                                                    except StopIteration: 
                                                        pass
                                                # TODO: Update neutral/lower threshold emotion scores
                                                
                                                # elif convo_state.top_emo_score >= 0.5 and convo_state.top_emo_score < 0.75:
                                                #     keep_emotion = True
                                                #     res_emo_check = convo_state.emo_check()
                                                #     try:
                                                #         tts.say(next(res_emo_check))
                                                #         start_dialogue = False
                                                #         misunderstood = True
                                                #     except StopIteration: 
                                                #         pass

                                                # elif misunderstood:
                                                #     if "yes" in convo_state.input_text:
                                                #         "clarified emotion, continue with emotion response"
                                                #         try:
                                                #             print(next(res_ent))
                                                #         except StopIteration: 
                                                #             pass   
                                                #     else:
                                                #         print "ok, probe user if dialogue will continue"
                                                #     try:
                                                #         tts.say(next(res_emo_check))
                                                #     except StopIteration: 
                                                #         pass

                                            else:
                                                print "no high emotions detected, just respond to entity"
                                                try:
                                                    tts.say(next(res_ent))
                                                except StopIteration: 
                                                    pass
                                     
                                        elif not keep_entity:
                                            convo_state.entity_state = convo_state.get_entity_response()
                                            print "new entity",convo_state.entity_state
                                            keep_entity = True
                                            continue   
                                            
                                    except:
                                        traceback.print_exc()
                                        print "can't find entity, go on"
                                        tts.say("I didn't get your entity. Please try speaking again.")
                                        pass
                            
                                elif not keep_intent:
                                    # TODO: add more conditional code here to redirect conversation not based on 
                                    # maintained initial intent
                                    intent_state,intent_response = get_intent_response(user_speech_text)
                                    print "new intent",intent_state
                                    keep_intent = True
                                    continue

                            except:
                                traceback.print_exc()
                                print "can't find intent, continue"
                                tts.say("I didn't understand your intent. Please try speaking again.")
                                pass

                            start_dialogue = False 

                    except:
                        print "error in speech detection"
                        nao_response = "Hmm. I couldn't understand you. Try telling me what's going on again."
                        tts.say(nao_response) 
                        traceback.print_exc()
                        print "try speaking again"
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