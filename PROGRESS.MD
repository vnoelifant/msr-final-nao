
# NAO: A Caring, Emotionally Intelligent Robot: Project Tracker

## Researcher/Developer: Veronica Medrano

## Advisor: Matthew Elwin 

This is a list of weekly goals as advised by Matthew Elwin, weekly accomplishments/issues noted by student researcher, and project meeting minutes. 

## **Weekly Goals**:

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

  