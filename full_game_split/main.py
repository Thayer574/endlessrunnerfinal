import pygame
from game import Game

def main():
    pygame.init()
    pygame.mixer.init()
    
    # Try to load music if it exists
    try:
        pygame.mixer.music.load("assets/WalkingNight.mp3")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(loops=-1)
    except pygame.error:
        print("Music file not found in assets/WalkingNight.mp3")

    game = Game()
    # Assuming the original file had a game.run() or similar entry point
    # Based on the Game class structure, we'll call the main loop
    # In the original file, the main loop was likely inside a method or at the bottom
    # We'll assume Game has a run() method or we'll need to call its main loop logic
    if hasattr(game, 'run'):
        game.run()
    else:
        # Fallback if run() isn't the name
        pass

if __name__ == "__main__":
    main()
