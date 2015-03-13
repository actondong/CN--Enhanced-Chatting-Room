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
usr_ip = {}#store ip for each login usr 
usr_port = {}#store listen port on each clnt 
usr_store_msg =defaultdict(lambda:" ")
usr_pass = {}
usr_blacklist=defaultdict(lambda:[])
sock_ip ={}
usr_timeoflastsig=defaultdict(lambda:" ")#record time when last heartbeat received
heartbeat_lock = threading.Lock()
login_lock=defaultdict(lambda:" ")#lock usr if three login failure in a row
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
                  t_datetime_obj = datetime.strptime(t,"%Y-%m-%d%H:%M:%S")
                  if (cur_timestamp - t_datetime_obj).total_seconds() > 5:                   
                        # del usr_ip[u] should also be protected by a lock. 
                        try:
                              del usr_ip[u]
                              print "remove "+u
                              del usr_timeoflastsig[u]
                              print "usr logout by heartbeat"
                              broadcast(u+" logout\n")
                        except:
                              print "fail to logout usr thru heartbeat\n"
            heartbeat_lock.release()
            time.sleep(5)#every 5 secs, checkout thru usr_timeoflastsig

class myThread2 (threading.Thread):#This thread for P2P consent and privacy
      def __init__(self, name, usrName, peerName, peer_addr,peer_port, usr_ip,usr_port):
            threading.Thread.__init__(self)
            self.name = name
            self.usrName = usrName
            self.peerName = peerName
            self.addr = usr_ip#the ip of who initialize the request of getaddress
            self.clnt_port_l = usr_port
            self.peer_addr = peer_addr
            self.peer_port = peer_port
      def run(self):
            print "Starting " + self.name
            peer_sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_sock_to_send.connect((self.peer_addr,self.peer_port))#the sock connecting usr who initialize the getaddress request
            usr_sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            usr_sock_to_send.connect((self.addr,self.clnt_port_l))#the sock connecting peer
            msg = "Privacy"+" "+self.usrName + " wants to get your IP for P2P chat. Type Y/y if agree, type N/n otherwise\n"#protocal is Privacy
            peer_sock_to_send.send(msg)
            feedback = peer_sock_to_send.recv(4096)#blcok for receiving
            feedback = feedback.strip()
            feedback = feedback.upper()
            peer_sock_to_send.close()#This one is closed on initialization side only
            if feedback == 'Y':
                  msg = "usrIp " + self.peerName + " " + self.peer_addr + " " + str(self.peer_port)
                  usr_sock_to_send.send(msg)
            else:
                  msg = "\nYour request is rejected\n"
                  usr_sock_to_send.send(msg)
            print "Ending "+self.name
            return 0

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
      			sockfd, addr = s_sock.accept()
                        sock_ip[sockfd] = addr[0]
      			#keep record of sockfd for each addr. Later this will help get ip for usr to put into usr_ip
      			SOCKET_LIST_READ.append(sockfd)
                        print "Client (%s, %s) connected" % addr
                  else:
                        try:  
      			#receiving from clnt socket
                              recv_buff = sock.recv(RECV_BUFFER)
                              addr = sock_ip[sock]
                              # For surpervision purpose
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
                                          clnt_port_l = int(recv_list[3])
                                          print clnt_port_l
                                          sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                          sock_to_send.connect((addr,clnt_port_l))
                                          if usrName in usr_pass:#usr exists
                                                if usrName not in login_lock:#usr not locked
                                                      if usrName not in usr_ip:#usr not already login
                                                            print "usr exist and not login\n"
                                                            if passWord == usr_pass[usrName]:
                                                                  usr_ip[usrName] = addr   
                                                                  usr_port[usrName] = clnt_port_l
                                                                  sock_to_send.send("Ok")        
                                                                  login_broad = ">>>"+usrName+"<<<" + "logs in\n"
                                                                  broadcast(login_broad,addr,usr_port)
                                                                  store_msg = usr_store_msg[usrName]#check offline msg
                                                                  sock_to_send.send(store_msg)    
                                                            else:
                                                                  sock_to_send.send("wrong password")          
                                                      else:#already login
                                                            pre_usr_ip = usr_ip[usrName]#previous user ip
                                                            pre_usr_port = usr_port[usrName]#previous usr port
                                                            sock_to_pre= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                            sock_to_pre.connect((pre_usr_ip,pre_usr_port))
                                                            msg = "logout" + " " +addr#logout previous usr and notice him new login ip
                                                            sock_to_pre.send(msg) 
                                                            usr_ip[usrName] = addr
                                                            usr_port[usrName] = clnt_port_l#record new usr
                                                            sock_to_send.send("Ok")            
                                                            login_broad = ">>>"+usrName+"<<<" + "logs in\n"
                                                            broadcast(login_broad,addr,usr_port)
                                                            store_msg = usr_store_msg[usrName]#check offline msg
                                                            sock_to_send.send(store_msg)   
                                          
                                                else:#usr locked
                                                      cur_timestamp = datetime.now()
                                                      t = login_lock[usrName]
                                                      t_datetime_obj = datetime.strptime(t,"%Y-%m-%d%H:%M:%S")#form string to date obj.
                                                      if (cur_timestamp - t_datetime_obj).total_seconds() > 30:
                                                            if usrName not in usr_ip:#not already login
                                                                  print "usr exist and not login\n"
                                                                  if passWord == usr_pass[usrName]:
                                                                        usr_ip[usrName] = addr   
                                                                        usr_port[usrName] = clnt_port_l
                                                                        sock_to_send.send("Ok")        
                                                                        login_broad = ">>>"+usrName+"<<<" + "logs in\n"
                                                                        broadcast(login_broad,addr,usr_port)
                                                                        store_msg = usr_store_msg[usrName]#check offline msg
                                                                        sock_to_send.send(store_msg)    
                                                                  else:
                                                                        sock_to_send.send("wrong password")          
                                                            else:#already login
                                                                  pre_usr_ip = usr_ip[usrName]#previous user ip
                                                                  pre_usr_port = usr_port[usrName]#previous usr port
                                                                  sock_to_pre= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                                  sock_to_pre.connect((pre_usr_ip,pre_usr_port))
                                                                  msg = "logout" + " " +addr#logout previous usr and notice him new login ip
                                                                  sock_to_pre.send(msg) 
                                                                  usr_ip[usrName] = addr
                                                                  usr_port[usrName] = clnt_port_l#record new usr
                                                                  sock_to_send.send("Ok")            
                                                                  login_broad = ">>>"+usrName+"<<<" + "logs in\n"
                                                                  broadcast(login_broad,addr,usr_port)
                                                                  store_msg = usr_store_msg[usrName]#check offline msg
                                                                  sock_to_send.send(store_msg)   
                                                      else:
                                                            sock_to_send.send("BLOCK")

                                          else: 
                                                sock_to_send.send("usr not exist")
                        #loginfail

                                    if recv_list[1] == "loginfail":
                                          print "record loginfail"
                                          usrName = recv_list[0]
                                          timeoflastloginfail = recv_list[2]
                                          login_lock[usrName] = timeoflastloginfail

                        #logout                 
                                    if recv_list[1] == "logout":
                                          usrName=recv_list[0]
                                          print usrName+"log out"
                                          logout_broad = ">>>"+usrName+"<<<" + "logs out\n"
                                          del usr_ip[usrName]
                                          del usr_port[usrName]
                                          heartbeat_lock.acquire(1)
                                          try:
                                                del usr_timeoflastsig[usrName]
                                          except:
                                                print "fail to del usr_timeoflastsig"
                                          heartbeat_lock.release()
                                          broadcast(logout_broad,addr,usr_port)
                        #block sb
                                    if recv_list[1] == "block":
                                          if recv_list[2] in usr_pass:
                                                block_usr = recv_list[2]#who will be blocked
                                                op_usr = recv_list[0]#who initial the block
                                                usr_blacklist[op_usr].append(block_usr)
                                                clnt_port_l = usr_port[op_usr]
                                                sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                sock_to_send.connect((addr,clnt_port_l))
                                                sock_to_send.send(block_usr+" is Blocked Successfully\n")
                                          else:
                                                clnt_port_l = usr_port[op_usr]
                                                sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                sock_to_send.connect((addr,clnt_port_l))
                                                sock_to_send.send("\nblock_usr doesn't exist\n")
                        #unblock sb
                                    if recv_list[1] == "unblock":
                                          op_usr = recv_list[0]#who initial the block
                                          if recv_list[2] in usr_blacklist[op_usr]:#if the person to unblock is in blacklist only
                                                unblock_usr = recv_list[2]#who will be blocked
                                                usr_blacklist[op_usr].remove(block_usr)
                                                clnt_port_l = usr_port[op_usr]
                                                sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                sock_to_send.connect((addr,clnt_port_l))
                                                sock_to_send.send(unblock_usr+" is Unblocked Successfully\n")
                                          else:
                                                clnt_port_l = usr_port[op_usr]
                                                sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                sock_to_send.connect((addr,clnt_port_l))
                                                sock_to_send.send("\nunblock_usr doesn't exist in your blacklist\n")
                        #list online users
                                    if recv_list[1] == "online":
                                          print "list usr online"
                                          try:  
                                                usrName = recv_list[0]
                                                clnt_port_l = usr_port[usrName] 
                                                sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                sock_to_send.connect((addr,clnt_port_l))
                                                msg = "\n"
                                                for u,p in usr_ip.items(): 
                                                      u+="\n"
                                                      msg+=u
                                                sock_to_send.send(msg)
                                          except:
                                                print "online fail"
      			#send msg to another clnt 
                                    if recv_list[1] == "message":
                                          print recv_list
                                          usrName = recv_list[0]
                                          sendTo = recv_list[2]#sendto is the receiver of msg
                                          msg = recv_list[3:]
                                          msg = " ".join(msg)
                                          if sendTo in usr_pass:#sendto exist
                                                if usrName not in usr_blacklist[sendTo]:#receiver doesn't block sender
                                                      if sendTo in usr_ip:#receiver is online
                                                            try:
                                                                  addr_msg = usr_ip[sendTo]
                                                                  port_msg = usr_port[sendTo]
                                                                  sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                                  sock_to_send.connect((addr_msg,port_msg))
                                                                  sock_to_send.send("\n"+usrName + ":"+msg+"\n")
                                                                  print "msg delived"
                                                            except:#store msg if sending failed
                                                                  usr_store_msg[sendTo]+= "\n"+usrName+" said:"+msg+"\n"
                                                                  print "msg stored"
                                                      else:
                                                      #store msg if receiver is offline
                                                            usr_store_msg[sendTo]+= "\n"+usrName+" said:"+msg+"\n"
                                                            print "msg stored"
      			                        else: #notify sender that he is blocked by receiver 
                                                      clnt_port_l = usr_port[usrName]
                                                      sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                      sock_to_send.connect((addr,clnt_port_l))
                                                      sock_to_send.send("\nyou are blocked by this user, sending failed\n")
                                          else:#notify sender that reveiver doesn't exist
                                                clnt_port_l = usr_port[usrName]
                                                sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                sock_to_send.connect((addr,clnt_port_l))
                                                sock_to_send.send("\nusr doesn't exist\n")
                        #broadcast           
                                    if recv_list[1] == "broadcast":
                                          msg = recv_list[2]
                                          usr = recv_list[0]
                                          port = usr_port[usr]
                                          msg = usr + " said: "+ msg
                                          broadcast(msg,addr,port)
                        #getaddress
                                    if recv_list[1] == "getaddress":
                                          peerName = recv_list[2]
                                          usrName = recv_list[0]
                                          clnt_port_l = usr_port[usrName]
                                          sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                          sock_to_send.connect((addr,clnt_port_l))
                                          if usrName in usr_blacklist[peerName]:
                                                msg = "\nsorry, you are blocked by "+peerName+". Failed to get the peer address \n"
                                                sock_to_send.send(msg)
                                          else:
                                                try:
                                                      peer_port = usr_port[peerName]
                                                      peer_add = usr_ip[peerName]             
                                                      P2P_Privacy = myThread2("P2P_Thread",usrName,peerName,peer_add,peer_port,addr,clnt_port_l)
                                                      P2P_Privacy.setDaemon(True)
                                                      P2P_Privacy.start()
                                                except:#if peer is not online, try will fail to get peer_add and peer_port
                                                      sock_to_send.send(peerName+" is not online, please send offline msg")     
                                                #msg = "usrIp " + peerName + " " + peer_add + " " + str(peer_port)
                                                #sock_to_send.send(msg)

                        #close the socket and remove it from Socket_List_Read after all                  
                                    SOCKET_LIST_READ.remove(sock)
                                    sock.close()
                              else:
      				# 0 data received from clnt sock
                              	if sock in SOCKET_LIST_READ:
      			         		SOCKET_LIST_READ.remove(sock)
      			except:
                              print "in except"
                              continue

def broadcast (message,self_addr=None,self_port=None):#if self_addr not given, send to all login usr
      print "broadcast()"
      if len(usr_ip.items()) > 0:
            for usr in usr_ip:
                  addr_msg = usr_ip[usr]
                  port_msg = usr_port[usr] 
                  print addr_msg
                  sock_to_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                  if addr_msg == self_addr: #when the ip is the same
                        if port_msg !=  self_port :#when test within a machine, same ip but different port implies different usrs
                              sock_to_send.connect((addr_msg,port_msg))
                              try : 
                                    message = message + "\n"
                                    sock_to_send.send(message)
                              except :
                                    print"fail in broadcast()"
                  else:#when clnt on different machine, different ip implies different usrs
                        sock_to_send.connect((addr_msg,port_msg))
                        try : 
                              message = message + "\n"
                              sock_to_send.send(message)
                        except :
                              print"fail in broadcast()"

      else:
            print "no usr left..."

if __name__ == "__main__":
	server()

