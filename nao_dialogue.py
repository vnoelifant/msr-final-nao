###########################################################
# Main program to converse with Nao
# Syntax
#    python scriptname --pip <ip> --pport <port>
# 
#    --pip <ip>: specify the ip of your robot (without specification it will use NAO_IP variable defined
# in main program)

###########################################################

import os
#from pydub import AudioSegment
#from pydub.playback import play
import json
from os.path import join, dirname
from ibm_watson import SpeechToTextV1, AssistantV1,NaturalLanguageUnderstandingV1,ToneAnalyzerV3
from ibm_watson.natural_language_understanding_v1 \
    import Features, EntitiesOptions, KeywordsOptions
from optparse import OptionParser
import naoqi
import numpy as np
import time
import sys
import os
import wave
from os.path import join, dirname
import json
from naoqi import ALProxy
from naoqi import ALBroker
from nao_recorder import SoundReceiverModule
import traceback


NAO_IP = "169.254.126.202" 

TOP_EMOTION_SCORE_THRESHOLD = 0.5

# initialize Watson Assistant service
assistant = AssistantV1(
    version='2019-02-28',
    iam_apikey='VbfeqWup87p3MP1jPbwoLXhFv7O-1bmSXiN2HZQFrUaw',
    url='https://gateway.watsonplatform.net/assistant/api'
)

# initialize Watson Tone Analyzer
tone_analyzer = ToneAnalyzerV3(
    version='2017-09-21',
    iam_apikey='lcyNkGVUvRAKH98-K-pQwlUT0oG24TyY9OYUBXXIvaTk',
    url='https://gateway.watsonplatform.net/tone-analyzer/api'
)

# to retrieve intents, user examples, entities from Watson Assistant
workspace_id = 'f7bf5689-9072-480a-af6a-6bce1db1c392'

# container for intent history
intent_state = ""

# container for entity history
entity_state = ""

# if set to true, stores initial intent for each user utterance to maintain same intent
# if set to false,initial intent is not stored and intent detection is random
keep_intent = True

# if set to true, stores initial entity for each user utterance to maintain same entity
# if set to false,initial entity is not stored and entity detection is random
keep_entity = True

# list of possible tones
emotions = ['sadness','joy','anger','confident','tentative','analytical','fear']

# list of possible tone responses per emotional state based on entity
# TODO: Update string responses 
emo_list = [{'meeting':["Oh no, I am sorry, what happened at the meeting?","Oh, You sound sad again meeting"],
    'coworker':["Oh, what bothered you about your coworker?","Oh, You sound sad again coworker"]},
    {'meeting':["Oh, You sound happy meeting","Oh, You sound happy again meeting"],
    'coworker':["Good yo hear you sound happy. I'm always here for you.","Oh, You sound happy again coworker"]},
    {'meeting':["Oh you sound a bit angry,I'm here to help you. What happened at the meeting?","Oh, You sound angry again meeting"],
    'coworker':["Oh, Oh, what bothered you about your coworker?","Oh, You sound angry again coworker"]},
    {'meeting':["Oh, You sound confident meeting","Oh, You sound confident again meeting"],
    'coworker':["Oh, what bothered you about your coworker?","Oh, does he at least try to come up with a middle ground?"]},
    {'meeting':["Oh, what bothered you about your coworker?","Oh, You sound tentative again meeting"],
    'coworker':["Ah don't be tentative, I can help! What bothered you about your coworker?","Oh, You sound tentative coworker"]},
    {'meeting':["Oh, does he at least try to come up with a middle ground?","Oh, You sound analytical again meeting"],
    'coworker':["Oh, what bothered you about your coworker?","Oh, You sound analytical again coworker"]},
    {'meeting':["Oh no, I am sorry, what happened at the meeting?","Oh, You sound scared again meeting"],
    'coworker':["Oh don't be scared, what bothered you about your coworker?","Oh, You sound scared coworker"]}]

# list of possible entity responses for unemotional user speech text
ent_res_list = [{'meeting':["Oh, how was the meeting?"],
    'coworker':["Oh, what bothered you about your coworker?"]}]

# list of possible intent responses for unemotional user speech text
int_res_list = [{'work':["What did you do at work?"],
    'reading':["What book did you read?"],
    'friends':["Which friend did you visit?"]}]

# convert text to speech via Nao TTS
def get_nao_response(nao_text):
    tts = ALProxy("ALTextToSpeech", "169.254.126.202", 9559)
    tts.say(nao_text)

