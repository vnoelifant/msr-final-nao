
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

# threshold value that determines tone
TOP_EMOTION_SCORE_THRESHOLD = 0.65

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

emotions = ['sadness','joy','anger','fear']

# Dialogue class
class Dialogue:  
    def __init__(self,path_to_audio_file):
        # get the .wav file path
        self.path_to_audio_file = path_to_audio_file 

    # convert speech to text via Watson STT
    def transcribe_audio(self):
        #initialize speech to text service
        speech_to_text = SpeechToTextV1(
            iam_apikey='zzCg3g-cCs5FIKKuTF0pA87OZi8WFdD2i5yOv762cj62',
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
            user_speech_text = {
                'workspace_id': workspace_id,
                'input': {
                    'text': speech_text
                }
            }
        
        return user_speech_text

    # look for intents via Watson Assistant
    def get_intent_response(self,user_speech_text):

        intent_response = assistant.message(workspace_id=workspace_id,
                                         input=user_speech_text['input'],
                                        ).get_result()
        
        if intent_response['intents'][0]['confidence'] > 0.6:
            intent_state = intent_response['intents'][0]['intent']
            return intent_state
        
        return None

    # look for entities via Watson Assistant
    def get_entity_response(self,user_speech_text,intent_state=""):
        entity_response = assistant.message(workspace_id=workspace_id,
                                         input=user_speech_text['input'],
                                         ).get_result()
        if intent_state:
            #print "found intent for entity"
            entity_response['intents'][0]['intent'] = intent_state
            entity_response['intents'][0]['confidence'] = None
        
           
        if entity_response['entities']:
            if entity_response['entities'][0]['confidence'] > 0.5:
                entity_state = entity_response['entities'][0]['value']
                entity = entity_response['entities'][0]['entity']
                return entity_state
        
        return None


   # get the top emotion via Watson Tone Analyzer
    def get_top_emo(self,user_speech_text):
        # initialize emotion data
        max_score = 0.0
        top_emotion = None
        top_emo_score = None

        tone_analysis = tone_analyzer.tone(tone_input=user_speech_text['input'], content_type='application/json').get_result()
        # create list of tones
        tone_list = tone_analysis['document_tone']['tones']
       
        # find the emotion with the highest tone score
        for tone_dict in tone_list:
            if tone_dict['tone_id'] == "sadness" or tone_dict['tone_id'] == "joy" or \
            tone_dict['tone_id'] == "anger" or tone_dict['tone_id'] == "fear":
                if tone_dict['score'] > max_score:
                    max_score = tone_dict['score']
                    top_emotion = tone_dict['tone_id']
                    top_emo_score = tone_dict['score']
                # set a neutral emotion if under tone score threshold
                if max_score <= TOP_EMOTION_SCORE_THRESHOLD:
                    #print "tone score under threshold"
                    top_emotion = 'neutral'
                    top_emo_score = None

        return top_emotion, top_emo_score

    # function to retrieve responses for intent utterances per conversation turn
    def intent_state_response(self,res_list,intent_list):
        try:
      
            for response_dict in res_list:
                for response in response_dict[intent_list[0]]:
                    yield response
            
        except KeyError:
            return

    # function to retrieve responses for entity utterances per conversation turn
    def entity_state_response(self,res_list,entity_list):
        try:
            for response_dict in res_list:
                for response in response_dict[entity_list[0]]:
                    yield response
    
        except KeyError:
            return
    # function to retrieve responses for tone utterances per conversation turn
    def emo_state_response(self,res_list,entity_list,top_emotion):
        try:

            for emo,response_dict in zip(emotions,res_list):
                if emo == top_emotion:
                    for response in response_dict[entity_list[0]]:
                        yield response
    
        except KeyError:
            return
 

