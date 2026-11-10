"""
Sound Engine Module
Generates and manages procedural audio for game feedback
"""
import array
import math
import random

try:
    import pygame
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


class SoundEngine:
    """Manages all game audio with procedurally generated sounds"""
    
    def __init__(self):
        self.enabled = AUDIO_AVAILABLE
        if self.enabled:
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
                self.click_sound = self._gen_click()
                self.error_sound = self._gen_error()
                self.levelup_sound = self._gen_levelup()
                self.gameover_sound = self._gen_gameover()
                self.achievement_sound = self._gen_achievement()
                self.combo_sound = self._gen_combo()
                self.powerup_sound = self._gen_powerup()
            except Exception as e:
                print(f"Audio initialization failed: {e}")
                self.enabled = False

    def _gen_click(self):
        """Generate a satisfying click sound for correct keystrokes"""
        buffer = array.array('h', [
            int(random.uniform(-1, 1) * 32000 * math.exp(-15 * i / 2205)) 
            for i in range(2205)
        ])
        return pygame.mixer.Sound(buffer)

    def _gen_error(self):
        """Generate an error buzz sound"""
        buffer = array.array('h', [
            int(math.sin(2 * math.pi * 150 * (i/44100)) * 20000 * math.exp(-10 * (i/44100))) 
            for i in range(6615)
        ])
        return pygame.mixer.Sound(buffer)
    
    def _gen_levelup(self):
        """Generate an ascending victory sound"""
        buffer = array.array('h')
        for note in [440, 554, 659, 880]:
            for i in range(3500):
                t = i / 44100
                buffer.append(int((2 * abs(2 * (note * t - math.floor(note * t + 0.5))) - 1) * 10000))
        return pygame.mixer.Sound(buffer)

    def _gen_gameover(self):
        """Generate a descending defeat sound"""
        buffer = array.array('h')
        for i in range(22000):
            t = i / 44100
            freq = 200 - (150 * t)
            val = int((random.random() * 0.5 + 0.5) * math.sin(2 * math.pi * freq * t) * 20000)
            buffer.append(val)
        return pygame.mixer.Sound(buffer)

    def _gen_achievement(self):
        """Generate a triumphant achievement sound"""
        buffer = array.array('h')
        notes = [523, 659, 784, 1047]  # C, E, G, C (major chord)
        for note in notes:
            for i in range(4000):
                t = i / 44100
                val = int(math.sin(2 * math.pi * note * t) * 15000 * math.exp(-3 * t))
                buffer.append(val)
        return pygame.mixer.Sound(buffer)

    def _gen_combo(self):
        """Generate a quick combo hit sound"""
        buffer = array.array('h')
        for i in range(2000):
            t = i / 44100
            freq = 800 + (400 * t)
            val = int(math.sin(2 * math.pi * freq * t) * 18000 * math.exp(-8 * t))
            buffer.append(val)
        return pygame.mixer.Sound(buffer)

    def _gen_powerup(self):
        """Generate a power-up activation sound"""
        buffer = array.array('h')
        for i in range(8000):
            t = i / 44100
            freq = 300 + (600 * t)
            val = int(math.sin(2 * math.pi * freq * t) * 12000 * math.exp(-2 * t))
            buffer.append(val)
        return pygame.mixer.Sound(buffer)

    def play_click(self):
        """Play keystroke sound"""
        if self.enabled:
            self.click_sound.play()
    
    def play_error(self):
        """Play error sound"""
        if self.enabled:
            self.error_sound.play()
    
    def play_levelup(self):
        """Play level up sound"""
        if self.enabled:
            self.levelup_sound.play()
    
    def play_gameover(self):
        """Play game over sound"""
        if self.enabled:
            self.gameover_sound.play()
    
    def play_achievement(self):
        """Play achievement unlock sound"""
        if self.enabled:
            self.achievement_sound.play()
    
    def play_combo(self):
        """Play combo sound"""
        if self.enabled:
            self.combo_sound.play()
    
    def play_powerup(self):
        """Play power-up sound"""
        if self.enabled:
            self.powerup_sound.play()