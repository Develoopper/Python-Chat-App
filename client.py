import socket
import threading
import datetime
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

# python -u "c:\Users\MyPC\Desktop\Python chat app\client.py"

nickname = ''
conversation = []
connectedUsersNicknames = []

def datetimeNow():
  return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  
def newMsg(datetime=datetimeNow(), msg='', sender='', taggedNicknames=[], exceptUser=''):
  return {
    'datetime': datetime,
    'msg': msg,
    'sender': sender,
    'taggedNicknames': taggedNicknames,
    'exceptUser': exceptUser
  }

def prettify(root):
  return minidom.parseString(root).toprettyxml(indent='\t')

def sendMsgs(s):
  while True:
    # input non empty messages
    msg = ''
    while msg == '':
      msg = input().strip()
      print()

    # export conversation to XML file if the user types '#export'
    if msg == '#export':
      exportConversation()
      continue

    # store the tagged users in taggedNicknames list
    taggedNicknames = []
    for word in msg.split(' '):
      if word[0] == '@' and len(word) > 1:
        taggedNicknames.append(word[1:])
    
    # send message
    msgToSend = newMsg(
      msg=msg,
      taggedNicknames=taggedNicknames,
      sender=nickname
    )
    s.send(json.dumps(msgToSend).encode('utf8'))

    # exit application if the user types '#exit'
    if msg == '#exit':
      exit()
    
def exportConversation():
  messages = ET.Element('messages')

  for msg in conversation:
    newMsg = ET.SubElement(messages, 'message')

    for key, val in msg.items():
      attr = ET.SubElement(newMsg, key)
      if key == 'taggedNicknames':
        for nickname in msg['taggedNicknames']:
          _nickname = ET.SubElement(attr, 'nickname')
          _nickname.text = nickname
      else:
        attr.text = msg[key]

  stringifiedXML = ET.tostring(messages, 'utf-8')
  prettifiedXML = prettify(stringifiedXML)
  with open("messages.xml", "w") as xml:
    xml.write(prettifiedXML)
  print(datetimeNow())
  print("Notification> Conversation exported to 'messages.xml'\n")

def logMsg(msg):
  # add the message to the conversation history
  conversation.append(msg)

  msgToLog = msg['datetime'] + '\n'
  msgToLog += msg['sender']
  msgToLog += ' tagged ' if len(msg['taggedNicknames']) else ''
  # replace in the tag the nickname of the user with 'you'
  _ = ['you' if nickname == _nickname else _nickname for _nickname in msg['taggedNicknames']]
  # let 'you' tag be the first
  try:
    _.insert(0, _.pop(_.index('you')))
  except:
    pass
  msgToLog += ', '.join(_)
  msgToLog += '> ' + msg['msg']
  print(msgToLog + '\n')

def printMsgs(logMsg, s):
  logMsg(json.loads(s.recv(1024).decode('utf8')))
  s.send('handshake'.encode('utf8'))
  
  # the main thread prints the recieved messages
  while True:
    logMsg(json.loads(s.recv(1024).decode('utf8')))



try:
  # connect to the server
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  conn = s.connect(('127.0.0.1', 9999))

  # input and send nickname to the server
  nickname = input("> Nickname: ")
  s.send(nickname.encode('utf8'))
  print()

  # run a thread for print messages
  thread = threading.Thread(target = printMsgs, args = (logMsg, s,))
  thread.daemon = True
  thread.start()

  # the main thread inputs and sends messages
  sendMsgs(s)

except socket.error as msg:
  print('Error :' + str(msg))
  s.close()

# python -u "c:\Users\MyPC\Desktop\Python chat app\client.py"