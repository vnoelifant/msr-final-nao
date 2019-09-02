
import os
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
import wave
import json
import traceback
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
# from nao_recorder import SoundReceiverModule
# from nao_dialogue import Transcriber,Dialogue
import traceback


# NAO_IP = "10.104.239.48" 

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


# list of possible intent responses for unemotional user speech text
int_res_list = [{'work':["What did you do at work?"],
    'reading':["What book did you read?"],
    'friends':["Which friend did you visit?"]}]


# list of possible entity responses for unemotional user speech text
ent_res_list = [{'meeting':["Oh, how was the meeting?","Oh, how was the meeting again?","Oh, how was the meeting yet again?"],
    'coworker':["Oh, what bothered you about your coworker?",
     "Does he at least try to come up with a middle ground?",
     "Oh I am sorry to hear. Maybe if you speak to someone higher up they can help sort things out for you."],
     'Quicksand':["Oh, what was Quicksand about?","Very interesting, I will check it out!"],
     'concert':["Oh, what concert did you see?"],
     'Penny':["Oh, what did you and Penny do?"],
     'concert':["That sounds like a lot of fun!"]}]

# list of possible tone responses per emotional state based on entity
emotions = ['sadness','joy','anger','fear']

# list of possible tone responses per emotional state based on entity
# TODO: Update string responses 
emo_ent_list = [{'meeting':["Oh no, I am sorry to hear that. What happened at the meeting?","Oh, You sound sad again about your meeting."],
    'coworker':["Oh, I am sorry to hear that. What bothered you about your coworker?","Oh, You sound sad again about your coworker."]},
    {'meeting':["Great to hear you sound happy about the meeting!","Great to hear you sound happy again about the meeting!"],
    'coworker':["Anytime! Great to hear you sound happy. I'm always here for you.","Oh, You sound happy again coworker"]},
    {'meeting':["Oh no, sorry you are frustrated. Let me help. What happened at the meeting?","Oh, You sound angry again meeting"],
    'coworker':["Oh no, sorry you are frustrated. Let me help. What bothered you about your coworker?","Oh, You sound angry again about coworker"]},
    {'meeting':["Oh no, I am sorry you sound scared. I am here to help. What happened at the meeting?","Oh, You sound scared again meeting"],
    'coworker':["Oh don't be scared, what bothered you about your coworker?","Oh, You sound scared again about coworker"]}]

#TODO: create resonses for which Nao misunderstands the user's tone
emo_check_list = []

tone_hist = []

class Transcriber:  
    def __init__(self,path_to_audio_file):
        self.path_to_audio_file = path_to_audio_file 

    # convert speech to text via Watson STT
    def transcribe_audio(self):
        #initialize speech to text service
            speech_to_text = SpeechToTextV1(
                iam_apikey='9MXnNlJ3iDrKTsvBYVF5IR3CLVbCHkkL1fhGaRySFsEe',
                url='https://stream.watsonplatform.net/speech-to-text/api')

            with open((self.path_to_audio_file), 'rb') as audio_file:
                speech_result = speech_to_text.recognize(
                        audio=audio_file,
                        content_type='audio/wav',
                        word_alternatives_threshold=0.9,
                        keywords=['hey', 'hi','watson','friend','meet'],
                        keywords_threshold=0.5
                    ).get_result()

                speech_text = speech_result['results'][0]['alternatives'][0]['transcript']
                print("User Speech Text: " + speech_text + "\n")
                   
                user_speech_text = {
                    'workspace_id': workspace_id,
                    'input': {
                        'text': speech_text
                    }
                }
            
            return user_speech_text

class Dialogue:

    def __init__(self):

        self.emo_ent_list = emo_ent_list
        self.ent_res_list = ent_res_list
        self.int_res_list = int_res_list
        self.tone_hist = tone_hist

    def get_intent_response(self,user_speech_text):

        intent_response = assistant.message(workspace_id=workspace_id,
                                         input=user_speech_text['input'],
                                        ).get_result()
        
        if intent_response['intents'][0]['confidence'] > 0.7:
            intent_state = intent_response['intents'][0]['intent']
            return intent_state
        
        return None

    def state_response(self,res_list,state,top_emotion="",top_emo_score="",tone_hist=""):
        try:
            if res_list == ent_res_list:
                print "generating entity response"
                while len(state) > 0:
                    print "entity state",state
                    for response_dict in res_list:
                        for response in response_dict[state[0]]:
                            yield response
            
            if res_list == int_res_list and state[0] != None:
                if len(state) == 1:
                    print "generating intent response"
                    print "intent state",state
                    for response_dict in res_list:
                        for response in response_dict[state[0]]:
                            yield response

            if top_emotion and top_emo_score and tone_hist:
                print "generating emotional response"
                print "emotional state",top_emotion,top_emo_score
                while len(tone_hist) > 0:
                    for emo,response_dict in zip(emotions,res_list):
                        if emo == top_emotion:
                            for response in response_dict[state[0]]:
                                yield response
    
        except KeyError:
            return
    
    def emo_check(self,top_emotion):
        yield "I think you may be feeling" + " " + top_emotion + " " + "is that right?"
        yield "Ok I was just checking, you can tell me more if you'd like."

   # get the top emotion
    def get_top_emo(self,user_speech_text):
        # initialize emotion data
        max_score = 0.0
        top_emotion = None
        top_emo_score = None

        tone_analysis = tone_analyzer.tone(tone_input=user_speech_text['input'], content_type='application/json').get_result()
        #print "tone response",json.dumps(tone_analysis, indent=2)
        #print tone_analysis
        # create list of tones
        tone_list = tone_analysis['document_tone']['tones']
       
        # find the emotion with the highest tone score
        for tone_dict in tone_list:
            #print "tone dict",tone_dict
            if tone_dict['tone_id'] == "sadness" or tone_dict['tone_id'] == "joy" or \
            tone_dict['tone_id'] == "anger" or tone_dict['tone_id'] == "fear":
                #print "tone id",tone_dict['tone_id'] 
                #print "max score", max_score,top_emotion,top_emo_score
                if tone_dict['score'] > max_score:
                    max_score = tone_dict['score']
                    #top_emotion = tone['tone_name'].lower()
                    top_emotion = tone_dict['tone_id']
                    top_emo_score = tone_dict['score']
                    #print "top emo",top_emotion, top_emo_score

                # set a neutral emotion if under tone score threshold
                if max_score <= TOP_EMOTION_SCORE_THRESHOLD:
                    print "tone score under threshold"
                    top_emotion = 'neutral'
                    top_emo_score = None
 
        print "chosen top emo",top_emotion, top_emo_score
        return top_emotion, top_emo_score

    
    def get_entity_response(self,user_speech_text,intent_state):
        print "intent state for entity",intent_state
        entity_response = assistant.message(workspace_id=workspace_id,
                                         input=user_speech_text['input'],
                                        ).get_result()
        if intent_state:
            print "found intent for entity"
            entity_response['intents'][0]['intent'] = intent_state
            entity_response['intents'][0]['confidence'] = None
        
           
        if entity_response['entities']:
            if entity_response['entities'][0]['confidence'] > 0.5:
                entity_state = entity_response['entities'][0]['value']
                entity = entity_response['entities'][0]['entity']
                print "response with detected entity"
                print(json.dumps(entity_response, indent=2))
                return entity_state, entity
        
        return None
 

