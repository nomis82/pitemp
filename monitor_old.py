#!/usr/bin/python

# nohup sudo python ~/Adafruit_Nokia_LCD/examples/termometer_2.py  &
# v1.0 display temp on LCD
# v1.1 graph osv
# v2.0 thread
# v2.1 autoscale
# v2.2 sqlite export (timecount) 
import os
import glob
import time
import datetime
#from time import time, sleep, gmtime, strftime
#threading
import thread
#sqlite
import sqlite3

import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# global variables
#Sqlite Database where to store readings
dbname='/var/www/templog.db'

# Raspberry Pi hardware SPI config:
DC = 23
RST = 24
SPI_PORT = 0
SPI_DEVICE = 0

# Hardware SPI usage:
disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))

# Initialize library.
disp.begin(contrast=50)

# Clear display.
disp.clear()
disp.display()

image = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))

font = ImageFont.load_default()
font2 = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', 18)

draw = ImageDraw.Draw(image)

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
     
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

# Temperature history in values (history duration will be samples * refresh)
samples = 60
templist = [3.1] * samples
timecount = 0

# store the temperature in the database
def log_temperature(temp):

    conn=sqlite3.connect(dbname)
    curs=conn.cursor()

    curs.execute("INSERT INTO temps values(datetime('now'), (?))", (temp,))
#    today = datetime.now()
#    print today, temp
    # commit the changes
    conn.commit()

    conn.close()
    

def read_temp_raw():
 f = open(device_file, 'r')
 lines = f.readlines()
 f.close()
 return lines
    
def read_temp():
 lines = read_temp_raw()
 while lines[0].strip()[-3:] != 'YES':
  time.sleep(0.2)
  lines = read_temp_raw()
 equals_pos = lines[1].find('t=')
 if equals_pos != -1:
  temp_string = lines[1][equals_pos+2:]
  temp_float = float(temp_string) / 1000.0
  temp_float = round(temp_float,1)
  temp_c = str(temp_float)
  return temp_c

def temp_list( threadName, delay):
 while True:	
  temp = read_temp()
  temp = float(temp)
  global timecount
  timecount += 1
  for x in range(len(templist)-1):
   templist[x] = templist[x+1]
 # Set the end item to be our current temperature
   templist[len(templist)-1] = temp
  time.sleep(delay)

def draw_screen( threadName, delay):
 while True:	
  temp = read_temp()
  # Store the temperature in the database
  
  log_temperature(temp)
  #***
  draw.rectangle((0,0,LCD.LCDWIDTH,LCD.LCDHEIGHT), outline=255, fill=255)
  temp_max = max(templist)
  temp_min = min(templist)
  temp_mid = int(round(temp_max-((temp_max-temp_min)/2),0)) 
  #autoscale
  if temp_max-temp_min < 4:
   scale = 20/4
   scale_max = temp_mid+2
   scale_min = temp_mid-2
  elif temp_max-temp_min < 8:
   scale = 20/8
   scale_max = temp_mid+4
   scale_min = temp_mid-4
  else:
   scale = 20/16
   scale_max = temp_mid+8
   scale_min = temp_mid-8 
  # temp graph
  for x in range(len(templist)-1):
   yadd = (templist[x]-temp_mid)*scale
   y = 15 - round(yadd, 0)
   draw.line((x,y+1,x,y-1), fill=0)
  # scale degree
  draw.text((65,0), str(scale_max), font=font) 
  draw.text((65,10), str(temp_mid), font=font) 
  draw.text((65,20), str(scale_min), font=font)
  draw.line((60,5,63,5), fill=0) 
  draw.line((60,10,63,10), fill=0) 
  draw.line((60,15,63,15), fill=0) 
  draw.line((60,20,63,20), fill=0) 
  draw.line((60,25,63,25), fill=0) 
  # scale time
  for x in range(10):
   draw.line((x*6,0,x*6,2), fill=0) 
  #max min temp 
  draw.text((40,30), 'max', font=font) 
  draw.text((60,30), str(max(templist)), font=font) 
  draw.text((40,39), 'min', font=font)
  draw.text((60,39), str(min(templist)), font=font)
  #actual temp
  draw.text((1,30), temp, font=font2)
  # timecount
  draw.text((50,23), str(timecount), font=font)
  #draw display
  disp.image(image)
  disp.display()
  #print(templist)
  print(yadd)
  print(y) 
  print(temp)
  time.sleep(delay)
 
try:
 thread.start_new_thread(draw_screen, ("Thread-1", 15, ))
 thread.start_new_thread(temp_list, ("Thread-2", 600, ))
except:
   print "Error: unable to start thread"

while True:
 time.sleep(0.01)
 pass
