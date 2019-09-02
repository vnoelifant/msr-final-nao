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

def build_intent_res(intent_list):
    return [{'work':["What did you do at" + " " + intent_list[0]],'reading':["What book did you read?"],'friends':["Which friend did you visit?"]}]

def build_entity_res(entity_list):
    return [{'meeting':["Oh, how was the" + " " + entity_list[0],"Oh, how was the" + " " + entity_list[0] + " " + "again?","Oh, how was the meeting yet again?"],
                
                'coworker':["Oh, what bothered you about" + " " + entity_list[0],"Does" + " " + entity_list[0] + " " + "at least try to come up with a middle ground?",
                
                "Oh I am sorry to hear. Maybe if you speak to someone higher up they can help sort things out for you."],
                
                'title':["Oh, what was Kokoro about?","Very interesting, I will check it out!"],
                
                'concert':["Oh, what concert did you see?"],

                'Penny':["Oh, what did you and Penny do?"]}]

def build_emo_res(entity_list):
    return [{'meeting':["Oh no, you sound sad,what happened at the" + " " + entity_list[0],"Oh no, you sound sad,what happened at the" + " " + entity_list[0]],
                'coworker':["Oh no, you sound sad,what bothered you about" + " " + entity_list[0],"Oh no, you sound sad,what bothered you about" + " " + entity_list[0]]},
                {'meeting':["Oh, You sound happy about the" + " " + entity_list[0],"Oh, You sound happy again about the" + " " + entity_list[0]],
                'coworker':["Good to hear you are experiencing joy", "I'm always here for you.","Good to hear you sound happy again"]},
                {'meeting':["Oh you sound a bit angry,I'm here to help you. What happened at the" + " " + entity_list[0],"Oh, You sound angry again about the" + " "  + entity_list[0]],
                'coworker':["Oh, you are angry, let me help. What bothered you about" + " " + entity_list[0],"Oh, You sound angry again about" + " " + entity_list[0]]},
                {'meeting':["Oh no, I am sorry you sound scared, what happened at the" + " " + entity_list[0],"Oh, You sound scared again about the" + " " +  entity_list[0]],
                'coworker':["Oh don't be scared, what bothered you about" + " " + entity_list[0],"Oh, You sound scared again about" + " " + entity_list[0]]}]

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
    nao_response = "Hello, Veronica, what did you do today?"
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
            
            # instantiate conversation state
            # every new loop indicates a new conversation turn with potentially
            # new state information or the state is maintained via flags. 
            my_convo = Dialogue('myspeech.wav')       
            
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
                                    intent_state = my_convo.get_intent_response(user_speech_text) 
                                    if intent_state != None:
                                        intent_list.append(intent_state)
                                    # build list of possible intent responses
                                    int_res_list = build_intent_res(intent_list)
                                    # initialize intent response generator object
                                    res_int = my_convo.intent_state_response(int_res_list,intent_list)
                                    print "first detected intent: ",intent_list[0]
                                    try:
                                        tts.say(next(res_int))
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
                                    entity_state, entity = my_convo.get_entity_response(user_speech_text,intent_list[0])
                                    if entity_state != None:
                                        entity_list.append(entity_state)
                                
                                # initialize entity response generator object
                                if len(entity_list) == 1 and entity_state != None:
                                    # build list of possible intent responses
                                    ent_res_list = build_entity_res(entity_list)
                                    # initialize entity response generator object
                                    res_ent = my_convo.entity_state_response(ent_res_list,entity_list)
                                   
                                print "look for tone"
                                top_emotion,top_emo_score = my_convo.get_top_emo(user_speech_text)
                                if top_emo_score != None and top_emo_score >= 0.70:
                                            tone_hist.append({
                                                    'tone_name': top_emotion,
                                                    'score': top_emo_score
                                         })

                                print "intent list",intent_list, len(intent_list)
                                print "entity list",entity_list,len(entity_list)
                                print "tone history dict",tone_hist,len(tone_hist)

                                 # initialize tone response generator object
                                if len(tone_hist) == 1:
                                    # build list of possible tone responses based on entity
                                    emo_ent_list = build_emo_res(entity_list)
                                    # initialize tone response generator object
                                    print "initializing tone response object"
                                    res_emo = my_convo.emo_state_response(emo_ent_list,entity_list,top_emotion)

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
                                                tts.say((next(res_ent)))
                                                 # new test to transition to other remaining intent
                                                if "Quicksand" in entity_list:
                                                    keep_intent = False
                                            except StopIteration: 
                                                pass
             
                                        if tone_hist:
                                            print "detected high emotion"
                                            try:                          
                                                tts.say(next(res_emo))
                                                # transitioning to new work entity
                                                if entity_list[0] == "meeting":
                                                    keep_entity = False
                                                # transitioning to new intent after joyful ending to work intent dialogue
                                                if "coworker" in entity_list and top_emotion == "joy":
                                                    keep_intent = False
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
                                    if not keep_intent:
                                        print "clearing intent list"
                                        intent_list = []
                                        print "clearing entity list"
                                        entity_list = []
                                        print "clearing tone list"
                                        tone_hist = []
                                        print "tone list",entity_list,len(entity_list)
                                        print "detect new entity"
                                        print "entity list",entity_list,len(entity_list)
                                         # Nao wants to know what someone else did today
                                        nao_response = "Hello, new friend, what did you do today?"
                                        tts.say(nao_response)

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
                        # nao_response = "Oh Watson, a little rusty today in your detection eh? Sorry, user, can you repeat that?"
                        # tts.say(nao_response) 
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