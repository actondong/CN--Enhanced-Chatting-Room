import sys
import socket
import select
import threading
import time
from datetime import datetime
import logging
from collections import defaultdict
RECV_BUFFER = 4096
SOCKET_LIST_READ = []
SOCKET_LIST_WRITE = []
usr_ip = {}
#usr_socket_dict = defaultdict(int)
usr_store_msg =defaultdict(lambda:" ")
usr_pass = {}
usr_blacklist=defaultdict(lambda:[])
sock_ip ={}
usr_timeoflastsig=defaultdict(lambda:" ")
heartbeat_lock = threading.Lock()
class myThread (threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
    def run(self):
        print "Starting " + self.name
        while 1:
            cur_timestamp = datetime.now()
            heartbeat_lock.acquire(1)
            for u,t in usr_timeoflastsig.items():
                  print u
                  print t
                  t_datetime_obj = datetime.strptime(t,"%Y-%m-%d%H:%M:%S")
                  if (cur_timestamp - t_datetime_obj).total_seconds() > 30:                   
                        del usr_ip[u]
                        print "remove "+u
                        del usr_timeoflastsig[u]
                        print "usr logout by heartbeat"
                        broadcast(u+" logout\n")
            heartbeat_lock.release()
            time.sleep(30)#every 30 secs, checkout thru usr_timeoflastsig

def server():
      with open('credentials.txt') as inputfile:
            for line in inputfile:
                  usr_pass_list = line.split()
                  key=usr_pass_list[0]
                  value=usr_pass_list[1]
                  print key
                  print value
                  usr_pass[key] = value

      s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      print socket.gethostname()
      s_sock.bind((socket.gethostname(), 5566))
#become a server socket
      s_sock.listen(5)
      SOCKET_LIST_READ.append(s_sock)
      heartbeat_t = myThread("heartbeat")
      heartbeat_t.setDaemon(True)
      heartbeat_t.start()
      while 1:
            ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST_READ,SOCKET_LIST_WRITE,[],0)
            for sock in ready_to_read:
                  if sock == s_sock:
                        print "new clnt connecting"
      			sockfd, addr = s_sock.accept()
                        sock_ip[sockfd] = addr[0]
      			#keep record of sockfd for each addr
      			SOCKET_LIST_READ.append(sockfd)
      			#SOCKET_LIST_WRITE.append(sockfd)
                        print "Client (%s, %s) connected" % addr
                  else:
                        try:  
      			#receiving from clnt socket
                              recv_buff = sock.recv(RECV_BUFFER)
                              addr = sock_ip[sock]
                              print addr
                              if recv_buff:
                                    sys.stdout.write(recv_buff+"\n")
                                    sys.stdout.flush()
      			#process the protocal
                                    recv_list = recv_buff.split(" ")
                                    print recv_list
                        #heartbeat
                                    if recv_list[1] == "heartbeat":
                                          usrName = recv_list[0]
                                          timeoflastsig = recv_list[2]
                                          heartbeat_lock.acquire(1)
                                          usr_timeoflastsig[usrName] = timeoflastsig
                                          heartbeat_lock.release()
                        #login            
                                    if recv_list[0] == "logIn":
                                          usrName = recv_list[1]
                                          print usrName
                                          passWord = recv_list[2]
                                          print passWord
                                          if usrName in usr_pass:
                                                print "usr exist"
                                                if passWord == usr_pass[usrName]:
                                                      usr_ip[usrName] = addr     
                                                      sock.send("Ok")    
                                                      time.sleep(1)         
                                                      login_broad = ">>>"+usrName+"<<<" + "logs in\n"
                                                      broadcast(login_broad,addr)
                                                      store_msg = usr_store_msg[usrName]
                                                      sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                      sock_to_send.connect((addr,6655))
                                                      sock_to_send.send(store_msg)                 
                                                else:
                                                      sock.send("wrong password")
                                          else: 
                                                sock.send("usr not exist")
                        #logout                 
                                    if recv_list[1] == "logout":
                                          usrName=recv_list[0]
                                          print usrName+"log out"
                                          logout_broad = ">>>"+usrName+"<<<" + "logs out\n"
                                          del usr_ip[usrName]
                                          heartbeat_lock.acquire(1)
                                          try:
                                                del usr_timeoflastsig[usrName]
                                          except:
                                                print "fail to del usr_timeoflastsig"
                                          heartbeat_lock.release()
                                          broadcast(logout_broad,addr)
                        #block sb
                                    if recv_list[1] == "block":
                                          if recv_list[2] in usr_ip:
                                                block_usr = recv_list[2]
                                                op_usr = recv_list[0]
                                                usr_blacklist[op_usr].append(block_usr)
                                                sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                sock_to_send.connect((addr,6655))
                                                sock_to_send.send(block_usr+" is Blocked Successfully\n")
                                          else:
                                                sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                sock_to_send.connect((addr,6655))
                                                sock_to_send.send("\nblock_usr doesn't exist\n")
                        #list online users
                                    if recv_list[1] == "online":
                                          print "list usr online"
                                          try:
                                                sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                sock_to_send.connect((addr,6655))
                                                usrName = recv_list[0]
                                          #sock_to_send = usr_socket_dict[usrName]
                                                msg = "\n"
                                                for u,p in usr_ip.items(): 
                                                      u+="\n"
                                                      msg+=u
                                                sock_to_send.send(msg)

                                          except:
                                                print "online fail"
      			#send msg to another clnt 
                                    if recv_list[1] == "message":
                                          print "msg deliver"
                                          print recv_list
                                          usrName = recv_list[0]
                                          sendTo = recv_list[2]
                                          msg = recv_list[3]
                                          if sendTo in usr_pass:
                                                if usrName not in usr_blacklist[sendTo]:
                                                      if sendTo in usr_ip:
                                                            try:
                                                                  addr_msg = usr_ip[sendTo]
                                                                  sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                                  sock_to_send.connect((addr_msg,6655))
                                                                  sock_to_send.send("\n"+usrName + ":"+msg+"\n")
                                                            except:
                                                                  usr_store_msg[sendTo]+= "\n"+usrName+"said:"+msg+"\n"
                                                      else:
                                                      #store msg
                                                            usr_store_msg[sendTo]+= "\n"+usrName+"said:"+msg+"\n"
      			                        else:   

                                                      sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                      sock_to_send.connect((addr,6655))
                                                      sock_to_send.send("\nyou are blocked by this user, sending failed\n")
                                          else:
                                                sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                sock_to_send.connect((addr,6655))
                                                sock_to_send.send("\nusr doesn't exist\n")
                        #broadcast           
                                    if recv_list[1] == "broadcast":
                                          print "in broadcast mode"
                                          print usr_ip.items()
                                          msg = recv_list[2]
                                          broadcast(msg,addr)
                                    SOCKET_LIST_READ.remove(sock)
                                    sock.close()
                              else:
      				# 0 data received from clnt sock
                              	if sock in SOCKET_LIST_READ:
      			         		SOCKET_LIST_READ.remove(sock)
      			except:
                              print "in except"
                              continue

def broadcast (message,self_addr=None):
      print "broadcast()"
      if len(usr_ip.items()) > 0:
            for usr in usr_ip:
                  addr_msg= usr_ip[usr]
                  print addr_msg
                  sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                  if addr_msg != self_addr :
                        sock_to_send.connect((addr_msg,6655))
                        try :
                              sock_to_send.send(message)
                        except :
                              print"fail in broadcast()"
      else:
            print "no usr left..."

if __name__ == "__main__":
	server()

