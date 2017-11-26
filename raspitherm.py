#!/usr/bin/python
# 
# PiEyeR - Raspberry Pi Thermal Camera 
#
# Enhanced version of Adafruit Raspberry Pi Thermal Camera
# Based on Adafruit AMG8833 Grid-Eye module and PiTFT 2.8" screen
#
# Normally run by pi crontab at bootup
# Turn off by commenting out @reboot... using $ crontab -e; sudo reboot
# Manually run using $ sudo python raspitherm.py
#
# Version 0.5 2017.11.26 - initial release
#
# License: GPLv3, see: www.gnu.org/licenses/gpl-3.0.html
#

from Adafruit_AMG88xx import Adafruit_AMG88xx
import pygame
import os
import math
import time
import logging

import numpy as np
from scipy.interpolate import griddata
from pygame.locals import *
from colour import Color

import RPi.GPIO as GPIO


##### VARIABLES
DEBUG	= 0	# Debug 0/1 off/on (writes to debug.log)

# INITIAL TEMPERATURE VALUES
MINTEMP = 26	# Low temp range (blue)
MAXTEMP = 32	# High temp range (red)

COLORDEPTH = 1024	
MARGIN = 20

# GPIO BUTTONS
BTN1	= 17	# Top	
BTN2	= 22	# Second
BTN3	= 23	# Third
BTN4	= 27	# Fourth

# FULL SCREEN COLORS
WHITE = (255,255,255)
BLACK = (0,0,0)
BLUE  = (0,0,255)
YELLOW= (255,255,0)
CYAN  = (255,255,0)
RED   = (255,0,0)

F_WIDTH  = 320
F_HEIGHT = 240

###### FUNCTIONS
def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))

def map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

# Clear Screen
def cleartft(scolor):
    logger.info('cleartft('+str(scolor)+')')
    lcd = pygame.display.set_mode((F_WIDTH, F_HEIGHT))
    lcd.fill(scolor)
    pygame.display.update()

# Display the Mode Screen (Designed for 320x240 screen)
def displayMode():
    logger.info('displayMode()')
    cleartft(BLACK)
    lcd = pygame.display.set_mode((F_WIDTH, F_HEIGHT))

    # Title Screen
    fnt = pygame.font.Font(None, 40)
    txt = fnt.render('PiEyeR Camera',True,CYAN)
    lcd.blit(txt, (10,10))
    pygame.draw.lines(lcd,WHITE,False, [(10,50),(210,50)])

    # Info Box
    pygame.draw.rect(lcd,BLUE,[(10,60),(200,180)])
    pygame.draw.rect(lcd,WHITE,[(10,60),(200,180)],1)
    fnt = pygame.font.Font(None, 15)
    txt = fnt.render('AMG8833 Grid-Eye Thermal Camera',True,YELLOW)
    lcd.blit(txt, (20,70))
    txt = fnt.render('for Raspberry Pi',True,WHITE)
    lcd.blit(txt, (60,90))
    txt = fnt.render('PWR   = Shutdown/Startup',True,CYAN)
    lcd.blit(txt, (30,130))
    txt = fnt.render('UP/DN = Change Sensitivity',True,CYAN)
    lcd.blit(txt, (30,150))
    txt = fnt.render('CAM    = Camera Mode',True,CYAN)
    lcd.blit(txt, (30,170))
    
    # Function Buttons
    font_big = pygame.font.Font(None, 25)
    mode_buttons = {'PWR ->':(280,40), '   UP ->':(280,100), 'DOWN->':(280,160), 'CAM ->':(280,220)}
    for k,v in mode_buttons.items():
        text_surface = font_big.render('%s'%k, True, WHITE)
        rect = text_surface.get_rect(center=v)
        lcd.blit(text_surface, rect)
    pygame.display.update()

