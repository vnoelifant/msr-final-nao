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

# conainer for tone history
tone_hist = []

# container for intent history
intent_list = []

# if set to true, stores initial intent for each user utterance to maintain same intent
# if set to false,initial intent is not stored and intent detection is random
keep_intent = True

# create Watson Assistant dialogue logic:
# call the Watson Tone analyzer service
# get the current tone from tone analyzer service
# append tone and tone score to dictionary to maintain tone history
# get Nao response according to tone and intent conditions
def analyze_tone(user_speech_text):
    tone_analysis = tone_analyzer.tone(tone_input=user_input_text['input'], content_type='application/json').get_result()
    print(json.dumps(tone_analysis, indent=2)) 
    detected_emotion, tone_hist = get_top_emo(user_input_text, tone_analysis)
    return detected_emotion, tone_hist

def get_intent_response(user_speech_text):
    intent_response = assistant.message(workspace_id=workspace_id,
                                     input=user_speech_text['input'],
                                    ).get_result()
    print "response with detected intent"
    print(json.dumps(intent_response, indent=2))
    intent = intent_response['intents'][0]['intent']
    intent_list.append(intent)
    return intent_list,intent_response
    
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
def get_top_emo(user_speech_text,tone_analysis):
    
    # initialize emotion data
    max_score = 0.0
    top_emotion = None
    top_emo_score = None
    
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
        print "updated tone analysis", tone_analysis

        # append tone and tone score to tone history list
        tone_hist.append({
                    'tone_name': top_emotion,
                    'score': top_emo_score
         })
 
    return top_emotion, tone_hist

# list of responses from nao for work intent
def work_intent():
    yield "Oh, how was work?"
    yield "Ah. how were they?"
    yield "Oh no, do you want to talk about it?"
    yield "Aw, why is that?"

def reading_intent():
    yield "Oh, what book did you read?"
    yield "Cool, what was it about?"

def friends_intent():
    yield "Oh, which friend did you visit?"
    yield "Oh,what did you all do?"

# get response from Nao based on intents and/or entities
def get_convo_response(intent_list,intent_response,keep_intent,res_work, res_reading, res_friends):
    # if driving the conversation flow based on first detected intent
    if keep_intent:
        print "first detected intent from intent list: ",intent_list[0]
        intent_response['intents'][0]['intent'] = intent_list[0] 
        print "detected intent",intent_response['intents'][0]['intent']
        
        if intent_response['intents'][0]['intent'] == "work":
            print "detected work convo"
            get_nao_response(next(res_work))
        elif intent_response['intents'][0]['intent'] == "reading":
            print "detected reading convo"
            get_nao_response(next(res_reading))
        elif intent_response['intents'][0]['intent'] == "friends":
            print "detected friends convo"
            get_nao_response(next(res_friends))
    else:
        # TODO: add more conditional code here to redirect conversation not based on 
        # maintained initial intent
        print "generate response not based on initial maintained intent"
        print "detected intent: ",intent_response['intents'][0]['intent'] 

    print "response"
    print(json.dumps(intent_response, indent=2))

def main():
    """ Main entry point

    """
    # initialize generator objects for Nao's responses to utterances
    res_work = work_intent()
    res_reading = reading_intent()
    res_friends = friends_intent()

    
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
    # subscribe to Naoqi and begin recording speech
    SoundReceiver.start_recording() 

    try:
        # waiting while recording in progress
        while True:
            time.sleep(1)
            # done recording; ready to transcribe speech
            if SoundReceiver.recording == False:
                print "stopped recording, ready to transcribe"
                
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
                    
                    # TODO: Update tone analyzer conditional logic
                    # send user_speech_text to Watson Tone Analyzer to be analyzed for tone
                    # detected_emotion, tone_hist = analyze_tone(user_speech_text)
                    
                    # send user_speech_text to Watson Assistant to be analyzed for intents and entities 
                    try:
                        # generate intents
                        intent_list,intent_response = get_intent_response(input_text)
                        # dialogue flow based on first detected intent maintained and unchanged
                        # throughout conversation turn or not maintained
                        get_convo_response(intent_list,intent_response,keep_intent,res_work, res_reading,res_friends)           
                    except:
                        traceback.print_exc()
                        print "error in intent detection"
                        nao_response = "Hmm. I couldn't understand you. Can you repeat what you just said?"
                        get_nao_response(nao_response) 
                        pass
                        #get_convo_response(intent_list,intent_response,keep_intent)   
                except:
                    print "error in speech detection"
                    nao_response = "Hmm. I couldn't understand you. Try telling me what's going on again."
                    get_nao_response(nao_response) 
                    traceback.print_exc()
                    print "try speaking again"
                    pass
         
                print "resuming"
                SoundReceiver.resume_recording()        
    
    except KeyboardInterrupt:
        # closing
        myBroker.shutdown()
        print("disconnected")
        sys.exit(0)

if __name__ == "__main__":
    main()



