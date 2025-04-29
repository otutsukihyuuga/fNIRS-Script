import pygame
import random
import sys
import time
import pandas as pd
import os
import uuid
from pylsl import StreamInfo, StreamOutlet
from lsl import LSL


# Initialize Pygame
pygame.init()

# Screen dimensions
screen_info = pygame.display.Info()
screen_width, screen_height = screen_info.current_w, screen_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height-50))
pygame.display.set_caption("Mental Arithmetic Test")

# Create LSL StreamInfo and StreamOutlet
channels=1
name = 'Trigger'
type = 'arithmetic'
# sampling_rate=10.2
datatype='int16'
source_id='fNIRS'
info = StreamInfo(name = name,type= type, channel_count=channels, channel_format=datatype, source_id=source_id)
#3 channels for response, question presented and mode
#mode will be of 3 types: break, question, pause
#this can be done with 1 channel as well. format: break, question: {q}, pause, key: {Yes/No}
#since there is no entry to other cases i'll have a entry flag which if true will send data to stream. this will have to do for 3 modes only.
outlet = LSL(StreamOutlet(info))

# Colors
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
green = (0, 255, 0)

# Fonts
font = pygame.font.Font(None, 74)
small_font = pygame.font.Font(None, 36)

def getAdd(carry,fdigits,ldigits):
    #carry: 0 based position from left in ldigit where u want carry to happen
    #fdigits > ldigits
    addend=0
    addund=0
    i=0

    fdigits -= ldigits
    while fdigits>0:
        addund += random.randint(1,9)
        fdigits-=1
    
    while i<ldigits:
        addend*=10
        addund*=10
        if i in carry:
          digit = random.randint(1,9) #[1,9]
        else:
          digit = random.randint(1,8) #[1,8]
        addund+=digit
        if i in carry:
            digit = random.randint(10-digit,9)
        else:
            digit = random.randint(1,9-digit)
        addend+=digit
        i+=1
    if addund == addend:#would only happen if fdigit==ldigit not using fdigit as it's value is changed
        return getAdd(carry,ldigits,ldigits)
    return addund,addend

def newGetAdd(digits):#dont't care if carry is present or not
    addends=[]
    for digit in digits:
        addund=0
        while digit>0:
            addund*=10
            addund += random.randint(1,9)
            digit-=1
        addends.append(addund)
    return addends

def getQuestionAnswerList(difficulty,q=[],a=[],quant=2,fprob=0.5):
    events=[True,False]
    prob=[1-fprob,fprob]
    while quant>0:
        quant-=1
        error=0
        if difficulty == 1:
            # x,y = getAdd(carry=[0], fdigits=2,ldigits=1)
            addends = newGetAdd([2,1])
            answer = random.choices(events,prob)[0]
            if not answer:
                error = random.choices([1,-1],[0.5,0.5])[0]

        elif difficulty == 2:
            # x,y = getAdd(carry=[],fdigits=2,ldigits=2)
            addends = newGetAdd([2,1,1])
            answer = random.choices(events,prob)[0]
            if not answer:
                error = random.choices([10,-10,1,-1],[0.25,0.25,0.25,0.25])[0]

        elif difficulty == 3:
            # x,y = getAdd(carry=[1],fdigits=2,ldigits=2)
            addends = newGetAdd([2,1,1,1])
            answer = random.choices(events,prob)[0]
            if not answer:
                error = random.choices([10,-10,1,-1],[0.25,0.25,0.25,0.25])[0]
            
        elif difficulty ==4:
            # x,y = getAdd(carry=[1],fdigits=3,ldigits=2)
            addends = newGetAdd([2,2])
            answer = random.choices(events,prob)[0]
            if not answer:
                error = random.choices([10,-10,1,-1],[0.25,0.25,0.25,0.25])[0]

        elif difficulty == 5:
            # x,y = getAdd(carry=[0,1],fdigits=3,ldigits=2)
            addends = newGetAdd([2,2,1])
            answer = random.choices(events,prob)[0]
            if not answer:
                error = random.choices([10,-10,1,-1],[0.25,0.25,0.25,0.25])[0]

        elif difficulty == 6:
            # x,y = getAdd(carry=[0,1],fdigits=3,ldigits=3)
            addends = newGetAdd([2,2,1,1])
            answer = random.choices(events,prob)[0]
            if not answer:
                error = random.choices([10,-10,1,-1],[0.25,0.25,0.25,0.25])[0]
        sum=0
        qString = ''
        for addend in addends:
            sum+=addend
            qString+=str(addend)+' + '
        qString = qString[:-2]
        q.append(qString+' = '+str(sum-error))
        a.append(answer)
    return q,a

