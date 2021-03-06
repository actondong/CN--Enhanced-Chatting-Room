import sys
import socket
import select
import threading
import time
import logging
from collections import defaultdict
RECV_BUFFER = 4096
SOCKET_LIST_READ = []
def chat_client():
    if(len(sys.argv) < 3) :
        print 'Usage : python chat_client.py hostname port'
        sys.exit()
    host = sys.argv[1]
    port = int(sys.argv[2])
    s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip = socket.gethostbyname(socket.gethostname())
    s_sock.bind((ip, 6655))
#become a server socket
    s_sock.listen(5)
    SOCKET_LIST_READ.append(s_sock)
    c_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
    	c_sock.connect((host,port))
    	print "connected!"
    	print('Connected to remote host. You can start sending messages')
    	retry = 3
    	while retry>0:
    		usrName = raw_input("User Name: ")
    		passWord = raw_input("PassWord: ")	
    		logIn = usrName + " " + passWord
    		c_sock.send("logIn" +" " + logIn)
    		credentialCheck = c_sock.recv(100)
    		print credentialCheck
    		if credentialCheck == "Ok":
    			break
    		retry-=1
    	if retry == 0:
            c_sock.close()
            sys.exit("wrong usr info, Disconnected")

        print "welcome"
        time.sleep(2)
        c_sock.close()
        sys.stdout.write('[>>>] '); sys.stdout.flush()
    except:
    	sys.exit("Unable to connect")
    SOCKET_LIST_READ.append(sys.stdin)
    while 1:
        #print "in while"
    	ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST_READ , [], [])
    	for sock in ready_to_read:
            if sock == s_sock:
                print "in accept"
                try:
                    s_c_sock,addr = s_sock.accept()
                    SOCKET_LIST_READ.append(s_c_sock)
                except:
                    print "accept fail"
            elif sock == sys.stdin:
                print "in stdin"
                #try
                msg = raw_input("[>>>]:")
                c_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                c_sock.connect((host,port))   
    			#msg = sys.stdin.readline().strip()
                if msg == "logout":
                    print "in logout if "
                    c_sock.send(usrName+" "+msg)
                    sys.exit("Log out")
                else:
                    c_sock.send(usrName + " " + msg)
                #except:
                #   print "stdin fail to send"
            else:
                print "in else"
                data = sock.recv(4096)
                if not data:
                    print "\nDisconnected from server"
                    SOCKET_LIST_READ.remove(sock)
                else:
                    sys.stdout.write(data)
                    sys.stdout.flush()
                    SOCKET_LIST_READ.remove(sock)
                    sock.close()
                    print "else done"

                


if __name__ == "__main__":
    sys.exit(chat_client())