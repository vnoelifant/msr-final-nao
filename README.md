# NAO: A Caring, Emotionally Intelligent Robot

This is the final project of the Northwestern MSR project. This project is an extension of the TJBot project last quarter. The goal is to program a NAO into a caring, emotionally intelligent robot using NAO software and Watson Services. The target audience is intended to be all people who want a companion, entertainment, or a support system during difficult times.


## Project Tracker

 Click [here](./PROGRESS.MD) to view project goals and progress. 

 ## NAO-Watson Framework (v1)

 ![](images/NAO_Watson_Architecture.png)

 ## NAO-Watson Framework (v2)

 ![](images/NAO_Watson_Architecture_v2.png)

 ## General Flow (v1) (IN WORK)

1. User speaks to NAO.
2. A client python application extracts speech in form of a .wav file. 
3. Python application sends the .wav file to Watson Speech to Text Service.
4. Watson Speech to Text converts the speech to text.
5. Watson Assistant analyzes makes a call to the Watson Tone Analyzer via IBM Cloud function
6. Watson Tone Analyzer analyzes the tone and returns tone back to Watson Assistant via IBM Cloud Function. Note that here it is intented to have Nao light up his eyes based on emotion. 
7. The tone is saved as a context variable and stored in the IBM Cloudant JSON database for tracking the flow of the dialogue. 
8. Watson Assistant makes an additional function call to Watson Studio (Watson's Machine Learning/Data Science Platform) for retrieving conversational response. 
9. Watson Studio trains Machine Learning Model coded in a Jupyter Notebook and using the dialogue training data stored in IBM Cloud Storage. The Cloud storage also stores the trained model and training results.
10. Watson Studio retrieves intelligent response generated via trained machine learning model. 
11. Watson Studio sends back the response back to Watson Assistant via IBM Cloud Function. 
12. The Watson Assistant API sends the textual response back to the client Python application.
13. The client Python application converts the text to speech via Nao's Text to Speech function. 
14. Nao speaks response to user. 
  * **NOTE**: Conversation transitions and endings are based on the state of the emotional tone (saved in the Cloudant DB). If For instance, a transition from a sad state to a happy state will trigger an end to the conversation. This is all managed in the dialogue nodes of Watson Assistant. The node flow is primarily driven by contextual variables representing emotional tone. Intents and Entities will be managed via Python Neural Network code in the Jupyter Notebook. **Need to figure out if importing the intents and entities from Watson Assistant is really needed and/or possible.**


 ## General Flow (v2)
 Same as steps above except that Watson's Natural Language Understanding service would extract sentiment (positive/negative), emotion, entities, concepts and keword extractions. Then that information would be used in a machine learning model to train against the dialogue training dataset in Watson Studio. **Need to figure out if importing this from Natural Language Understanding is really needed and/or possible.**

## Included components

* Python Application including functions to run the NAO robot and connect to Watson Services. Tools included in application are:
  * [Nao-Robot Python-SDK](http://doc.aldebaran.com/2-1/dev/python/index.html): Allows devveloper to create Python modules that can run remotely or on the robot.
  * [Watson Developer Python-SDK](https://github.com/watson-developer-cloud/python-sdk): Client library to use the IBM Watson services in Python and available in pip as watson-developer-cloud

* [Watson Studio](https://cloud.ibm.com/cloud/watson-studio): IBM’s Watson Studio is a data science platform that provides all the tools necessary to develop a data-centric solution on the cloud. It makes use of Apache Spark clusters to provide the computational power needed to develop and train complex machine learning models. You can choose to create assets in Python, Scala, and R, and leverage open source frameworks (such as TensorFlow) that are already installed on Watson Studio. 

* [Watson Assistant](https://cloud.ibm.com/apidocs/assistant): The IBM Watson™ Assistant service combines machine learning, natural language understanding, and integrated dialog tools to create conversation flows between your apps and your users.

* [Jupyter Notebooks](https://jupyter.org/): An open-source web application that allows you to create and share documents that contain live code, equations, visualizations and explanatory text.

* [IBM Cloud Object Storage](https://www.ibm.com/cloud/object-storage?cm_mmc=Search_Google-_-Hybrid+Cloud_Cloud+Platform+Digital-_-WW_NA-_-ibm%20cloud%20storage_e&cm_mmca1=000016GC&cm_mmca2=10007090&cm_mmca7=9021485&cm_mmca8=kwd-358437825807&cm_mmca9=_k_EAIaIQobChMI96b1oJjr4wIVhJ6fCh0wYAm5EAAYASAAEgILTvD_BwE_k_&cm_mmca10=317209285678&cm_mmca11=e&gclid=EAIaIQobChMI96b1oJjr4wIVhJ6fCh0wYAm5EAAYASAAEgILTvD_BwE): A highly scalable cloud storage service, designed for high durability, resiliency and security.

* [IBM Cloud Watson Machine Learning](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ml-overview.html): Create, train, and deploy self-learning models.

* [IBM Watson Tone Analyzer](https://cloud.ibm.com/apidocs/tone-analyzer): Uses linguistic analysis to detect communication tones in written text.

* [IBM Cloudant](https://www.ibm.com/cloud/cloudant): A fully managed, distributed JSON document database.

* [Watson Speech To Text](https://www.google.com/search?ei=4oBIXZj2Dca4tQavgL24CQ&q=watson+speech+to+text+API&oq=watson+speech+to+text+API&gs_l=psy-ab.3..0l4j0i22i30l6.2150.2538..2781...0.0..0.89.319.4......0....1..gws-wiz.......0i71j0i67.vwnvoEZLDS0&ved=&uact=5): Transcribes speech from various languages and audio format.

* Alternative Solution: [Natural Language Understanding](https://www.ibm.com/cloud/watson-natural-language-understanding): Analyze text to extract metadata from content such as concepts, entities, keywords, categories, sentiment, emotion, relations, and semantic roles using natural language understanding. 
  * **Note** It seems this solution would provide more information from a speech utterance vs. just the Tone Analyzer. But not sure whether this vs. Tone integrated with Assistant would be a better choice. Also, can the intents and entities sent to be directly sent to Watson Studio machine learning model?

## Dialogue Flow (Preliminary)
![](images/nao_dialogue.png)


## List of Intents and Entities 

![](images/nao_intents.png)
![](images/nao_entities.png)


## Example Dialogue Flow: Tone = Sadness:

 ![](images/flow1.jpg)