def displayBreak(timer,break_duration,clock):
    timer+=clock.get_time()
    if timer>break_duration:
        break_duration=0
        timer=0
    else:
        # Render the input text
        screen.fill(white)
        display_text = 'Break Time left: '+str(timer//1000)+'/'+str(break_duration//1000)
        text_surface = font.render(display_text, True, black)
        screen.blit(text_surface, (screen_width // 2 - text_surface.get_width() // 2,
                                screen_height // 2 - text_surface.get_height() // 2))
    return timer,break_duration

def saveData(question,answer,response, participant_id):
    directory = 'data'

    if not os.path.exists(directory):
        os.makedirs(directory)
    file_name = str(participant_id) +'_Arithmetic_data.xlsx'
    file_path = os.path.join(directory, file_name)
    pd.DataFrame({
        'Questions':question,
        'Answers':answer,
        'Response':response
    }).to_excel(file_path,index=False)
    outlet.save(str(participant_id)+'_Arithmetic_mapping.json')

def main():
    clock = pygame.time.Clock()
    running = True

    difficulty = [1,2,3,4,5,6]
    # difficulty = [5,6]
    session = 2
    n=5
    sessionBreak = 10000
    levelBreak = 5000
    trialLengthList = [5000,6000,7000,6000,7000,8000] #change by trial and error for participants
    # trialLengthList = [7000,8000]
    bufferTime = 500
    trialLength = trialLengthList[0]
    
    index = 0
    break_duration = 0
    timer = 0
    difficultyIndex = 0
    pressed = False
    nextQuestion = False
    show_break = True
    show_question = True
    fprob = 0.5
    question, answer = getQuestionAnswerList(difficulty[difficultyIndex],quant=n,fprob=fprob)
    response=[]
    outletDataSent = -1 #0 for break, 1 for question, 2 for pause
    participant_id = input("Enter participant ID: ")
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if not pressed:
                    if event.key == pygame.K_m and show_question:
                        pressed = True
                        response.append(True)
                        outlet.push_sample('Pressed: Yes')
                    elif event.key == pygame.K_x and show_question:
                        pressed = True
                        response.append(False)
                        outlet.push_sample('Pressed: No')
                if event.key == pygame.K_RETURN and show_break:
                    show_break = False

        if break_duration>0:
            if outletDataSent!=0:
                outlet.push_sample('Break: '+str(break_duration//1000))
                outletDataSent=0
            timer,break_duration = displayBreak(timer,break_duration,clock)
            if break_duration == 0:
                show_question = True
                show_break = True
        elif show_break:
            screen.fill(white)
            stimulus_text = font.render("Break is over. Press enter when you are ready.", True, black)
            screen.blit(stimulus_text, (screen_width // 2 - stimulus_text.get_width() // 2,
                                    screen_height // 2 - stimulus_text.get_height() // 2))
        elif nextQuestion:
            screen.fill(white)
            if outletDataSent!=2:
                outlet.push_sample('Pause')
                outletDataSent=2
            info_text = font.render("+", True, black)
            screen.blit(info_text, (screen_width//2 - info_text.get_width()//2, screen_height // 2 - info_text.get_height() // 2))
            timer += clock.get_time()
            if timer>bufferTime:
                timer = 0
                pressed=False
                nextQuestion=False 
                index+=1
                if index == len(question):
                    difficultyIndex+=1
                    if difficultyIndex==len(difficulty):#after finishing 1 block
                        difficultyIndex=0
                        session-=1
                        if session == 0:
                            #todo record data along with time
                            saveData(question,answer,response,participant_id)
                            running = False
                            continue
                        break_duration = sessionBreak
                    else:
                        break_duration = levelBreak
                    question, answer = getQuestionAnswerList(difficulty[difficultyIndex],question,answer,quant=n,fprob=fprob)
                    trialLength = trialLengthList[difficultyIndex]
                else:
                    show_question = True
        elif show_question:
            # Clear the screen
            screen.fill(white)
            if outletDataSent!=1:
                outlet.push_sample('Question: '+question[index])
                outletDataSent=1
            # Render the input text
            display_text = question[index]
            text_surface = font.render(display_text, True, black)
            screen.blit(text_surface, (screen_width // 2 - text_surface.get_width() // 2,
                                        screen_height // 2 - text_surface.get_height() // 2))
            
            display_text = str(timer//1000)+'/'+str(trialLength//1000)
            if not pressed:
                stimulus_text = font.render(display_text, True, black)
            else:
                stimulus_text = font.render(display_text, True, white)
            screen.blit(stimulus_text, (screen_width // 2 - stimulus_text.get_width() // 2,
                                    7*screen_height//10 + stimulus_text.get_height() // 2))

            timer+=clock.get_time()
            if timer>trialLength:
                print(question[index])
                if not pressed:
                    response.append('NA')
                    outlet.push_sample('Pressed: NA')
                timer = 0
                nextQuestion=True
                pressed=True
                show_question = False
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()