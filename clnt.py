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
usrName = "usr"#global var for username
usr_ip = {} # keep ip needed for p2p communication
usr_port = {}# keep port needed for p2p communication
class myThread (threading.Thread):
    def __init__(self, name,host,port,usr):
        threading.Thread.__init__(self)
        self.name = name
        self.host = host
        self.port = port
        self.usr = usr
    def run(self):
        print "Starting " + self.name
        while 1:
            protocal = "heartbeat"
            t_stamp = datetime.now().strftime("%Y-%m-%d%H:%M:%S")#change datetime obj to str in a fixed format
            msg = self.usr + " "+ protocal+ " "+ t_stamp#prepend with a protocal tag
            c_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            c_sock.connect((self.host,self.port))  
            c_sock.send(msg)
            time.sleep(30)#every 30 secs, send out a live signal

def chat_client():
    if(len(sys.argv) < 3) :
        print 'Usage : python chat_client.py hostname port'
        sys.exit()
    host = sys.argv[1]
    port = int(sys.argv[2])
    s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#create a socket for listening on clnt
    ip = socket.gethostbyname(socket.gethostname())

    s_sock.bind((ip, 0)) #port 0 will let os pick up a free port to use
    clnt_port_l = s_sock.getsockname()[1]
#become a server socket
    s_sock.listen(5)#up to 5 
    SOCKET_LIST_READ.append(s_sock)
    c_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
    	c_sock.connect((host,port))
    	print "connected!"
    	retry = 3
        while retry>0:
            usrName = raw_input("User Name: ")
            passWord = raw_input("PassWord: ")
            usrName = usrName.strip()
            passWord = passWord.strip()
            logIn = usrName + " " + passWord + " " + str(clnt_port_l)#initial msg sent to server includes clnt listen port. Once login
            #is authorized, the clnt listen port will be stored on server side.
            c_sock.send("logIn" +" " + logIn)
            credentialCheck = c_sock.recv(100)
            print credentialCheck
            if credentialCheck == "Ok":
                break
            retry-=1
        if retry == 0:
            c_sock.close()
            sys.exit("wrong usr info, Disconnected")

        print "welcome"+">>>"+ usrName+"<<<"
        time.sleep(2)
        c_sock.close()
        sys.stdout.write('[>>>] '); sys.stdout.flush()
    except:
    	sys.exit("Unable to connect")
    hearbeat_t = myThread("heartbeat",host,port,usrName)
    hearbeat_t.setDaemon(True)
    hearbeat_t.start()
    SOCKET_LIST_READ.append(sys.stdin)
    while 1:
        #print "in while"
    	ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST_READ , [], [])
    	for sock in ready_to_read:
            if sock == s_sock:
                try:
                    s_c_sock,addr = s_sock.accept()
                    SOCKET_LIST_READ.append(s_c_sock)
                except:
                    print "accept fail"
            elif sock == sys.stdin:
                #try
                msg = raw_input("[>>>]:")
                msgList = msg.split(" ")
                protocal = msgList[0]#get protocal of sending msg
                c_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                c_sock.connect((host,port))#connect to server , ready to send msg 
                if msg == "logout":
                    c_sock.send(usrName+" "+msg)
                    sys.exit("Log out")
                elif protocal == "private":
                    peerName = msgList[1]
                    if peerName not in usr_ip:
                        print "getaddr first before P2P messaging"
                    else:
                        peerAddr = usr_ip[peerName]
                        peerPort = usr_port[peerName]
                        peerMsg = msgList[2:]
                        peerMsg = " ".join(peerMsg)
                        c_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        try:
                            c_sock.connect((peerAddr,peerPort))#initialize socket to send to peer
                            msg = usrName+": "+peerMsg + "\n"
                            c_sock.send(msg)
                        except:#if connection fails
                            print peerName+" is no longer available on the given IP, please send offline msg "
                else:
                    c_sock.send(usrName + " " + msg)
                #except:
                #   print "stdin fail to send"
            else:
                data = sock.recv(4096)
                if not data:
                    print "\nsocket brokes\n"
                    SOCKET_LIST_READ.remove(sock)
                else:
                    msg = data.split(" ")
                    if msg[0] == "usrIp":
                        peerName = msg[1]
                        peerAddr = msg[2]
                        peerPort = msg[3]
                        usr_ip[peerName] = peerAddr
                        usr_port[peerName] = int(peerPort)
                        SOCKET_LIST_READ.remove(sock)
                        sock.close()          
                        
                    elif msg[0] == "logout":
                        dup_ip = msg[1]
                        msg =  "logout because new login on "+dup_ip+"\n"
                        sys.exit(msg)
                    else:
                        sys.stdout.write(data)
                        sys.stdout.flush()
                        SOCKET_LIST_READ.remove(sock)
                        sock.close()                
         #broadcast(s_sock,sock,recv_buff)


if __name__ == "__main__":
    sys.exit(chat_client())