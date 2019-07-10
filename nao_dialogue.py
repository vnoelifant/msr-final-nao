import os
import json
from os.path import join, dirname
from ibm_watson import SpeechToTextV1
from optparse import OptionParser
import naoqi
import numpy as np
import time
import sys
import os
import wave
from os.path import join, dirname
import json
#from naoqi import ALProxy
from nao_recorder import SoundReceiverModule

NAO_IP = "169.254.126.202" 

def get_nao_response(text):
    tts = naoqi.ALProxy("ALTextToSpeech", "169.254.126.202", 9559)
    tts.say("Hey there friend!")

def transcribe_audio(path_to_audio_file):
    # initialize speech to text service
    speech_to_text = SpeechToTextV1(
        iam_apikey='4aXD2UR_3lDdbH6XwF1u2g0OP8-jAuAU2uVmafislERZ',
        url='https://stream.watsonplatform.net/speech-to-text/api')

    with open((path_to_audio_file), 'rb') as audio_file:
        speech_recognition_results = speech_to_text.recognize(
                audio=audio_file,
                content_type='audio/wav',
                word_alternatives_threshold=0.9,
                keywords=['hey', 'hello', 'hi'],
                keywords_threshold=0.5
            ).get_result()
        print(json.dumps(speech_recognition_results, indent=2))
        with open('test5_response.txt', 'w') as responsefile:  
            json.dump(speech_recognition_results, responsefile)
        text = speech_recognition_results['results'][0]['alternatives'][0]['transcript'] # figure out how to print more transcripts! (loop?)
        # think there is an example of this in the javascript examples from winter quarter (sports buddy)
        print("Text: " + text + "\n")

    get_nao_response(text)

def main():
    """ Main entry point

    """
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
    myBroker = naoqi.ALBroker("myBroker",
       "0.0.0.0",   # listen to anyone
       0,           # find a free port and use it
       pip,         # parent broker IP
       pport)       # parent broker port


    # Warning: SoundReceiver must be a global variable
    # The name given to the constructor must be the name of the variable
    global SoundReceiver
    SoundReceiver = SoundReceiverModule("SoundReceiver", pip)

    print("Please say something into NAO's microphone\n")
    SoundReceiver.start()

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print
        print "Interrupted by user, shutting down"
        print("Transcribing audio....\n")
        transcribe_audio('test6.wav')
        sys.exit(0)

if __name__ == "__main__":
    main()



