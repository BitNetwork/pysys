import sys
import os
import shutil
import time

width = 80
height = 20
cd = os.getcwd()
display = []

def updateSize():
  size = shutil.get_terminal_size((80, 20))
  global width, height
  width, height = size[0], size[1]

def clear():
  print(chr(27) + "[2J")

def redraw():
  global display
  updateSize()
  clear()
  display = []
  for index in range(height):
    display.append([])
    for index2 in range(width):
      display[index].append(" ")
  for line in display:
    print("".join(line))
  #print(display)

while 1:
  redraw()
  time.sleep(2)
