import sys
import os
import tty
import termios
import shutil
import time
import signal

width = 80
height = 20
terminalConfig = None
cd = os.getcwd()
display = []

def inputMode():
  global terminalConfig
  terminalConfig = termios.tcgetattr(sys.stdin)
  tty.setcbreak(sys.stdin)

def resetMode():
  global terminalConfig
  termios.tcsetattr(sys.stdin, termios.TCSADRAIN, terminalConfig)

def updateSize():
  size = shutil.get_terminal_size((80, 20))
  global width, height
  width, height = size[0], size[1]

def clear():
  #time.sleep(2)
  # sys.stdout.write("\r" + chr(27) + "[H")
  sys.stdout.write("\r" + (chr(27) + "[A") * height)
  #time.sleep(2)
  # sys.stdout.write((((" " * width) + "\r\n") * height)[:-2]) # No need to clear the stdout... the display is already empty and does that
  # sys.stdout.write("\r" + chr(27) + "[H")

def flushDisplay():
  global display
  updateSize()
  clear()
  display = []
  for index1d in range(height):
    display.append([])
    for index2d in range(width):
      display[index1d].append(" ")

def updateDisplay():
  global display
  for line in range(len(display)):
    if line != len(display) - 1:
      sys.stdout.write(("".join(display[line]) + "\r\n"))
    else:
      sys.stdout.write("".join(display[line]))
      sys.stdout.flush()

def draw(givenList, text, position, direction):
  if position[0] < 0:
    position[0] = len(givenList) + position[0]
  if position[1] < 0:
    position[1] = len(givenList[0]) + position[1]
  for index in range(len(text)):
    if direction == 0:
      givenList[position[0]][position[1] + index] = text[index]
    elif direction == 1:
      givenList[position[0]][position[1] + len(text) - index] = text[index]
    elif direction == 2:
      givenList[position[0] + index][position[1]] = text[index]
    elif direction == 3:
      givenList[position[0] + len(text) - 1 - index][position[1]] = text[index]
  return givenList

def redraw(checkInput):
  global display, width, height
  flushDisplay()
  # begin draw code #
  
  for line in range(len(display)):
    draw(display, str(line), [line, 0], 0)
    #display[line][0] = str(line)
  size = str(height) + " x " + str(width)
  draw(display, size, [-1, -1 - len(size)], 0)
  # draw(display, "asdf", [-2, -2 + len], 0)
  
  # end draw code #
  if checkInput == True:
    keyHandle(ord(sys.stdin.read(1)))
  updateDisplay()

def keyHandle(key):
  draw(display, str(key), [0, 2], 0)

def signalHandler(signal, frame):
  resetMode()
  sys.exit(1)

signal.signal(signal.SIGINT, signalHandler)

inputMode()
redraw(False)
while 1:
  redraw(True)
  # time.sleep(1)
