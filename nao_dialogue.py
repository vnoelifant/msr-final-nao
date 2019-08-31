
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

# list of possible tones
emotions = ['sadness','joy','anger','confident','tentative','analytical','fear']

# list of possible tone responses per emotional state based on entity
# TODO: Update string responses 
emo_ent_list = [{'meeting':["Oh no, you sound sad,what happened at the meeting?","Oh, You sound sad again meeting"],
    'coworker':["Anytime! Glad to hear you sound happy","Oh, You sound happy again coworker"]},
    {'meeting':["Oh, You sound happy meeting","Oh, You sound happy again meeting"],
    'coworker':["Good yo hear you sound happy. I'm always here for you.","Oh, You sound happy again coworker"]},
    {'meeting':["Oh you sound a bit angry,I'm here to help you. What happened at the meeting?","Oh, You sound angry again meeting"],
    'coworker':["Oh, you are angry, let me help. What bothered you about your coworker?","Oh, You sound angry again about coworker"]},
    {'meeting':["Oh, You sound confident meeting","Oh, You sound confident again meeting"],
    'coworker':["Oh, you are confident. what bothered you about your coworker?","Oh,confident again. Does he at least try to come up with a middle ground?"]},
    {'meeting':["Ah don't be tentative, I can help! What bothered you about meeting?","Oh, You sound tentative again meeting"],
    'coworker':["Ah don't be tentative, I can help! What bothered you about your coworker?","Oh I am sorry to hear. Maybe if you speak to someone higher up they can help sort things out for you."]},
    {'meeting':["Oh, analytical huh?","Oh, You sound analytical again meeting"],
    'coworker':["Oh, analytical huh? Does he at least try to come up with a middle ground?","Oh, analytical again huh? does he at least try to come up with a middle ground?"]},
    {'meeting':["Oh no, I am sorry you sound scared, what happened at the meeting?","Oh, You sound scared again meeting"],
    'coworker':["Oh don't be scared, what bothered you about your coworker?","Oh, You sound scared again about coworker"]}]
# list of possible entity responses for unemotional user speech text
ent_res_list = [{'meeting':["Oh, how was the meeting?"],
    'coworker':["Oh, what bothered you about your coworker?",
     "Does he at least try to come up with a middle ground?",
     "Oh I am sorry to hear. Maybe if you speak to someone higher up they can help sort things out for you."]}]

# list of possible intent responses for unemotional user speech text
int_res_list = [{'work':["What did you do at work?"],
    'reading':["What book did you read?"],
    'friends':["Which friend did you visit?"]}]

#emo_check_list = []

class Transcriber:  
    def __init__(self,path_to_audio_file):
        self.path_to_audio_file = path_to_audio_file 

    # convert speech to text via Watson STT
    def transcribe_audio(self):
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
               
            self.user_speech_text = {
                'workspace_id': workspace_id,
                'input': {
                    'text': speech_text
                }
            }
        
        return self.user_speech_text

class Dialogue:

    def __init__(self,user_speech_text,top_emotion,top_emo_score,tone_hist,intent_state,entity_state):

        self.top_emotion = top_emotion
        self.top_emo_score = top_emo_score
        self.intent_state = intent_state
        self.entity_state = entity_state
        self.user_speech_text = user_speech_text
        self.emo_ent_list = emo_ent_list
        self.ent_res_list = ent_res_list
        self.int_res_list = int_res_list
        self.tone_hist = []
       
    def get_intent_response(self):

        intent_response = assistant.message(workspace_id=workspace_id,
                                         input=self.user_speech_text['input'],
                                        ).get_result()
        
        if intent_response['intents'][0]['confidence'] > 0.5:
            self.intent_state = intent_response['intents'][0]['intent']
            print "response with detected intent"
            print(json.dumps(intent_response, indent=2))
            return self.intent_state

        return None

    def state_response(self,state,res_list):
        print "generating response"
        print "emotion", self.top_emotion,self.top_emo_score

        if res_list == self.emo_ent_list:
            print "getting an emo response"
            for emo,response_dict in zip(emotions,res_list):
                if emo == self.top_emotion:
                    for response in response_dict[state]:
                        yield response
        else:
            print "getting an intent or work non-emotions response"
            for response_dict in res_list:
                for response in response_dict[state]:
                    yield response
    
    def emo_check(self):
        yield "I think you may be feeling", self.top_emotion, "is that right?"
        yield "Ok I was just checking, you can tell me more if you'd like."

    # get the top emotion
    def get_top_emo(self):
        # initialize emotion data
        max_score = 0.0
        self.top_emotion = None
        self.top_emo_score = None

        tone_analysis = tone_analyzer.tone(tone_input=self.user_speech_text['input'], content_type='application/json').get_result()
        
        # create list of tones
        tone_list = tone_analysis['document_tone']['tones']
       
        # find the emotion with the highest tone score
        for tone_dict in tone_list:
            print "tone dict",tone_dict
            if tone_dict['tone_id'] == "sadness" or tone_dict['tone_id'] == "joy" or \
            tone_dict['tone_id'] == "anger" or tone_dict['tone_id'] == "fear":
                print "tone id",tone_dict['tone_id'] 
                print "max score", max_score,self.top_emotion,self.top_emo_score
                if tone_dict['score'] > max_score:
                    max_score = tone_dict['score']
                    #self.top_emotion = tone['tone_name'].lower()
                    self.top_emotion = tone_dict['tone_id']
                    self.top_emo_score = tone_dict['score']
                    print "top emo",self.top_emotion, self.top_emo_score

                # set a neutral emotion if under tone score threshold
                if max_score <= TOP_EMOTION_SCORE_THRESHOLD:
                    print "tone score under threshold"
                    self.top_emotion = 'neutral'
                    self.top_emo_score = None
                    print "top emotion, top score: ", self.top_emotion, self.top_emo_score
        if self.top_emo_score != None:
            self.tone_hist.append({
                        'tone_name': self.top_emotion,
                        'score': self.top_emo_score
             })
  
        print "chosen top emo",self.top_emotion, self.top_emo_score
        return self.top_emotion, self.top_emo_score
    
    def get_entity_response(self):
        print "intent state for entity",self.intent_state
        entity_response = assistant.message(workspace_id=workspace_id,
                                         input=self.user_speech_text['input'],
                                        ).get_result()
        if self.intent_state:
            print "found intent for entity"
            entity_response['intents'][0]['intent'] = self.intent_state
            entity_response['intents'][0]['confidence'] = None
        
            print "response with detected entity"
            print(json.dumps(entity_response, indent=2))
            self.entity_state = entity_response['entities'][0]['value']
            return self.entity_state

        return None
 

