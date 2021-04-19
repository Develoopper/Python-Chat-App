import socket
import threading
import datetime
import json

# list of connected users [{'nickname', 'socket'}]
connectedUsers = []


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

def handleMsgs(userSocket):
  # recieve nickname
  nickname = userSocket.recv(1024).decode('utf8')

  # send greetings
  msgToSend = newMsg(
    msg='Welcome ' + nickname, 
    sender='Notification',
    # datetime=''
  )
  userSocket.send(json.dumps(msgToSend).encode('utf8'))
  userSocket.recv(1024)

  # add user to the connected users list
  user = {
    'nickname': nickname,
    'socket': userSocket
  }
  connectedUsers.append(user)

  # notify everyone except the connected user that he has joined
  broadcast(newMsg(
    msg=nickname + ' has joined the chat', 
    sender='Notification',
    exceptUser=nickname
  ))
  
  # send to everyone how many users are connected
  connectedUsersNicknames = ', '.join([user['nickname'] for user in connectedUsers])
  msg = str(len(connectedUsers)) + ' users connected: ' + connectedUsersNicknames
  broadcast(newMsg(
    msg=msg,
    sender='Notification',
  ))

  while True:
    try:
      # recieve message
      msg = json.loads(userSocket.recv(1024).decode('utf8'))
      
      msg['sender'] = nickname
      if msg['msg'] == '#exit':
        # disconnect user if he types '#exit'
        userSocket.close()
        connectedUsers.remove(user)
        # notify everyone that the user has left
        msg['sender'] = 'Notification'
        msg['msg'] = nickname + ' has left the chat'
      
      # broadcast message
      broadcast(msg)
    except socket.error as msg:
      break

def logMsg(msg):
    msgToLog = '\n' + msg['datetime'] + '\n'
    msgToLog += msg['sender']
    msgToLog += ' tagged ' if len(msg['taggedNicknames']) else ''
    msgToLog += ', '.join(msg['taggedNicknames'])
    msgToLog += '> ' + msg['msg']
    print('\n' + msgToLog)

def broadcast(msg):
  for user in connectedUsers:
    # broadcast the message with users exceptions
    if user['nickname'] != msg['exceptUser']:
      user['socket'].send(json.dumps(msg).encode('utf8'))
  logMsg(msg)



try:
  # run the server
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.bind(('127.0.0.1', 9999))
  server.listen()
  print('Server is running...')

  while True:
    # accept incoming connections
    userSocket, address = server.accept()
    print('\n' + 'Connected to ' +  str(address))

    # run a thread for recieving and broadcasting messages
    thread = threading.Thread(target=handleMsgs, args=(userSocket,))
    thread.daemon = True
    thread.start()
except socket.error as msg:
  print('Error :' + str(msg))