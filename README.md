# NAO: A Caring, Emotionally Intelligent Robot

This is the final project of the Northwestern MSR project. This project is an extension of the TJBot project last quarter. The goal is to program a NAO into a caring, emotionally intelligent robot using NAO software and Watson Services. The target audience is intended to be all people who want a companion, entertainment, or a support system during difficult times.


## Project Tracker

 Click [here](./PROGRESS.MD) to view project goals and progress. 

 ## NAO-Watson Framework (IN WORK)

 ![](images/NAO_Watson_Architecture.png)

 ## General Flow

1. User speaks to NAO.
2. A client python application connected to NAO converts the speech to text and sends the text to the Watson Assistant API. 
3. The Watson Assistant API takes the text input, analyzed for intents (purposes of user inputs), and builds a dialogue that determines the responses NAO will give.
4. The Watson Assistant API sends the textual responses back to the client Python application.
5. The client Python application converts the text to speech.
6. Nao speaks response to user. 

## Included components

* Python Application including functions to run the NAO robot and connect to Watson Services. Tools included in application are:
  * [Nao-Robot Python-SDK](http://doc.aldebaran.com/2-1/dev/python/index.html): Allows devveloper to create Python modules that can run remotely or on the robot.
  * [Watson Developer Python-SDK](https://github.com/watson-developer-cloud/python-sdk): Client library to use the IBM Watson services in Python and available in pip as watson-developer-cloud

* [Watson-Assistant-Service](https://cloud.ibm.com/apidocs/assistant): The IBM Watson™ Assistant service combines machine learning, natural language understanding, and integrated dialog tools to create conversation flows between your apps and your users.

## Testing Flask with Watson. 

 IBM's voice bot code pattern was used to test integration of Watson services in a web app built on top of JQuery and Python Flask. See demo below. 

 [![IMAGE ALT TEXT](http://img.youtube.com/vi/enxMyH2EoZw/0.jpg)](http://www.youtube.com/watch?v=enxMyH2EoZw "Flask Watson Testing")