# convert speech to text via Watson STT
def transcribe_audio(path_to_audio_file):
    # initialize speech to text service
    speech_to_text = SpeechToTextV1(
        iam_apikey='4aXD2UR_3lDdbH6XwF1u2g0OP8-jAuAU2uVmafislERZ',
        url='https://stream.watsonplatform.net/speech-to-text/api')

    with open((path_to_audio_file), 'rb') as audio_file:
        return speech_to_text.recognize(
                audio=audio_file,
                content_type='audio/wav',
                word_alternatives_threshold=0.5,
                keywords=['hey there', 'hi','watson','friend','meet'],
                keywords_threshold=0.5
            ).get_result()

# get the top emotion
def get_top_emo(user_speech_text):
    
    # initialize emotion data
    max_score = 0.0
    top_emotion = None
    top_emo_score = None

    tone_analysis = tone_analyzer.tone(tone_input=user_speech_text['input'], content_type='application/json').get_result()
    #print "tone response",json.dumps(tone_analysis, indent=2)

    # create dictionary of tones
    tone_dict = tone_analysis['document_tone']['tones']
    
    # find the emotion with the highest tone score
    for tone in tone_dict:
        if tone['score'] > max_score:
            max_score = tone['score']
            top_emotion = tone['tone_name'].lower()
            top_emo_score = tone['score']

        # set a neutral emotion if under tone score threshold
        if max_score <= TOP_EMOTION_SCORE_THRESHOLD:
            top_emotion = 'neutral'
            top_emo_score = None
        #print "top emotion, top score: ", top_emotion, top_emo_score
        
        # update tone_response emotion tone
        tone_analysis['document_tone']['tones'][0]['tone_name'] = top_emotion
        tone_analysis['document_tone']['tones'][0]['score'] = top_emo_score
        #print "updated tone analysis", tone_analysis

        # # append tone and tone score to tone history list
        # tone_hist.append({
        #             'tone_name': top_emotion,
        #             'score': top_emo_score
        #  })
 
    #return top_emotion, tone_hist
    return top_emotion, top_emo_score

# list of responses from nao for intents, entities, and emotions
def int_response(intent_state, int_res_list):
    print "At the intent dialogue branch"
    for response_list in int_res_list:
        for response in response_list[intent_state]:
            yield response

def ent_response(entity_state,ent_res_list):
    print "At the entity dialogue branch"
    for response_list in ent_res_list:
        for response in response_list[entity_state]:
            yield response

def emo_response(top_emotion,top_emo_score,entity_state,emotions,emo_res_list):
    print "At the emo dialogue branch"
    if top_emo_score >= 0.75:
        for emo,response_list in zip(emotions,emo_res_list):
            if emo == top_emotion:
                for response in response_list[entity_state]:
                    yield response

def reading_intent():
    yield "Oh, what book did you read?"
    yield "Cool, what was it about?"

def friends_intent():
    yield "Oh, which friend did you visit?"
    yield "Oh,what did you all do?"

def get_intent_response(user_speech_text):

    intent_response = assistant.message(workspace_id=workspace_id,
                                     input=user_speech_text['input'],
                                    ).get_result()
    
    if intent_response['intents'][0]['confidence'] > 0.5:
        intent_state = intent_response['intents'][0]['intent']
        print "response with detected intent"
        print(json.dumps(intent_response, indent=2))
        return intent_state,intent_response

    return None,None

def get_entity_response(user_speech_text,intent_state = ""):
    print "intent state for entity",intent_state
    entity_response = assistant.message(workspace_id=workspace_id,
                                     input=user_speech_text['input'],
                                    ).get_result()
    if intent_state:
        print "found intent for entity"
        entity_response['intents'][0]['intent'] = intent_state
        entity_response['intents'][0]['confidence'] = None
    
        print "response with detected entity"
        print(json.dumps(entity_response, indent=2))
        entity_state = entity_response['entities'][0]['value']
        return entity_state,entity_response
  
    return None,None
 


