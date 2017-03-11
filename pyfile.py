import sys
import os
import tty
import termios
import shutil
import time
import signal
import math
import subprocess
from operator import eq
import stat

width = 80
height = 20
terminalConfig = None
cd = sys.argv[1] if len(sys.argv) >= 2 else os.getcwd()
display = []
paint = []
columnLength = 20
selected = 0
keypressCache = []
files = []

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

def top():
  #time.sleep(2)
  # sys.stdout.write("\r" + chr(27) + "[H") # This wasn't working
  sys.stdout.write("\r" + (chr(27) + "[A") * height) # Press the up key height times
  #time.sleep(2)
  # sys.stdout.write((((" " * width) + "\r\n") * height)[:-2]) # No need to clear the stdout... the display is already empty and does that
  # sys.stdout.write("\r" + chr(27) + "[H")

def flushPaint():
  global paint
  updateSize()
  paint = []
  for index1d in range(height):
    paint.append([])
    for index2d in range(width):
      paint[index1d].append(" ")

def flushDisplay():
  global display
  updateSize()
  display = []
  for index1d in range(height):
    display.append([])
    for index2d in range(width):
      display[index1d].append(" ")

def updateDisplay():
  global display, paint
  top()
  for line in range(len(paint)):
    if paint[line] != display[line]:
      for char in range(len(paint[line])):
        updated = False
        if paint[line][char] != display[line][char]:
          sys.stdout.write(paint[line][char])
          display[line][char] = paint[line][char]
          updated = True
        if char == len(paint[line]) - 1: # Last char in line, need a newline for next row
          if line != len(paint) - 1:
            sys.stdout.write(paint[line][char] + "\r\n\r")
          else: # Last line in display, no new line, don't forget to flush
            sys.stdout.write(paint[line][char])
            sys.stdout.flush()
        elif not updated:
          sys.stdout.write(chr(27) + "[C") # Move caret ahead
    else:
      sys.stdout.write(chr(27) + "[B") # Move caret down

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

def prompt(text, placeholder, charset, promptColor, inputColor, bgColor):
  global paint, height, width
  draw(paint, " " * width, [-1, 0], 0) # Clear the status bar
  if len(text) >= width - 10:
    text = text[:width - 13] + ".."
  draw(paint, text, [-1, 1], 0)
  
  inputText = placeholder
  position = len(placeholder) - 1
  keypressPromptCache = []
  charset = list(charset)
  
  while True:
    draw(paint, inputText[:position + 1] + "<" + inputText[position + 2:] + "|", [-1, 3 + len(text)], 0)
    rgbColorTile(paint, [-1, 1], [-1, 1 + len(text)], promptColor, bgColor) # Paint the prompt text
    rgbColorTile(paint, [-1, 0], [-1, -1], inputColor, bgColor) # Paint the status bar
    redraw(False, True)
    key = ord(sys.stdin.read(1))
    keypressPromptCache.append(key)
    keypressPromptCache = keypressPromptCache[-5:]
    if key == 127: # Backspace
      if len(inputText) > 0:
        inputText = inputText[:position] + inputText[position + 1:]
        position -= 1
        draw(paint, " " * (width - len(text) - 4), [-1, 3 + len(text)], 0) # Clear the input
    elif key == 10: # Enter
      return inputText
    elif key == 27: # Escape
      status("Press escape again to cancel.", promptColor, bgColor)
      key = ord(sys.stdin.read(1))
      keypressPromptCache.append(key)
      keypressPromptCache = keypressPromptCache[-5:]
      if key == 27:
        return None
      else:
        draw(paint, " " * width, [-1, 0], 0)
        draw(paint, text, [-1, 1], 0)
    elif keypressPromptCache[-3:] == [27, 91, 68]: # Left arrow key
      if position > 0:
        position -= 1
        draw(paint, " " * (width - len(text) - 4), [-1, 3 + len(text)], 0) # Clear the input
    elif keypressPromptCache[-3:] == [27, 91, 67]: # Right arrow key
      if len(inputText) > position:
        position += 1
    elif len(keypressPromptCache) < 2 or keypressPromptCache[-2] != 27:
      for char in charset:
        if char == chr(key):
          inputText = inputText[:position + 1] + chr(key) + inputText[position + 1:]
          position += 1
          break

def status(text, color, bgColor):
  global width, paint
  draw(paint, " " * width, [-1, 0], 0) # Clear the status bar
  if len(text) >= width - 10:
    text = text[:width - 2] + ".."
  draw(paint, text, [-1, 1], 0)
  rgbColorTile(paint, [-1, 0], [-1, -1], color, bgColor)
  flushDisplay()
  updateDisplay()

