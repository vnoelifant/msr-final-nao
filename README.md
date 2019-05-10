# NAO: A Caring, Emotionally Intelligent Robot

This is the final project of the Northwestern MSR project. This project is an extension of the TJBot project last quarter. The goal is to program a NAO into a caring, emotionally intelligent robot using NAO software and Watson Services. The target audience is intended to be all people who want a companion, entertainment, or a support system during difficult times.

## Project Tracker

 [Click here to view project status and timeline](https://docs.google.com/spreadsheets/d/1U-bm2-uXRQx1xlUcq1asHpyyIms6dJSCPX-FGHYObo8/edit#gid=1161341563). 

 ## Testing Flask with Watson. 

 IBM's voice bot code pattern was used to test integration of Watson services in a web app built on top of JQuery and Python Flask. See demo below. 

 [![IMAGE ALT TEXT](http://img.youtube.com/vi/enxMyH2EoZw/0.jpg)](http://www.youtube.com/watch?v=enxMyH2EoZw "Flask Watson Testing")

 ## NAO-Watson Framework

 ![](images/NAO_Watson_Architecture.png)

 ## General Flow

1. User speaks to NAO.
2. A client python application connected to NAO converts the speech to text and sends the text to the Watson Assistant API. 
3. The Watson Assistant API takes the text input, analyzed for intents (purposes of user inputs), and builds a dialogue that determines the responses NAO will give.
4. The Watson Assistant API sends the textual responses back to the client Python application.
5. The client Python application converts the text to speech.
6. Nao speaks response to user. 


**TODO**: Add numbers to flow diagram

## Included components

* [Nao-Robot Choregraphe Behaviour](http://doc.aldebaran.com/2-1/): The fruit of a unique combination of mechanical engineering and software, NAO is a character made up of a multitude of sensors, motors and software piloted by a made-to-measure operating system: NAOqi OS.

* [Node-RED](https://console.bluemix.net/catalog/starters/node-red-starter): Node-RED is a programming tool for wiring together APIs and online services.

* [Watson-Assistant-API](https://cloud.ibm.com/apidocs/assistant?code=python#get-response-to-user-input): Build, test and deploy a bot or virtual agent across mobile devices, messaging platforms, or even on a physical robot.





