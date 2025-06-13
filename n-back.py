import pygame
import random
import sys
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
pygame.display.set_caption("N-back Test")

# Create LSL StreamInfo and StreamOutlet
channels=1
name = 'LsLTriggers'
type = 'n-back'
# sampling_rate=10.2
datatype='int16'
source_id='fNIRS'
info = StreamInfo(name = name,type= type, channel_count=channels, channel_format=datatype, source_id=source_id)
#here types of markers would be break, instruction, stimulus, pause, response
# break: break time; instruction: N, stimulus: stimulus; pause; response: response

outlet = LSL(StreamOutlet(info))

# Colors
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
green = (0, 255, 0)

# Fonts
font = pygame.font.Font(None, 74)
small_font = pygame.font.Font(None, 36)

# Generate random sequence of stimuli
def generate_stimuli(N, stimuliRange, minHits, maxHits,sequence_length):
    hits = random.randint(minHits,maxHits)
    sequence = [random.randint(stimuliRange[0], stimuliRange[1]) for _ in range(sequence_length)]
    
    #get passes
    passes = sorted(random.sample(range(N, sequence_length), hits))

    for i in range(sequence_length):
        if i in passes: #if this has to be a hit then make it
            sequence[i] = sequence[i-N]
        if i+N < sequence_length and sequence[i] == sequence[i+N]: #make sure this number isn't a hit for next nback
            if sequence[i+N] == stimuliRange[1]:
                sequence[i+N] = sequence[i+N]-1
            else:
                sequence[i+N] = sequence[i+N]+1

    return sequence,passes

def update_df(N_back,inputs,passes, stimuli, df):
    inputs = ' '.join(map(str,inputs))
    passes = ' '.join(map(str,passes))
    stimuli = ' '.join(map(str,stimuli))

    new_df = pd.DataFrame({
        'N_back':[N_back],
        'inputs': [inputs],
        'passes': [passes],
        'stimuli': [stimuli]
    })
    df = pd.concat([df,new_df],ignore_index=True)
    return df

def save_df(df, participant_id):
    # Directory where you want to save the file
    directory = 'data'

    # Create the directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_name = str(participant_id) +'_Nback_data.xlsx'
    file_path = os.path.join(directory, file_name)

    # Save the DataFrame to an Excel file
    df.to_excel(file_path,index=False)
    file_name = str(participant_id) +'_Nback_mapping.json'
    file_path = os.path.join(directory, file_name)
    outlet.save(file_path)
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
    pygame.display.flip()
    clock.tick(60)
    return timer,break_duration
