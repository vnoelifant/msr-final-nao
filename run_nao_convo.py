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
from nao_dialogue import Dialogue
import traceback


NAO_IP = "169.254.126.202" 

def build_intent_res(intent_list):

    # list of intent responses
    return [{'work':["What did you do at your work?"],'reading':["What book did you read?"],'friends':["Which friend did you visit?"]}]

def build_entity_res(entity_list):
    
    # list of entity responses
    return [{'meeting':["Oh, how was the meeting?","Oh no, What happened at the meeting?","Oh no, What bothered you about your coworker?",
             "Ah. Does your coworker at least try to come up with a middle ground?","Oh I am sorry to hear. Maybe if you speak to someone even higher up they can help sort things out for you."],
             'mentor':["Oh, what bothered you about your mentor?","Ah. Does your mentor at least try to come up with a middle ground?",
             "Oh I am sorry to hear. Maybe if you speak to someone even higher up they can help sort things out for you."],
             'case':["Wow! Congratulations! What does this mean?","Wow! Congratulations! What does this mean?"],
             'raise':["That's so wonderful, congratulations! I knew you were capable of such an amazing thing!"],
             'promotion':["That's so wonderful, congratulations! I knew you were capable of such an amazing thing!"],
             'Minor':["Oh, wow! What were your thoughts about The Minor?","I am so glad to hear you enjoyed The Minor!","Anytime, Goodbye now!!"],
             'Twilight':["Oh, I've heard of Twilight, but forgot what it was about!","Haha, really, why?!","Oh dear! Okay, I will be sure not to pick up Twilight. To lighten things up for you, let me recommend reading The Minor, by Sotseki"],
             'concert':["Oh who did you see at the concert?"],
             'Beach House':["Cool! I love Beach House. How did they perform?"],
             'John':["Okay, what did you do with John?", "Oh okay. Is everything alright with you though?",
             "I'm sorry to hear that. Well let me know if you ever want to talk about John.You know I am here for you!","Anytime!"],
             'Penny':["Okay, what did you do with Penny?"]}]

