import sys
import socket
import select
import threading
import time
import logging
from collections import defaultdict
RECV_BUFFER = 4096
SOCKET_LIST_READ = []
SOCKET_LIST_WRITE = []
usr_ip = {}
def defactory():
      return " "

def server():
      usr_socket_dict = defaultdict(int)
      usr_store_msg =defaultdict(defactory)
      usr_pass = {}
      sock_ip ={}
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
                                    #broadcast(s_sock,sock,recv_buff)
      			#process the protocal
                                    recv_list = recv_buff.split(" ")
                                    print recv_list
                        #login            
                                    if recv_list[0] == "logIn":
                                          usrName = recv_list[1]
                                          print usrName
                                          passWord = recv_list[2]
                                          print passWord
                                          if usrName in usr_pass:
                                                print "usr exist"
                                                if passWord == usr_pass[usrName]:
                                                      print "passWord pass"
                                                      usr_socket_dict[usrName] = sock
                                                      print"usr_socket_dict pass"
                                                      usr_ip[usrName] = addr     
                                                      sock.send("Ok")    
                                                      time.sleep(1)                                     
                                                      store_msg = usr_store_msg[usrName]
                                                      sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                      sock_to_send.connect((addr,6655))
                                                      sock_to_send.send(store_msg)                 
                                                      print "OK"
                                                else:
                                                      sock.send("wrong password")
                                          else: 
                                                sock.send("usr not exist")
                        #logout                 
                                    if recv_list[1] == "logout":
                                          print "usr logout"
                                          usrName=recv_list[0]
                                          SOCKET_LIST_READ.remove(sock)
                                          sock.close()

                                          
                        #list online users
                                    if recv_list[1] == "online":
                                          print "list usr online"
                                          try:
                                                sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                sock_to_send.connect((addr,6655))
                                                usrName = recv_list[0]
                                          #sock_to_send = usr_socket_dict[usrName]
                                                msg = "\n"
                                                for u,s in usr_socket_dict.items(): 
                                                      u+="\n"
                                                      msg+=u
                                                sock_to_send.send(msg)
                                                SOCKET_LIST_READ.remove(sock)
                                                sock.close()
                                          except:
                                                print "online fail"
      			#send msg to another clnt 
                                    if recv_list[1] == "message":
                                          print "msg deliver"
                                          print recv_list
                                          usrName = recv_list[0]
                                          sendTo = recv_list[2]
                                          msg = recv_list[3]
                                          if sendTo in usr_ip:
                                                print " usr in usr_socket_dict "
                                                try:
                                                      addr_msg = usr_ip[sendTo]
                                                      sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                      sock_to_send.connect((addr_msg,6655))
                                                      sock_to_send.send("\n"+usrName + ":"+msg+"\n")
                                                      SOCKET_LIST_READ.remove(sock)
                                                      sock.close()
                                                except:
                                                      usr_store_msg[sendTo]+= "\n"+usrName+"said:"+msg+"\n"
                                                      SOCKET_LIST_READ.remove(sock)
                                                      sock.close()
                                          else:
                                          #store msg
                                                usr_store_msg[sendTo]+= "\n"+usrName+"said:"+msg+"\n"
                                                SOCKET_LIST_READ.remove(sock)
                                                sock.close()
      			#broadcast
                                    if recv_list[1] == "broadcast":
                                          print "in broadcast mode"
                                          print usr_ip.items()
                                          msg = recv_list[2]
                                          broadcast(s_sock,sock,msg)
                                          SOCKET_LIST_READ.remove(sock)
                                          sock.close()
                              else:
      				# 0 data received from clnt sock
                              	if sock in SOCKET_LIST_READ:
      			         		SOCKET_LIST_READ.remove(sock)
      			except:
      				#recv failed
                              print "in except"
                              continue



def broadcast (server_socket, sock, message):
      print "broadcast()"
      for usr in usr_ip:
            print "in for"
            addr_msg= usr_ip[usr]
            print addr_msg
            sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_to_send.connect((addr_msg,6655))
            if sock_to_send != sock :
                  try :
                        sock_to_send.send(message)
                  except :
                        print"fail in bd()"


if __name__ == "__main__":
	sys.exit(server())

