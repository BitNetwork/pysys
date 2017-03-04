import sys
import os
import tty
import termios
import shutil
import time
import signal
import math

width = 80
height = 20
terminalConfig = None
cd = os.getcwd()
display = []
columnLength = 20
selected = 0
keypressCache = []

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
  # Direction: 0: left to right, 1: right to left, 2: down to up, 3: up to down
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

def color(text, color, bgColor, style):
  # See http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python/21786287#21786287, https://i.stack.imgur.com/6otvY.png, https://i.stack.imgur.com/lZr23.png & https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
  # Color: Black: 30, Red: 31, Green: 32, Yellow: 33, Blue: 34, Purple: 35, Cyan: 36, White: 37
  # Background color: Black: 40, Red: 41, Green: 42, Yellow: 43, Blue: 44, Purple: 45, Cyan: 46, White: 47
  # Style: Normal: 0, Bold: 1, Thin: 2, Italic: 3, 4: Underline, 5: Increase brightness, 6: Increase brightness, 7: Inverse color & bgcolor
  return "\x1b[" + str(style) + ";" + str(color) + ";" + str(bgColor) + "m" + text + "\x1b[0m"

def rgbColor(text, color, bgColor):
  return "\x1b[38;2;" + str(color[0]) + ";" + str(color[1]) + ";" + str(color[2]) + ";48;2;" + str(bgColor[0]) + ";" + str(bgColor[1]) + ";" + str(bgColor[2]) + "m" + text + "\x1b[0m"

def rgbColorTile(givenList, start, end, color, bgColor):
  if start[0] < 0:
    start[0] = len(givenList) + start[0]
  if start[1] < 0:
    start[1] = len(givenList[0]) + start[1]
  if end[0] < 0:
    end[0] = len(givenList) + end[0] + 1
  if end[1] < 0:
    end[1] = len(givenList[0]) + end[1]
  for indexY in range(end[0] - start[0]):
    for indexX in range(end[1] - start[1]):
      givenList[start[0] + indexY][start[1] + indexX] = rgbColor(givenList[start[0] + indexY][start[1] + indexX], color, bgColor)

def redraw(checkInput):
  global display, width, height, keypressCache
  flushDisplay()
  if checkInput == True:
    key = ord(sys.stdin.read(1))
    keypressCache.append(key)
    keypressCache = keypressCache[-5:]
    draw(display, str(keypressCache), [6, 90], 0)
    keyHandle(key)
  # begin draw code #
  
  # for line in range(len(display)): # Line numbers
    # draw(display, str(line), [line, 0], 0)

  size = str(height) + " x " + str(width) # Terminal size
  draw(display, size, [-1, -1 - len(size)], 0)
  
  dirList = os.listdir("/bin")
  for file in range(len(dirList)):
    column = math.floor(file / (height - 2))
    row = file - (column * (height - 2))
    filename = dirList[file]
    if len(filename) >= columnLength:
      filename = filename[:columnLength - 3] + ".."
    draw(display, filename, [1 + row, 1 + column * columnLength], 0)
    if file == selected:
      rgbColorTile(display, [1 + row, 1 + column * columnLength], [2 + row, column * columnLength + columnLength], [0x10, 0x10, 0x10], [0xA0, 0xA0, 0xA0])
  
  # colors
  rgbColorTile(display, [0, -21], [-1, -20], [0x80, 0x80, 0x80], [0x5, 0x5, 0x5])
  rgbColorTile(display, [0, 0], [-1, -1], [0xA0, 0xA0, 0xA0], [0x10, 0x10, 0x10]) # Paint everything c#101010 bgc#A0A0A0
  # end draw code #
  updateDisplay()

def keyHandle(key): # 27 91 66 - 27 91 65
  global keypressCache, selected
  draw(display, str(key), [0, 2], 0)
  if keypressCache[-3:] == [27, 91, 66]: # down key
    selected += 1
  elif keypressCache[-3:] == [27, 91, 65]: # up key
    selected -= 1
  # time.sleep(3)

def signalHandler(signal, frame):
  resetMode()
  sys.exit(1)

signal.signal(signal.SIGINT, signalHandler)

inputMode()
redraw(False)
while 1:
  redraw(True)
  # time.sleep(1)
