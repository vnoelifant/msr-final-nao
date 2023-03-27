import time
from naoqi import ALProxy


#word_list = []

#words = []
ROBOT_IP = "169.254.126.202"

tts = ALProxy("ALTextToSpeech", ROBOT_IP, 9559)
# Creates a proxy on the speech-recognition module
asr = ALProxy("ALSpeechRecognition", ROBOT_IP, 9559)

asr.pause(True)
asr.setLanguage("English")

# Example: Adds "yes", "no" and "please" to the vocabulary (without wordspotting)
#vocabulary = ["hey", "my", "name","is","ronnie"]
#vocabulary = ["hey"]
vocabulary= ["hi","hello there","mommy","tomorrow will be a great day","dog","cat","yo lindsey"]
#vocabulary = ["i","will","eat","food","now"]
asr.setVocabulary(vocabulary, False)

# Start the speech recognition engine with user Test_ASR
print 'Speech recognition engine started'
asr.subscribe("Test_ASR")

# memory proxy used to write values
memProxy = ALProxy("ALMemory", ROBOT_IP, 9559)
memProxy.subscribeToEvent('WordRecognized',ROBOT_IP,'wordRecognized')
#asr.unsubscribe("Test_ASR")
#asr.pause(False)
#time.sleep(10)
#memProxy.removeData("WordRecognized")


try:
	#memProxy.removeData("mommy")
	#asr.unsubscribe("Test_ASR")

	while len(memProxy.getData("WordRecognized")) > 1:
		#memProxy.removeData("hello there")
		asr.pause(False)
		time.sleep(5)
		word = memProxy.getData("WordRecognized")[0]
		conf = memProxy.getData("WordRecognized")[1]
		#word = memProxy.getData("WordRecognized")
		asr.unsubscribe("Test_ASR")
		#asr.pause(True)
		print "word: %s" % word, "confidence: %s" % conf
		tts.say(word)
		asr.subscribe("Test_ASR")
		#asr.unsubscribe("Test_ASR") # not needed
		#memProxy.removeData("WordRecognized")[0]

except KeyboardInterrupt:
	print("KeyboardInterrupt has been caught.")


