import json
from ibm_watson import SpeechToTextV1, AssistantV1,NaturalLanguageUnderstandingV1, \
ToneAnalyzerV3,TextToSpeechV1
from ibm_watson.natural_language_understanding_v1 \
import Features, EntitiesOptions, KeywordsOptions
from speech_sentiment_python.recorder import Recorder
import traceback
import sys
from pydub import AudioSegment
from pydub.playback import play
import cozmo

TOP_TONE_SCORE_THRESHOLD = 0.65

tone_analyzer = ToneAnalyzerV3(
    version='2017-09-21',
    iam_apikey='lcyNkGVUvRAKH98-K-pQwlUT0oG24TyY9OYUBXXIvaTk',
    url='https://gateway.watsonplatform.net/tone-analyzer/api'
)

# initialize the Watson Assistant
assistant = AssistantV1(
    version='2019-02-28',
    iam_apikey='VbfeqWup87p3MP1jPbwoLXhFv7O-1bmSXiN2HZQFrUaw',
    url='https://gateway.watsonplatform.net/assistant/api'
)

workspace_id = 'f7bf5689-9072-480a-af6a-6bce1db1c392'

text_to_speech = TextToSpeechV1(
            iam_apikey='db8bGD6av4hlvFZxfJBnI3LodOnwRN-D8kX5AYMf_Lvk',
            url='https://stream.watsonplatform.net/text-to-speech/api'
)

emotions = ['sadness','joy','anger','fear']
           
class Transcriber:
    def __init__(self,path_to_audio_file):
        self.path_to_audio_file = path_to_audio_file

    def transcribe_audio(self):
        # initialize speech to text service
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
               
            input_text = {
                'workspace_id': workspace_id,
                'input': {
                    'text': speech_text
                }
            }
        
        return input_text

