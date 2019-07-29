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
from os.path import join, dirname
from ibm_watson import SpeechToTextV1, AssistantV1
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


NAO_IP = "169.254.126.202" 

def get_nao_response(watson_text):
    tts = ALProxy("ALTextToSpeech", "169.254.126.202", 9559)
    tts.say(watson_text)

def get_watson_response(user_speech_text):
    # initialize the Watson Assistant
    assistant = AssistantV1(
        version='2019-02-28',
        iam_apikey='VbfeqWup87p3MP1jPbwoLXhFv7O-1bmSXiN2HZQFrUaw',
        url='https://gateway.watsonplatform.net/assistant/api'
    )

    response = assistant.message(
    workspace_id='5db84ece-e19e-4914-9993-ab7206b50a5c',
    input={'text': user_speech_text}).get_result()
    print(json.dumps(response, indent=2))
    watson_text_response = response['output']['text'][0]
    watson_text_response = '{}'.format(watson_text_response)
    return watson_text_response

def transcribe_audio(path_to_audio_file):
    # initialize speech to text service
    speech_to_text = SpeechToTextV1(
        iam_apikey='4aXD2UR_3lDdbH6XwF1u2g0OP8-jAuAU2uVmafislERZ',
        url='https://stream.watsonplatform.net/speech-to-text/api')

    with open((path_to_audio_file), 'rb') as audio_file:
        return speech_to_text.recognize(
                audio=audio_file,
                content_type='audio/wav',
                word_alternatives_threshold=0.9,
                keywords=['hey', 'hi','watson','friend','meet'],
                keywords_threshold=0.3
            ).get_result()


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
    # The name given to the constructor must be the name of the variable
    #fileCounter += 1
    global SoundReceiver
    SoundReceiver = SoundReceiverModule("SoundReceiver", pip)

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
                speech_recognition_results = transcribe_audio('speak9.wav')
                print(json.dumps(speech_recognition_results, indent=2))
                user_speech_text = speech_recognition_results['results'][0]['alternatives'][0]['transcript'] 
                print("User Speech Text: " + user_speech_text + "\n")
                watson_text_response = get_watson_response(user_speech_text)
                print("Watson Text Response",watson_text_response)
                # trigger to end conversation
                if watson_text_response == "Ok goodbye":
                    print "stop conversation"
                    get_nao_response(watson_text_response)
                    break
                else:
                    get_nao_response(watson_text_response)
                    print "resuming"
                    # start recording again
                    SoundReceiver.resume_recording() 
    
    except KeyboardInterrupt:
        # closing
        myBroker.shutdown()
        print("disconnected")
        sys.exit(0)

if __name__ == "__main__":
    main()