def main():
    """ Main entry point

    """
    # Configure initial Naoqi and Watson settings
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

    # Nao wants to know what you did today
    nao_response = "Hello, what did you do today?"
    get_nao_response(nao_response)
    print("Please say something into NAO's microphone\n")
    loop_count = 0
    print "recorder loop count: ",loop_count
    # subscribe to Naoqi and begin recording speech
    SoundReceiver.start_recording() 

    try:
        # waiting while recording in progress
        
        while True:
            time.sleep(1)
            
            # initialize generator objects for Nao's responses to utterances
            res_work = work_intent()
            res_meeting = meeting_entity()
            res_reading = reading_intent()
            res_friends = friends_intent()
            res_coworker = coworker_entity()
            intent_state = ""
            entity_state = ""
            top_emotion = ""
            top_emo_score = ""
            keep_entity = True
            keep_intent = True
            
            while True:
                if SoundReceiver.recording == False:   
                    print "SoundReceiver.recording detected as False, transcribe"
                    print "stopped recording, ready to transcribe"
                    print "recorder loop count: ",loop_count
                    print "len intent", intent_state
                    print "len entity", entity_state
                    print "keep intent", keep_intent
                    print "keep entity", keep_entity
                    
                    try:
                        speech_recognition_results = transcribe_audio('speak32.wav')
                        print(json.dumps(speech_recognition_results, indent=2))
                        speech_text = speech_recognition_results['results'][0]['alternatives'][0]['transcript'] 
                        print("User Speech Text: " + speech_text + "\n")

                        user_speech_text = {
                            'workspace_id': workspace_id,
                            'input': {
                                'text': speech_text
                            }
                        } 

                        # send user_speech_text to Watson Tone Analyzer to be analyzed for tone
                        # detected_emotion, tone_hist = analyze_tone(user_speech_text)
                        top_emotion,top_emo_score = get_top_emo(user_speech_text)
                        print "emotion",top_emotion,top_emo_score
                    
                        # send user_speech_text to Watson Assistant to be analyzed for intents and entities 
                        # dialogue flow is based on intents,entities (maintained or not maintained), and tone
                        try:
                            # dialogue flow based on first detected intent maintained 
                            # throughout conversation turn or not maintained
                            if keep_intent:
                                if intent_state:
                                    pass
                                else:
                                    print "starting intent detection"
                                    intent_state,intent_response = get_intent_response(user_speech_text) 
                                    res_intent = int_response(intent_state,int_res_list)
                                    try:
                                        print(next(res_intent))
                                    except StopIteration: 
                                        pass

                                print "first detected intent: ",intent_state
                                
                                try:
                                    if keep_entity:
                                        if entity_state:
                                            pass
                                        else:
                                            print "start entity detection"
                                            entity_state,entity_response = get_entity_response(user_speech_text,intent_state)
                                            print "detected entity",entity_state
                                            res_ent = ent_response(entity_state,ent_res_list)
                                            try:
                                                print(next(res_ent))
                                            except StopIteration: 
                                                pass
                                        if entity_state and top_emotion == None and top_emo_score == None:
                                            try:
                                                print(next(res_ent))
                                            except StopIteration: 
                                                pass
                                        print "detected entity",entity_state
                                        
                                        if top_emotion and top_emo_score >= 0.75:
                                            emo = emo_response(top_emotion,entity_state,emotions,emo_list)
                                            try:
                                                print next(emo)
                                                if entity_state == "meeting":
                                                    keep_entity = False
                                            except StopIteration: 
                                                pass

                                        elif top_emo_score >= 0.5 and top_emo_score < 0.75:
                                            #emo_check = res_emo_check(entity_state)
                                            if "yes" in user_speech_text:
                                                try:
                                                    print(next(emo))
                                                except StopIteration: 
                                                    pass
                                            else:
                                                try:
                                                    print(next(res_emo_check))
                                                except StopIteration: 
                                                    pass
                                        print "entity bool",keep_entity
                                
                                    elif not keep_entity:
                                        entity_state,entity_response = get_entity_response(user_speech_text,intent_state)
                                        print "new entity",entity_state
                                        keep_entity = True
                                        continue    
                                except:
                                    traceback.print_exc()
                                    print "can't find entity, go on"
                                    pass
                        
                                # # TODO: Add reading entities and tone analysis
                                # elif intent_state  == "reading":
                                #     try:
                                #         print "detected reading convo"
                                #         get_nao_response(next(res_reading))
                                #     except StopIteration:
                                #         pass
                                
                                # # TODO: Add friends entities and tone analysis
                                # elif intent_state == "friends":
                                #     try:
                                #         print "detected friends convo"
                                #         get_nao_response(next(res_friends))
                                #     except StopIteration:
                                #         pass

                            elif not keep_intent:
                                # TODO: add more conditional code here to redirect conversation not based on 
                                # maintained initial intent
                                print "Just getting a random response, not in intent flow"
                                get_nao_response("you do not want to maintain state") 
                                intent_state,intent_response = get_intent_response(user_speech_text)
                                print "intent response",intent_response
                                # entity_state,entity_response = get_entity_response(user_speech_text) 
                                # top_emotion,top_emo_score = get_top_emo(user_speech_text)
                                # print "emotion",top_emotion,top_emo_score
                                pass

                        except:
                            traceback.print_exc()
                            print "can't find intent, continue"
                            pass

                    except:
                        print "error in speech detection"
                        nao_response = "Hmm. I couldn't understand you. Try telling me what's going on again."
                        get_nao_response(nao_response) 
                        traceback.print_exc()
                        print "try speaking again"
                        pass
                   
    except KeyboardInterrupt:
        # closing
        myBroker.shutdown()
        print("disconnected")
        sys.exit(0)
  
    print "resuming recording"
    loop_count += 1
    SoundReceiver.resume_recording()  

if __name__ == "__main__":
    main()