def build_emo_res(entity_list,top_emotion):
    
    # sadness, joy, anger, fear response lists for all entities
    return [{'meeting':["Oh no, you sound sad. What happened at the meeting?",
            "Oh sorry I missed that, you sound sad. What happened at the  meeting?"],
            'mentor':["Oh no, you sound sad,what bothered you about your mentor?","Oh no, you sound sad,what bothered you about your mentor?"],
            'Twilight':["Oh dear! Okay, I will be sure not to pick up Twilight. To lighten things up for you, let me recommend reading The Minor, by Sotseki"],
            'John':["Oh okay. Is eveyrthing alright with you though?","I'm sorry to hear that. Well let me know if you ever want to talk about John. You know I am here for you!",
            "Anytime! I love you!"]},
                
            {'mentor':["Good to hear you are experiencing joy. I'm always here for you.","Good to hear you sound happy again"],
            'case':["Anytime!"],
            'raise':["Anytime! You deserve it!"],
            'promotion':["That's so wonderful, congratulations! I knew you were capable of such an amazing thing!"],
            'Minor':["I am so glad to hear you enjoyed the Minor!","Anytime! Goodbye now dear Ronnie!"],
            'Twilight':["Anytime, Goodbye Now dear Ronnie!"],
            'Beach House':["Wow that's awesome! Any band that makes makes Penny feel wonderful is worth watching in my book!"],
            'John':["Anytime, I love you!"]},
            
            {'meeting':["Oh you sound a bit angry,I'm here to help you. What happened at the meeting?","Oh you sound a bit angry,I'm here to help you. What happened at the meeting?"],
            'mentor':["Oh, you are angry, let me help. What bothered you about your mentor?","Oh, don't be angry, what bothered you about your mentor?"],
            'Twilight':["Oh dear! Okay, I will be sure not to pick up Twilight.To lighten things up for you, let me recommend reading The Minor, by Sotseki"],
            'John':["Oh okay. Is eveyrthing alright with you though?","I'm sorry to hear that. Well let me know if you ever want to talk about John. You know I am here for you!"]},
            
            {'meeting':["Oh no, I am sorry you sound scared, what happened at the meeting?","Oh, I am sorry you sound scared. What happened at the meeting?"],
            'mentor':["Oh don't be scared, what bothered you about your mentor?","Oh don't be scared, what bothered you about your mentor?"],
            'Twilight':["Haha, really, why?!","Oh dear! Okay, I will be sure not to pick up Twilight.To lighten things up for you, let me recommend reading The Minor, by Sotseki"],
            'John':["Oh okay. Is eveyrthing alright with you though?","I'm sorry to hear that. Well let me know if you ever want to talk about John.You know I am here for you!"]}]


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
    tts = ALProxy("ALTextToSpeech", NAO_IP, 9559)


    ledsProxy = ALProxy("ALLeds",NAO_IP, 9559)

    # Nao wants to know what you did today
    ledsProxy.fadeRGB("FaceLeds", "magenta", 1)
    nao_response = "Hello, friend, what did you do today?"
    tts.say(nao_response)
    #print("Please say something into NAO's microphone\n")
    
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
            keep_entity = True
            tone_hist = []
            misunderstood = False
            intent_list = []
            entity_list = []
            
            # instantiate conversation state
            # every new loop indicates a new conversation turn with potentially
            # new state information or the state is maintained via flags. 
            my_convo = Dialogue('speech.wav')       
            
            # start recording for speech
            while not start_dialogue: 
                
                # flag for detected speech
                if SoundReceiver.recording == False: 
                    # start transcribing speech to text
                    try:
                            
                        my_convo = Dialogue('speech.wav')
                        user_speech_text = my_convo.transcribe_audio()
                        if user_speech_text == "goodbye":
                            break

                        if user_speech_text:
                            start_dialogue = True
                        print "user speech text",user_speech_text
                        
                        # begin detecting intent
                        try:    
                            if keep_intent:
                                if len(intent_list) > 0:
                                    pass
                                else:
                                    intent_state = my_convo.get_intent_response(user_speech_text) 
                                    if intent_state != None:
                                        intent_list.append(intent_state)
                                    # build list of possible intent responses
                                    int_res_list = build_intent_res(intent_list)
                                    # initialize intent response generator object
                                    res_int = my_convo.intent_state_response(int_res_list,intent_list)
                                    try:
                                        tts.say(next(res_int))
                                    except StopIteration: 
                                        pass
                                    start_dialogue = False
                                    continue

                            # detect entity  and tone based on intent
                            try:
                                if len(entity_list) > 0:
                                    pass
                                else:
                                    entity_state = my_convo.get_entity_response(user_speech_text)
                                    if entity_state != None:
                                        entity_list.append(entity_state)
                                
                                # initialize entity response generator object
                                if len(entity_list) == 1 and entity_state != None:
                                    # build list of possible intent responses
                                    ent_res_list = build_entity_res(entity_list)
                                    # initialize entity response generator object
                                    res_ent = my_convo.entity_state_response(ent_res_list,entity_list)
                                   
                                top_emotion,top_emo_score = my_convo.get_top_emo(user_speech_text)
                                if top_emo_score != None and top_emo_score >= 0.60:
                                    tone_hist.append({'tone_name': top_emotion,'score': top_emo_score})

                                 # initialize tone response generator object
                                if len(tone_hist) == 1:
                                    # build list of possible tone responses based on entity
                                    emo_ent_list = build_emo_res(entity_list,top_emotion)
                                    # initialize tone response generator object
                                    res_emo = my_convo.emo_state_response(emo_ent_list,entity_list,top_emotion)

                                # start dialogue with Nao
                                while start_dialogue:
                                    # dialogue flow including entities and tone based on first detected intent 
                                    # maintained throughout conversation turn or not maintained  
                                    if keep_entity:
                                        if entity_list and entity_state != None and not tone_hist:
                                            #print "detected unemotional entity"
                                            print "maintained entity",entity_state
                                            print "detected unemotional entity"
                        
                                            try:
                                                tts.say((next(res_ent)))
                                                # conditions to transition to other entities
                                                if entity_list[0] == "Penny":
                                                    keep_entity = False
                                                if entity_list[0] == "concert":
                                                    keep_entity = False
                                            except StopIteration: 
                                                pass
                                        
                                        # condition for tone
                                        if tone_hist:
                                            try:                          
                                                tts.say(next(res_emo))
                                                # transitioning to new work entities
                                                if entity_list[0] == "case":
                                                    keep_entity = False
                                                if entity_list[0] == "meeting":
                                                    # shine face eyes red
                                                    ledsProxy.fadeRGB("FaceLeds", "red", 2)     
                                                    keep_entity = False   
                                                # transitioning to new intent after joyful ending to work intent dialogue
                                                if "mentor" in entity_list and top_emotion == "joy":
                                                    # shine face eyes yellow
                                                    ledsProxy.fadeRGB("FaceLeds", "yellow", 2)
                                                    keep_intent = False
                                                if "Beach House" in entity_list and top_emotion == "joy":
                                                    ledsProxy.fadeRGB("FaceLeds", "magenta", 2)
                                                    keep_intent =False
                                                if "John" in entity_list and top_emotion == "joy":
                                                    ledsProxy.fadeRGB("FaceLeds", "green", 2)
                                                    keep_intent = False
                                                if "raise" or "promotion" in entity_list and top_emotion == "joy":
                                                    ledsProxy.fadeRGB("FaceLeds", "cyan", 5)
                                                    keep_intent = False
                                            except StopIteration: 
                                                pass  
                                        
                                        if entity_state != None:
                                            entity_list.append(entity_state)
                                        #print "entity list",entity_list,len(entity_list)
                                     
                                    if not keep_entity:
                                        entity_list = []
                                        tone_hist = []

                                    # start detecting for new intent, clear prior intent, entity and tone lists
                                    if not keep_intent:
                                        intent_list = []
                                        entity_list = []
                                        tone_hist = []
                                        # Nao wants to know what someone else did today
                                        nao_response = "Hello, new friend, what did you do today?"
                                        tts.say(nao_response)

                                    #print "ending current convo turn"
                                    start_dialogue = False
                                    keep_entity = True
                                    keep_intent = True

                            except:
                                traceback.print_exc()
                                tts.say("I wasn't sure of your entity, what was that again?")
                                pass               
                        except:
                            traceback.print_exc()
                            tts.say("I wasn't sure of your intent, what was that again?")
                            pass
                        
                    except:
                        traceback.print_exc()
                        nao_response = "Oh Watson, a little rusty today in your detection eh? Sorry, user, can you repeat that?"
                        tts.say(nao_response) 
                        pass

                    #print "going to new conversation turn round"
                    convo_turn_count += 1
                    SoundReceiver.resume_recording()  
    
    except KeyboardInterrupt:
        # closing
        myBroker.shutdown()
        print("disconnected")
        sys.exit(0)
  
if __name__ == "__main__":
    main()