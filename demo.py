import pygame
from pylsl import StreamInfo, StreamOutlet
import random
import time

# Initialize Pygame
pygame.init()

# Set up the Pygame window
window_width = 800
window_height = 600
window = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption('LSL with Pygame')

# Create LSL StreamInfo and StreamOutlet
info = StreamInfo('Trigger', 'Data', 1, 1, 'float32', 'my_random_data_stream')
outlet = StreamOutlet(info)

# Fonts for rendering text
font = pygame.font.Font(None, 48)

# Running flag and game loop
running = True
clock = pygame.time.Clock()

while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Generate a random float number
    random_value = random.random()

    # Push the random value to the LSL stream
    outlet.push_sample([random_value])

    # Clear the screen
    window.fill((0, 0, 0))

    # Render text on the screen (display the random value)
    text = font.render(f'Random Value: {random_value:.2f}', True, (255, 255, 255))
    window.blit(text, (window_width // 4, window_height // 2))

    # Update display
    pygame.display.flip()

    # Control the frame rate (30 frames per second)
    clock.tick(30)

    # Sleep for a bit to simulate data collection time
    time.sleep(0.1)

# Quit Pygame
pygame.quit()