def redraw(checkInput, smart):
  global display, width, height, keypressCache, files, selected
  if checkInput == True:
    key = ord(sys.stdin.read(1))
    keypressCache.append(key)
    keypressCache = keypressCache[-5:]
    draw(paint, str(keypressCache), [0, 0], 0)
    if keyHandle(key) == False:
      return
    
  if smart == True:
    # begin smart draw code #
    size = str(height) + " x " + str(width) # Terminal size
    draw(paint, size, [-2, -1 - len(size)], 0)
    
    files = os.listdir(cd)
    for file in range(len(files)):
      column = math.floor(file / (height - 3))
      row = file - (column * (height - 3))
      filename = files[file]
      if len(filename) >= columnLength:
        filename = filename[:columnLength - 3] + ".."
      draw(paint, filename, [1 + row, 1 + column * columnLength], 0)
      if file == selected:
        rgbColorTile(paint, [1 + row, 1 + column * columnLength], [2 + row, column * columnLength + len(filename) + 1], [0x10, 0x10, 0x10], [0xA0, 0xA0, 0xA0])
      else:
        rgbColorTile(paint, [1 + row, 1 + column * columnLength], [2 + row, column * columnLength + len(filename) + 1], [0xA0, 0xA0, 0xA0], [0x10, 0x10, 0x10])
        # end smart draw code #
  else:
    # begin draw code #
    
    # for line in range(len(display)): # Line numbers
      # draw(display, str(line), [line, 0], 0)
  
    size = str(height) + " x " + str(width) # Terminal size
    draw(paint, size, [-2, -1 - len(size)], 0)
    
    files = os.listdir(cd)
    for file in range(len(files)):
      column = math.floor(file / (height - 3))
      row = file - (column * (height - 3))
      filename = files[file]
      if len(filename) >= columnLength:
        filename = filename[:columnLength - 3] + ".."
      draw(paint, filename, [1 + row, 1 + column * columnLength], 0)
      if file == selected:
        rgbColorTile(paint, [1 + row, 1 + column * columnLength], [2 + row, column * columnLength + len(filename) + 1], [0x10, 0x10, 0x10], [0xA0, 0xA0, 0xA0])
    
    # colors
    # rgbColorTile(paint, [0, -21], [-1, -20], [0x80, 0x80, 0x80], [0x5, 0x5, 0x5])
    rgbColorTile(paint, [0, 0], [-2, -1], [0xA0, 0xA0, 0xA0], [0x10, 0x10, 0x10]) # Paint everything c#101010 bgc#A0A0A0
    rgbColorTile(paint, [-2, 0], [-1, -1], [0x10, 0x10, 0x10], [0xA0, 0xA0, 0xA0]) # Paint the status bar
    # end draw code #
  
  updateDisplay()

def keyHandle(key): # 27 91 66 - 27 91 65
  global keypressCache, selected, paint, files, selected, cd
  if keypressCache[-3:] == [27, 91, 66]: # down key
    selected += 1
  elif keypressCache[-3:] == [27, 91, 65]: # up key
    selected -= 1
  elif key == 127: # Backspace
    cd += "/.."
    selected = 0
    flushPaint()
    redraw(False, False)
  elif keypressCache[-4:] == [27, 91, 51, 126]: # Delete key
    response = prompt("Delete file?", "y", "ynYN", [0xA0, 0xA0, 0xA0], [0x60, 0x60, 0x60], [0xff, 0x0, 0x0])
    if response == "y" or response == "Y":
      os.remove(cd + "/" + files[selected])
    flushPaint()
    redraw(False, False)
  elif key == 110: # N key
    filename = prompt("New file name?", "", "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz?!.@#$%%^&*()-_=+[]{};:\"\'|\\,.<>` /", [0x5F, 0x5F, 0x5F], [0x9F, 0x9F, 0x9F], [0x0, 0xff, 0x0])
    if filename is not None and os.path.isfile(cd + "/" + filename):
      status("File already exists.", [0x5F, 0x5F, 0x5F], [0x0, 0xff, 0x0])
      time.sleep(2)
    elif filename is not None:
      file = open(cd + "/" + filename, "w")
      file.write("")
      file.close()
    flushPaint()
    redraw(False, False)
  elif key == 109:
    filename = prompt("Move to?", files[selected], "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz?!.@#$%%^&*()-_=+[]{};:\"\'|\\,.<>` /", [0x5F, 0x5F, 0x5F], [0x9F, 0x9F, 0x9F], [0x0, 0xff, 0x0])
    if filename is not None and os.path.isfile(cd + "/" + filename):
      status("File already exists.", [0x5F, 0x5F, 0x5F], [0x0, 0xff, 0x0])
      time.sleep(2)
    elif filename is not None:
      os.rename(cd + "/" + files[selected], cd + "/" + filename)
    flushPaint()
    redraw(False, False)
  elif key == 114: # R key
    flushPaint()
    flushDisplay()
    redraw(False, False)
  elif key == 10: # Enter key
    target = cd + "/" + files[selected]
    if os.path.isdir(target):
      cd = target
      selected = 0
      flushPaint()
      redraw(False, False)
    elif stat.S_IXUSR & os.stat(target)[stat.ST_MODE]:
      flushPaint()
      updateDisplay()
      resetMode()
      os.system(target)
      sys.stdout.write("Process finished. Press any key to continue...")
      sys.stdout.flush()
      inputMode()
      sys.stdin.read(1)
      redraw(False, False)

def signalHandler(signal, frame):
  exit(0)
  
def exit(code):
  resetMode()
  sys.exit(code)

signal.signal(signal.SIGINT, signalHandler)

inputMode()
flushPaint()
flushDisplay()
redraw(False, False)
while 1:
  redraw(True, True)