class Dialogue:

    def __init__(self,input_text):
        self.input_text = input_text
        self.intent_state = None
        self.entity_state = None
        self.top_tone = None
        self.top_tone_score = None
    
    def get_watson_intent(self):

        intent_response = assistant.message(workspace_id=workspace_id,
                                         input=self.input_text['input'],
                                        ).get_result()
        
        if intent_response['intents'][0]['confidence'] > 0.7:
            self.intent_state = intent_response['intents'][0]['intent']
            print("response with detected intent")
            print(json.dumps(intent_response, indent=2))
            return self.intent_state

        return None

    def get_watson_entity(self):
        
        entity_response = assistant.message(workspace_id=workspace_id,
                                         input=self.input_text['input'],
                                        ).get_result()
        if self.intent_state:
            entity_response['intents'][0]['intent'] = self.intent_state
            entity_response['intents'][0]['confidence'] = None
        
        if entity_response['entities']:
            if entity_response['entities'][0]['confidence'] > 0.5:
                self.entity_state = entity_response['entities'][0]['value']
                print(json.dumps(entity_response, indent=2))
                return self.entity_state

        return None

    # get the top emotion
    def get_watson_tone(self):
        
        # initialize emotion data
        max_score = 0.0
       
        tone_analysis = tone_analyzer.tone(tone_input=self.input_text['input'], content_type='application/json').get_result()
       
        # create list of tones
        tone_list = tone_analysis['document_tone']['tones']
       
        # find the emotion with the highest tone score
        for tone_dict in tone_list:
            if tone_dict['tone_id'] == "sadness" or tone_dict['tone_id'] == "joy" or \
            tone_dict['tone_id'] == "anger" or tone_dict['tone_id'] == "fear":
                if tone_dict['score'] > max_score:
                    max_score = tone_dict['score']
                    self.top_tone = tone_dict['tone_id']
                    self.top_tone_score = tone_dict['score']
                # set a neutral emotion if under tone score threshold
                if max_score <= TOP_TONE_SCORE_THRESHOLD:
                    self.top_tone = 'neutral'
                    self.top_tone_score = None
        return self.top_tone, self.top_tone_score

    def get_intent_response(self):

        intent_res_list = self.build_intent_res()
        
        try:
            for response_dict in intent_res_list:
                for response in response_dict[self.intent_state]:
                    yield response    
        except KeyError:
            return

    def get_entity_response(self):

        # self.entity_state = self.get_watson_tone()
        
        entity_res_list = self.build_entity_res()
        
        try:
            for response_dict in entity_res_list:
                for response in response_dict[self.entity_state]:
                    yield response 
        except KeyError:
            return

    def get_tone_response(self):
        
        tone_res_list = self.build_tone_res()
        
        try:
            for emo,response_dict in zip(emotions,tone_res_list):
                if emo == self.top_tone:
                    for response in response_dict[self.entity_state]:
                        yield response
        except KeyError:
            return

    def build_intent_res(self):
    
        return [{'work':["What did you do at your" + " " + self.intent_state + "?"],'reading':["What book did you read?"],'friends':["Which friend did you visit?"]}]

    def build_entity_res(self):
        
        return [{'meeting':["Oh, how was the" + " " + self.entity_state,"Oh no, What happened at the" + " " + self.entity_state + "?","Oh no, What happened at the" + " " + self.entity_state + "?"],
                 'coworker':["Oh, what bothered you about your" + " " + self.entity_state,"Ah. Does your" + " " + self.entity_state + " " + "at least try to come up with a middle ground?",
                 "Oh I am sorry to hear. Maybe if you speak to someone higher up they can help sort things out for you."],
                 'client':["Wow! Congratulations! What does this mean?"],
                 'promotion':["That's so wonderful, congratulations again! I knew you were capable of such an amazing thing!"],
                 'Minor':["Oh, wow! What were your thoughts about the"  + " " + self.entity_state + "?","I am so glad to hear you enjoyed the" + " " + self.entity_state + "!","Anytime, Goodbye now!!"],
                 'Twilight':["Oh, I've heard of" + " " +  self.entity_state + " " + "but forgot what it was about!","Haha, really, why?!","Oh dear! Okay, I will be sure not to pick up" + " " + self.entity_state + ".To lighten things up for you, let me recommend reading The Minor, by Sotseki"],
                 'concert':["Oh who did you see at the" + " " + self.entity_state + "?"],
                 'Beach House':["Cool! I love" + " " + self.entity_state + "!" + " " + ".How did they perform?"],
                 'John':["Okay, what did you do with" + " " + self.entity_state + "?", "Oh okay. Is eveyrthing alright with you though?",
                 "I'm sorry to hear that. Well let me know if you ever want to talk about" + " " + self.entity_state + ".You know I am here for you!","Anytime!"],
                 'Penny':["Okay, what did you do with" + " " + self.entity_state + "?"]}]

    def build_tone_res(self):
        # sadness, joy, anger, fear response lists for all entities
        return [{'meeting':["Oh no, you sound" + " " + self.top_tone + ".What happened at the" + " " + self.entity_state + "?",
                "Oh sorry I missed that, you sound" + " " + self.top_tone + ".what happened at the" + " " + self.entity_state + "?"],
                'coworker':["Oh no, you sound sad,what bothered you about" + " " + self.entity_state,"Oh no, you sound sad,what bothered you about" + " " + self.entity_state],
                'Twilight':["Oh dear! Okay, I will be sure not to pick up" + " " + self.entity_state + ".To lighten things up for you, let me recommend reading The Minor, by Sotseki"],
                'John':["Oh okay. Is eveyrthing alright with you though?","I'm sorry to hear that. Well let me know if you ever want to talk about" + " " + self.entity_state + ".You know I am here for you!",
                "Anytime! I love you!"]},
                    
                {'coworker':["Good to hear you are experiencing" + self.top_tone + ".I'm always here for you.","Good to hear you sound happy again"],
                'client':["Wow! Congratulations! What does this mean?"],
                'promotion':["That's so wonderful, congratulations again! I knew you were capable of such an amazing thing!","Anytime!"],
                'Minor':["I am so glad to hear you enjoyed the" + " " + self.entity_state + "!","Anytime! Goodbye now dear Ronnie!"],
                'Twilight':["Anytime, Goodbye Now dear Ronnie!"],
                'Beach House':["Wow that's awesome! Any band that makes makes Penny feel" + " " + self.top_tone + " " + "is worth watching in my book!"],
                'John':["Anytime, I love you!"]},
                
                {'meeting':["Oh you sound a bit angry,I'm here to help you. What happened at the" + " " + self.entity_state,"Oh, You sound angry again about the" + " "  + self.entity_state],
                'coworker':["Oh, you are angry, let me help. What bothered you about" + " " + self.entity_state,"Oh, You sound angry again about" + " " + self.entity_state],
                'Twilight':["Oh dear! Okay, I will be sure not to pick up" + " " + self.entity_state + ".To lighten things up for you, let me recommend reading The Minor, by Sotseki"],
                'John':["Oh okay. Is eveyrthing alright with you though?","I'm sorry to hear that. Well let me know if you ever want to talk about" + " " + self.entity_state + ".You know I am here for you!"]},
                
                {'meeting':["Oh no, I am sorry you sound scared, what happened at the" + " " + self.entity_state,"Oh, You sound scared again about the" + " " +  self.entity_state],
                'coworker':["Oh don't be scared, what bothered you about" + " " + self.entity_state,"Oh, You sound scared again about" + " " + self.entity_state],
                'Twilight':["Haha, really, why?!","Oh dear! Okay, I will be sure not to pick up" + " " + self.entity_state + ".To lighten things up for you, let me recommend reading The Minor, by Sotseki"],
                'John':["Oh okay. Is eveyrthing alright with you though?","I'm sorry to hear that. Well let me know if you ever want to talk about" + " " + self.entity_state + ".You know I am here for you!"]}]
    
    # cozmo robot speaks the text response from Watson
    def cozmo_text(self,response):
        def cozmo_program(robot: cozmo.robot.Robot):
            robot.say_text(response).wait_for_completed()     
        cozmo.run_program(cozmo_program)
