import json
from dialogue_cozmo import Transcriber,Dialogue
import traceback
import sys
from recorder_cozmo import Recorder

def main():

    convo_loop_count = 0
    start_dialogue = False  
    keep_intent = True
    keep_entity = True
    tone_hist = []
    misunderstood = False
    intent_list = []
    entity_list = []
    my_speech = Transcriber('speech.wav')
   

    while not start_dialogue:
        print("convo turn loop count",convo_loop_count)
        
        try:
            print("starting recording process")
            recorder = Recorder("speech.wav")
            print("Please say something nice into the microphone\n")
            recorder.save_to_file()
            print("Transcribing audio....\n")
          
            try: 
                input_text = my_speech.transcribe_audio()
                if input_text == "goodbye":
                    break
        
                if input_text:
                    start_dialogue = True
                my_convo = Dialogue(input_text)

                # begin detecting intent
                try:    
                    if keep_intent:
                        if len(intent_list) > 0:
                            pass
                        else:
                            my_convo.get_watson_intent()
                            if my_convo.intent_state:
                                intent_list.append(my_convo.intent_state)
                            # initialize intent response generator object
                            int_res = my_convo.get_intent_response()
                            try:
                                my_convo.cozmo_text((next(int_res)))
                            except StopIteration: 
                                pass
                            start_dialogue = False
                            continue

                    # detect entity  and tone based on intent
                    try:
                        if len(entity_list) > 0:
                            pass
                        else:
                            my_convo.get_watson_entity()
                            if my_convo.entity_state:
                                entity_list.append(my_convo.entity_state)
                        
                        # initialize entity response generator object
                        if len(entity_list) == 1 and my_convo.entity_state:
                            # initialize entity response generator object
                            ent_res = my_convo.get_entity_response()

                        my_convo.get_watson_tone()
                        if my_convo.top_tone_score: #and top_emo_score >= 0.70:
                                    tone_hist.append({
                                            'tone_name': my_convo.top_tone,
                                            'score': my_convo.top_tone_score
                                 })

                         # initialize tone response generator object
                        if len(tone_hist) == 1:
                            # initialize tone response generator object
                            tone_res = my_convo.get_tone_response()

                        # start dialogue with Nao
                        while start_dialogue:
                            # dialogue flow including entities and tone based on first detected intent 
                            # maintained throughout conversation turn or not maintained  
                            if keep_entity:
                                if entity_list and not tone_hist:
                                    try:
                                        my_convo.cozmo_text((next(ent_res)))
                                        # new test to transition to other entity
                                        if entity_list[0] == "Penny":
                                            keep_entity = False
                                        if entity_list[0] == "concert":
                                            keep_entity = False
                                        if entity_list[0] == "client":
                                            keep_entity = False
                                    except StopIteration: 
                                        pass

                           
                                if tone_hist:
                                    try:                          
                                        my_convo.cozmo_text(next(tone_res))
                                        if entity_list[0] == "meeting":
                                            keep_entity = False
                                        if "coworker" in entity_list and top_tone == "joy":
                                            keep_intent = False
                                        if "Beach House" in entity_list and top_tone == "joy":
                                            keep_intent =False
                                        if "John" in entity_list and top_tone == "joy":
                                            keep_intent = False
                                        if entity_list[0] == "client":
                                            keep_entity = False
                                        if "promotion" in entity_list and top_tone == "joy":
                                            keep_intent = False
        
                                    except StopIteration: 
                                        pass  

                                    entity_list.append(my_convo.entity_state)
                             
                            if not keep_entity:
                                entity_list = []
                                tone_hist = []

                            # start detecting for new intent, clear prior intent, entity and tone lists
                            if not keep_intent:
                                intent_list = []
                                entity_list = []
                                tone_hist = []

                            start_dialogue = False
                            keep_entity = True
                            keep_intent = True
                            # end conversation
                    except:
                        traceback.print_exc()
                        pass
                    
                except:
                    traceback.print_exc()
                    pass
                    
            except:
                traceback.print_exc()
                print("error in speech detection")
                my_convo.cozmo_text("Oh Watson, a little rusty today in your detection eh? Sorry, user, can you repeat that?")
                pass
           
        except KeyboardInterrupt:
            print("closing")
            sys.exit(0)

        convo_loop_count += 1
               
    
if __name__ == '__main__':
    main()