# TODO FUTURE FEATURES
def future(msg):
    logger.info('future('+msg+')')
    cleartft(BLUE)
    lcd = pygame.display.set_mode((F_WIDTH, F_HEIGHT))
    font_big = pygame.font.Font(None, 50)
    text_surface = font_big.render('FUTURE', True, WHITE)
    rect = text_surface.get_rect(center=(160,120))
    lcd.blit(text_surface, rect)
    pygame.display.update()
    time.sleep(2)

# IR Thermal Camera
def camera():
    logger.info('camera()')
    lcd = pygame.display.set_mode((width, height))
    lcd.fill(BLUE)
    pygame.display.update()
    time.sleep(0.5)	
    offset = 0
    loop = 1
    while (loop):
	#read the pixels
	pixels = sensor.readPixels()
	pixels = [map(p, MINTEMP+offset, MAXTEMP+offset, 0, COLORDEPTH - 1) for p in pixels]
	
	#perdorm interpolation
	bicubic = griddata(points, pixels, (grid_x, grid_y), method='cubic')
	
	#draw everything
	for ix, row in enumerate(bicubic):
		for jx, pixel in enumerate(row):
			pygame.draw.rect(lcd, colors[constrain(int(pixel), 0, COLORDEPTH- 1)], (displayPixelHeight * ix, displayPixelWidth * jx, displayPixelHeight, displayPixelWidth))
	
	# Flip the screen horizontally to match front facing IP camera
	surf = pygame.transform.flip(lcd,True,False)
	lcd.blit(surf,(0,0))
	pygame.display.update()

	# GPIO Button Press to exit
	if GPIO.input(BTN4) == GPIO.LOW:
		logger.info("stopping camera()")
		loop = 0
		time.sleep(0.5)	
	if GPIO.input(BTN2) == GPIO.LOW:
		logger.info("UP")
		offset = offset - 1
		time.sleep(0.5)	
	if GPIO.input(BTN3) == GPIO.LOW:
		logger.info("DOWN")
		offset = offset + 1
		time.sleep(0.5)	


######
# MAIN
######
# Setup Logging
logger = logging.getLogger()
handler = logging.FileHandler('debug.log')
if DEBUG:
    logger.setLevel(logging.INFO)
    handler.setLevel(logging.INFO)
else:
    logger.setLevel(logging.ERROR)
    handler.setLevel(logging.ERROR)
log_format = '%(asctime)-6s: %(name)s - %(levelname)s - %(message)s'
handler.setFormatter(logging.Formatter(log_format))
logger.addHandler(handler)

logger.info('Starting')

# Setup OS Env
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')


# Setup GPIO buttons
GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

## Thermal Sensor
sensor = Adafruit_AMG88xx()
points = [(math.floor(ix / 8), (ix % 8)) for ix in range(0, 64)]
grid_x, grid_y = np.mgrid[0:7:32j, 0:7:32j]

height = 240
width = 240

# Set Color range
blue = Color("indigo")
colors = list(blue.range_to(Color("red"), COLORDEPTH))

# Create the array of colors
colors = [(int(c.red * 255), int(c.green * 255), int(c.blue * 255)) for c in colors]

displayPixelWidth = width / 30
displayPixelHeight = height / 30


# PYGAME SCREEN
pygame.init()
pygame.mouse.set_visible(False)
cleartft(BLACK)

logger.info('setup complete')

# Display MODE screen
displayMode()

# Wait for sensor initialize
time.sleep(.1)
	
while True:
	# GPIO Button Press to exit
	if GPIO.input(BTN1) == GPIO.LOW:
		cleartft(BLACK)
		time.sleep(5)
		#exit(0)

	if GPIO.input(BTN4) == GPIO.LOW:
		cleartft(BLACK)
		time.sleep(0.1)	
		camera()
		displayMode()
		time.sleep(0.5)	

	if GPIO.input(BTN2) == GPIO.LOW:
                # Btn 2
		future("Btn 2")
		displayMode()
		time.sleep(0.5)	
	
	if GPIO.input(BTN3) == GPIO.LOW:
                # Btn 3
		future("Btn 3")
		displayMode()
		time.sleep(0.5)	
        time.sleep(.1)

### END