# Main game loop
def main(N,sessions,stimuliRange,sequence_length, minHits, maxHits, stimulus_duration, next_stimulus, sessionBreak, blockBreak):
    inputs=[]
    df = pd.DataFrame({
        'N_back':[],
        'inputs':[],
        'passes':[],
        'stimuli':[]
    })
    outletDataSent = -1 #0 for break, 1 for instruction, 2 for stimulus, 3 for pause
    stimuli, passes = generate_stimuli(N[0], stimuliRange, minHits, maxHits,sequence_length)
    
    N_index = 0
    
    running = True
    index = 0
    score = 0
    pressed = True
    show_stimulus = True
    next_stimulus = False
    show_instruction = True
    show_break = True
    match = False

    clock = pygame.time.Clock()
    timer = 0
    break_duration = 0
    participant_id = input('Enter participant ID: ')
    while running:
        screen.fill(white)
        if break_duration>0:
            if outletDataSent != 0:
                outlet.push_sample('Break: '+str(break_duration/1000))
                outletDataSent = 0
            timer,break_duration = displayBreak(timer,break_duration,clock)
            if break_duration == 0:
                show_break = True
            continue
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if not pressed:
                    if event.key == pygame.K_m and show_stimulus: #press when stimulus match
                        if match:
                            score += 1
                        else:
                            score -= 1
                        inputs.append('m')
                        outlet.push_sample('Pressed: m')
                        pressed = True
                    elif event.key == pygame.K_x and show_stimulus:  #press when stimulus dont match
                        if match:
                            score -= 1
                        else:
                            score +=1
                        inputs.append('x')
                        outlet.push_sample('Pressed: x')
                        pressed = True
                if event.key == pygame.K_RETURN and show_break:
                    show_break = False
                elif event.key == pygame.K_RETURN and show_instruction:
                    show_instruction = False
                    pressed = False
        if show_break:
            stimulus_text = font.render("Break is over press enter when you are ready.", True, black)
            screen.blit(stimulus_text, (screen_width // 2 - stimulus_text.get_width() // 2,
                                    screen_height // 2 - stimulus_text.get_height() // 2))
        elif show_instruction:
            if outletDataSent != 1:
                outlet.push_sample('Instruction: '+str(N[N_index]))
                outletDataSent = 1
            stimulus_text = font.render("{}-back Start".format(N[N_index]), True, black)
            screen.blit(stimulus_text, (screen_width // 2 - stimulus_text.get_width() // 2,
                                    screen_height // 2 - stimulus_text.get_height() // 2))
            
            instructionDescriptionList = ["In this task, you will be shown a sequence of numbers.","If the current number matches the number that was shown N numbers ago, press 'm'.","If the current number does not match the number that was shown N numbers ago, press 'x'."]
            for i,instructionDescription in enumerate(instructionDescriptionList):
                instruction_text = small_font.render(instructionDescription, True, black)
                screen.blit(instruction_text, (screen_width // 2 - instruction_text.get_width() // 2,
                                        3*screen_height//10 - instruction_text.get_height() // 2 + i*instruction_text.get_height()))
            
            pressEnter = "Press Enter to start the task"
            instruction_text = small_font.render(pressEnter, True, black)
            screen.blit(instruction_text, (screen_width // 2 - instruction_text.get_width() // 2,
                                    7*screen_height//10 - instruction_text.get_height() // 2))
            
            pygame.display.flip()

        elif show_stimulus:
            if index >= sequence_length: #current n-back is over
                if len(inputs) == len(stimuli):
                    df = update_df(N[N_index],inputs,passes,stimuli,df)
                    print(sessions)
                    print(df)
                    inputs=[]
                N_index+=1
                index=0
                if N_index == len(N) and sessions!=0: #n-back session is over
                    N_index = 0
                    random.shuffle(N)
                    sessions-=1
                    break_duration = sessionBreak
                elif N_index == len(N) and sessions==0: #game is over
                    running = False
                    save_df(df,participant_id)
                    continue
                else:
                    break_duration = blockBreak
                stimuli, passes = generate_stimuli(N[N_index], stimuliRange, minHits, maxHits,sequence_length)
                show_instruction = True
                
            if outletDataSent != 2:
                outlet.push_sample('Stimulus: '+str(stimuli[index]))
                outletDataSent = 2
            stimulus_text = font.render(str(stimuli[index]), True, black)
            screen.blit(stimulus_text, (screen_width // 2 - stimulus_text.get_width() // 2,
                                        screen_height // 2 - stimulus_text.get_height() // 2))
            stimulus_text = font.render("{}-back".format(N[N_index]), True, black)
            screen.blit(stimulus_text, (screen_width // 2 - stimulus_text.get_width() // 2,
                                    screen_height//10 - stimulus_text.get_height() // 2))
            display_text = str(timer//1000)+'/'+str(stimulus_duration//1000)
            if not pressed:
                stimulus_text = font.render(display_text, True, black)
            else:
                stimulus_text = font.render(display_text, True, white)
            screen.blit(stimulus_text, (screen_width // 2 - stimulus_text.get_width() // 2,
                                    7*screen_height//10 + stimulus_text.get_height() // 2))
            
            if index in passes:
                match = True
            else:
                match = False

            timer += clock.get_time()

            if timer >= stimulus_duration:
                timer = 0
                show_stimulus = False
                next_stimulus = True
                index += 1
                if not pressed:
                    inputs.append('NA')
                    outlet.push_sample('Pressed: NA')
        
        elif next_stimulus:
            if outletDataSent != 3:
                outlet.push_sample('Pause')
                outletDataSent = 3
            info_text = font.render("+", True, black)
            screen.blit(info_text, (screen_width//2 - info_text.get_width()//2, screen_height // 2 - info_text.get_height() // 2))
            timer += clock.get_time()
            if timer >= stimulus_duration:
                timer = 0
                show_stimulus = True
                next_stimulus = False
                pressed = False
        
        else:
            print('Condition forgotten')
            running = False

        pygame.display.flip()
        clock.tick(60)

    # End game and display score
    screen.fill(white)
    result_text = font.render("Score: {}".format(score), True, green if score >= 0 else red)
    screen.blit(result_text, (screen_width // 2 - result_text.get_width() // 2,
                              screen_height // 2 - result_text.get_height() // 2))
    pygame.display.flip()
    pygame.time.wait(3000)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":

    #params: n-back[1,2,3],min number of hits, max number of hits, shuffle is on, number of sessions, instructionTime, showTime, responseTime
    N = [1,2,3]
    sessions = 2
    stimuliRange = (1,9)
    sequence_length = 10
    minHits = 3
    maxHits = 4
    stimulus_duration = 4500  # milliseconds
    next_stimulus = 500
    sessionBreak = 10000
    blockBreak = 5000

    main(N,sessions-1,stimuliRange,sequence_length, minHits, maxHits, stimulus_duration, next_stimulus, sessionBreak, blockBreak)
