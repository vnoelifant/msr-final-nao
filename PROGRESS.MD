
# NAO: A Caring, Emotionally Intelligent Robot: Project Tracker

## Researcher/Developer: Veronica Medrano

## Advisor: Matthew Elwin 

This is a list of weekly goals as advised by Matthew Elwin, weekly accomplishments/issues noted by student researcher, and project meeting minutes. 


## Testing Flask with Watson: Pre-Summer Task. 

 IBM's voice bot code pattern was used to test integration of Watson services in a web app built on top of JQuery and Python Flask. See demo below. 

 [![IMAGE ALT TEXT](http://img.youtube.com/vi/enxMyH2EoZw/0.jpg)](http://www.youtube.com/watch?v=enxMyH2EoZw "Flask Watson Testing")

## **Summer Weekly Goals**:

* ## **Week 6/24/19 Goals**
  * **Items for Nao**
    * a. Get the .wav file from Nao onto your computer for further processing
    * b. Use Nao's audio intensity monitoring functions to determine when to start and stop recording the audio
    * c. if you get stuck here you can move on to the watson api stuff and just either record audio files using pyaudio or pre-record some audio and assume you have the files.

  * **Items for Watson**
    * c. Use the watson api from python to duplicate the functionality of the TJ bot project
    * d. Switch to synchronous requests for the text to speech (see below)
  
  * ### **Meeting Agenda**:
    * #### Accomplishments
      * Research into how to retrieve audio from Nao's microphones
      * Wrote the following Python [script](https://github.com/vnoelifant/msr-final-nao/blob/master/nao_record.py) that extracts the audio from Nao's microphone to send to a .wav file to remote computer. 
      * Started python script shown [here](https://github.com/vnoelifant/msr-final-nao/blob/master/nao_dialogue.py) that transcribes speech from Nao to text using Watson Speech to Text Service. See video demo of this below:
           
      [![IMAGE ALT TEXT](http://img.youtube.com/vi/6iSMbHyA8Ns/0.jpg)](http://www.youtube.com/watch?v=6iSMbHyA8Ns "Nao Speech to Text using Watson")
      
      * Continued the following Python [script](https://github.com/vnoelifant/msr-final-nao/blob/master/nao_dialogue.py) with following functionalities:
        * Transcribe speech from Nao to text using Watson Speech to Text Service
        * Retrieve text response from Watson
        * Send Watson text response to Nao for text to speech conversion
        * Have Nao speak back Watson response
        * Note: Program ends with keyboard interrupt.
        * See video demo below:

        [![IMAGE ALT TEXT](http://img.youtube.com/vi/m6YzH69SGXU/0.jpg)](http://www.youtube.com/watch?v=m6YzH69SGXU "Nao meets Watson")
    
    * #### Issues
      * Challenging to retrieve audio from Nao. Attempted piping file with no luck. Finally further research directed me to use Naoqi ALAudioDevice subscribe/unsubscribe, and setClientPreferences functions.
      * Sometimes takes a long wile to get back text response, or program will timeout
      * Audio file is being overwritten

    * #### TODO
      * Add silence detection functionality and start/stop recording functions
      

  * ### **7/10/19 Meeting Minutes**:
    * Tips on structuring code to allow for silent detections/start/stop recording functions
    * Tips on audio file management
      * Append to audio file/clear buffer, etc. 
      * Analyze the audio array data, get its length, get max length for max noise, etc.

* ## **Week 7/8/19 Goals**
  * 1. Update the audio capturing process so that it writes a single stretch of speech (as bracketed by silence both before and after) to a file and then signals the main loop to start processing the speech. After a statement has been captured, recording should be stopped until the main loop processes the statement
  * 2. When signaled by the audio process, the main loopuses watson to transcribe the audio, and then process it. Once the audio has been processed, recording starts again.
  * 3. In particular one processing step you should implement is an exit phrase.   if the exit phrase occurs, you should exit the program
  * 4. Once you get the above working you should start thinking/implementing the logic for processing the transcribed audio.



  * ### **Meeting Agenda**:
    * #### Accomplishments
      * Continued the following Python [script](https://github.com/vnoelifant/msr-final-nao/blob/master/nao_dialogue.py) using this tutorial for Pepper as reference:
      https://medium.com/@pwc.emtech.eu/pepper-integration-with-dialogflow-1d7f1582da1a. Updated script has following functionalities:
        * peak calculation for sound detection
        * silence detection
        * event thread for speech recognition and Queue for audio storage
        * trigger to stop event thread
        * MORE TO BE UPDATED
        * See video demo below:

       [![IMAGE ALT TEXT](http://img.youtube.com/vi/ttEaqCrsf54/0.jpg)](http://www.youtube.com/watch?v=ttEaqCrsf54 "Nao Dialogue")
    
    * #### Issues/Questions
      * IN WORK
      * Is there a way to clear the wav files after conversion?
      * Get this error often coming from Watson side, and doesn't respond:
        * Traceback (most recent call last):
  File "/home/veronicanoel90/NAO/scripts/nao_recorder_2.py", line 224, in stop_recording
    user_speech_text = speech_recognition_results['results'][0]['alternatives'][0]['transcript']
IndexError: list index out of range
catch index error and print results. Write pseudocode in functions first. Fill in one by 1. 


    * #### TODO
      * IN WORK
      * Restructure updated code and commit to Github 
      

  * ### **7/18/19 Meeting Minutes**:
    * Commit regularly
    * Revisit the pseudocode from meeting on 7/10/19 and get that working

* ## **Week 7/16/19 Goals**
  * At the meeting on 7/18 pseudocode was developed that describes the basic operation of the system that I am developing.  This week's goal is to implement that code and get it working.
  * ### **Meeting Agenda**:
    * #### Accomplishments
      * Major code updates that integrates the developed pseudocode. Updates include:
        * Silence detection
       * Peak sound detection
        * Pause recording flag and pause/resume recording functions
        * Averaging out volume of sound
        * Re-initializing audio buffer (in memory file) when resuming recording
        * Previous sound before peak sound reached added to buffer
        * See demo of code below:
 
      [![IMAGE ALT TEXT](http://img.youtube.com/vi/9iVaZ5tdjmw/0.jpg)](http://www.youtube.com/watch?v=9iVaZ5tdjmw "Nao Dialogue Test")
    
    * #### Issues
      * Had initial trouble in getting enough .wav audio data
        * resolved with  adding .seek(0) python function before converting to .wav. This function offsets the raw audio file to the beginning of file
      * Trouble with unsubsribing (stops program too soon). Discussed with Matt on approaches. 
      * Transcription seems to miss words: In playing the .wav file, the sound sounds very choppy. 
    * #### TODO
      * Trim leading and trailing silence in audio buffer
      * look at index in range error in Watson transcription
      * look into how to check whether a sentense has been uttered
      * analyze audio data
        * how long is audio sample?
        * might need to save data across multiple process remote data calls
        * may need to get different data and different sentences
      
  * ### **7/25/19 Meeting Minutes**:
    * Try to keep data as an array
    * Run tests to hear/play the .wav file

* ## **Week 7/29/19 Goals**
  * Implement speech_detect() such that you reliably have the following working:
    * 1. You speak to Nao
    * 2. You capture the speech. (This is where you need speech_detect() to determine when to pauseRecording(), create the .wav file, and have watson process the audio.)
    * 3. Watson transcribes the speech
    * 4. Nao speaks a response
    * 5. Goto step 1.

  * Start designing the dialog logic and start incorporating more watson api calls into the main loop. This includes 2 pieces: 
    * 1. Specifying the desired behavior, based on the capabilities of the watson api:
      * What are the intents you want to define?
      * What emotions do you want to detect?
      * How do you want the dialog to fit together?
        * Recommendation:  drawing a rough flow chart for this (doesn't need to be pretty but should show the interactions of the different pieces).  

    * 2. Start coding the behavior that you specified
      * One simple suggestion for a first step: 
        * Define an intent for "stop talking" and use this intent, rather than exact phrase matching, to exit the program.

  * ### **Meeting Agenda**:
    * #### Accomplishments
      * Updates to code to make the speech detection more reliable. Used deques, for instance a silence buffer that throws away silent data, and a speech buffer to hold speech surrounded by silence. Silence was detected based on a counter. 

    * #### Issues
      * None
    * #### TODO
      * AI portion of project
  
  * ### **7/29/19 Meeting Minutes**:
    * may need to tweak the sound threshold to make more rpbust. Ex: adding in a percentage. But this is not urgent. 
    * Check if any background items are running on Nao, to ensure Nao is only running my sound. 
    * AI and Watson Research: 
      * 1. what is AI going to do in phrasing?

        * 1a. What behavior do I want?

        * 2. how to structure code to achieve behavior. Main loop. Synchornous watson API. Transcribe text, now what do we do?

        * 3. implement the code. Continue pseudocode

        * 4. getting tone detection

      * Send by email the flow chart


* ## **Week 8/5/19 Goals**
  * Flowchart on the AI design of project
  * Per Matt comments on meeting 8/5/19: Get tone detection dialogue scenario from flow chart working. 

  * ### **Meeting Agenda**:
    * #### Accomplishments
      * Designed a couple of new frameworks on AI design, list of planned intents/entities, and a simple dialogue flowchart, and discussed with Matt
        * Discussed following: 
          * challenges: 
            * hard to find a Watson service to deliver intelligent responses
            * suggestions: 
              * try not to use Watson Studio
              * look into potential feasibility of RASA dialogue framework
              * modifying dialogue training data to include emotion label
              * test out tone detection on NAO without using Watson Assistant before working on the intelligent dialogue portion
      * Coded tone detection for simple sad emotion dialogue scenario per flowchart
        * Tested with success on Nao. See demo below!

        [![IMAGE ALT TEXT](http://img.youtube.com/vi/3_psNvxDgfc/0.jpg)](http://www.youtube.com/watch?v=3_psNvxDgfc "Nao Detects Silence")

    * #### Issues
      * Watson Natural Language Understanding seems to only take long text input vs Tone Analyzer. For instance "I am sad" on NLU yielded a response error message requesting more text input
    * #### TODO
      * AI portion of project
        * Look into capabilities of RASA Python dialogue framework
  
  * ### **8/8/19 Meeting Minutes**:
    * 




