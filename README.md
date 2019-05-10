# NAO: A Caring, Emotionally Intelligent Robot

This is the final project of the Northwestern MSR project. This project is an extension of the TJBot project last quarter. The goal is to program a NAO into a caring, emotionally intelligent robot using NAO software and Watson Services. The target audience is intended to be all people who want a companion, entertainment, or a support system during difficult times.

## Project Tracker

 [Click here to view project status and timeline](https://docs.google.com/spreadsheets/d/1U-bm2-uXRQx1xlUcq1asHpyyIms6dJSCPX-FGHYObo8/edit#gid=1161341563). 


 ## NAO-Watson Framework

 ![](/images/Nao_Watson_Architecture.png)

 ## General Flow

1. User speaks to NAO.
2. NAO converts the speech to text.
3. Node-RED flow sends the text to the Watson Assistant API. 
4. The Watson Assistant API takes the text input, analyzed for intents (purposes of user inputs), and builds a dialogue that determines the responses NAO will give.
5. The Watson Assistant API sends the textual responses back to Node-RED.
5. The Node-RED flow sends the dialogue responses back to NAO.
6. NAO convert the text to speech
7. NAO sends speech to user. 

## Included components

* [Nao-Robot Choregraphe Behaviour](http://doc.aldebaran.com/2-1/): The fruit of a unique combination of mechanical engineering and software, NAO is a character made up of a multitude of sensors, motors and software piloted by a made-to-measure operating system: NAOqi OS.

* [Node-RED](https://console.bluemix.net/catalog/starters/node-red-starter): Node-RED is a programming tool for wiring together APIs and online services.

* [Watson-Assistant-API](https://cloud.ibm.com/apidocs/assistant?code=python#get-response-to-user-input): Build, test and deploy a bot or virtual agent across mobile devices, messaging platforms, or even on a physical robot.





