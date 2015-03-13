CN_PA1 ChatRoom
sd2810
shiyu dong
###############
0. >>>even before moving to design<<<
   I use 5566 as default listen port for server. If you fail to initialize server because of 5566 is used.
   First
   $lsof -i:5566
   Then remember the pid of reported process
   $kill <pid>
   However, the above should never happen, os doesn't use this port and app should not use port like 5566 either. 

   Use control-C to abruptly terminate clnt. cltr-C will terminate all threads of clnt/server program. Once terminate by cltr-C,
   give os several seconds to reclaim ports. Then you can start the server again.

   I have everything under monioring on server side, which means you can see logs of every operation(fail or succeed) on server side stdout.

   I recommend you press 'return' button after every receiving to make your clnt side screen well formatted.
   
   

1. Design && DataStructure:

>>>Design<<<
I use multiplexing non-blocking I/O [select() function from select module] mechanism in both clnt side and server side to handle
TCP connections. 

On clnt side, I also have a socket for listening, name it sock_clnt_l. Initially, I put sys.stdin, sock_clnt_l in SOCKET_LIST_READ.
When scok_clnt_l accepts a new coming sock, the new sock is added to SOCKET_LIST_READ. Thus the select mechanism will keep monitoring the above three kinds of socks for reading and select those ready for reading to read from.

On server side, Initially I have sock_server_l in SOCKET_LIST_READ, and whenever sock_server_l accepts new sockets, those new sockets are added to SOCKET_LIST_READ.

Besides multiplexing select in one thread, I have two more threads on server side and one more thread on clnt side.

On clnt side, I have thread for sending HeartBeat to server every 5 secs. The HeartBeat thread is started once usr successfully login. Inside the thread, there is a while 1 loop, so untill the clnt exits, the HeartBeat thread keeps sending hearbeats to server every 5 secs.

On server side, First I also have a HeartBeat thread for checking heartbeat records for each usr every 5 secs. If any usr's record 				is outdated(5 secs ago), then the usr will be logouted by the server. And the server broadcasts that the usr logout. 
   				
   				Second I have a P2P thread for p2p consent/privacy purpose. The P2P thread is started every time a usr want to getaddress of a peer. Inside the P2P thread, the server initialize a sock to communicate with peer and a sock to cumminucate with usr. The P2P thread will take all variables needed to establish above two socks. 
                The reason to have such a dependent thread is that sock.recv() will block , the server need to wait for the 
                feedback from the peer. The sending and receiving are both done within the same thread, so the sock is closed on server side finally after sock.recv(). Notice that, while being asked for feedback from the server, the peer will 
                be blocked till it gives feedback. This is reasonable.
>>>DataStruct<<<
To store information needed on both clnt and server sides, I use python dicts only.

>>Server:
usr_ip = {}#store ip for each login usr 
usr_port = {}#store listen port on each clnt 
usr_store_msg =defaultdict(lambda:" ")
usr_pass = {}
usr_blacklist=defaultdict(lambda:[])
sock_ip ={}
usr_timeoflastsig=defaultdict(lambda:" ")
heartbeat_lock = threading.Lock()
login_lock=defaultdict(lambda:" ")
>>Clnt:
usrName = "usr"#global var for username
usr_ip = {} # keep ip needed for p2p communication
usr_port = {}# keep port needed for p2p communication 

>>>Source Code Explanation<<<
My code is commented while writing. With the design information above, it should be very clear.

>>>Instructions on how to run/compile<<< 
In terminal, cd to the folder having all source codes and files.(put your new test credential file in it too)
>>To start the server:
$python server.py

>>To start the clnt:
5566 is the default server port
Type ip in Google to get your IP.

$python clnt.py <your IP> 5566 
OR
$python clnt.py <your local host name> 5566 #To get your local host name, see info below in Sample Commands/Start Server

>>>Sample Commands (on my mac )<<<
>>General:

You are allowed to type anything on clnt side, but only under pre-defined format(protocal), you can expect certain responses. You will get no response by typing something which is not under any pre-defined protoca
press 'return' button , you send a '\n' to server. You should frequently press 'Return' button to keep clnt side screen having "[>>>]:" shown.


>>Start Server:
$python server.py

When server starts, you should see below info:

columbia #Information about credentials are listed
116bway
seas
summerisover
csee4119
lotsofexams
foobar
passpass
windows
withglass
google
hasglasses
facebook
wastingtime
wikipedia
donation
network
seemsez
tous-MacBook-Pro.local#This is your local host name

The last line : tous-MacBook-Pro.local is the name of local host.

>>Start Clnt:
$python clnt.py tous-MacBook-Pro.local 5566

>>login:
#############
You will see:
connected!
User Name:
#############
*************
You should:
Type your usrname
when it is done, press 'return' button
Type your password 
when it is done, press 'return' button
**************
Valid usrname and password combinations are shown in credentials above.
#############
You will see:
welcome>>>seas<<<
>>>seas<<<logs in
#############
You can add spaces after usrname or password, this will be ignored though.

You can only have three chances to login. If you login with usr seas with wrong password 3 times in a row, you will be blocked
for 30 secs to login as seas.(NOTICE: the usr who would be blocked is the one corresponding to your last failure of login out of three, which means, if you first login with seas twice (bot fail) and then login with columbia(also fail), what would be blocked is columbia. This is not very reasonable, but since there is no more detail about how to deal with three login in a row with different usrname, so I choose to implement the above.)

If you login with seas, but seas is then used to login by someone else, your chat service will be closed. And you will
be notified with the new IP where seas login with.


To make screen clean
**************
You could always:
press 'return' button
**************

In this sample commands, I login two usrs: columbia and seas on same machine.
>>online:
*************
You should type:
online
**************
#############
You will see:
[>>>]:
seas
columbia
#############

>>message:
*************
You should type on seas side:
message columbia 123
**************
#############
You will see on columbia side:
seas:123
#############

If you message some valid usr who is not online, the msg will be kept as offline msg on server side. And the msg will
be delivered to the usr when that usr login.

>>broadcast
*************
You should type on seas side:
broadcast 321
**************
#############
You will see only on columbia side not on seas side:
seas said: 321
#############

>>getaddress
*************
You should type on seas side:
getaddress columbia 
**************
If you are not blocked by columbia,(bonus part)
#############
You will see only on columbia side :
[>>>]:Privacy seas wants to get your IP for P2P chat. Type Y/y if agree, type N/n otherwise
>>>Type Y to accept, N to reject<<<:
#############
You should type Y/y to authorize and N/y and reject on columbia side. (bonus part)

If you getaddress on usr who is not online, you will see:
#############
You will see only on seas side :
<corresponding usr> is not online, please send offline msg
#############

>>private
You should private only those already have been getaddressed of.
**************
You should type on seas side:
private columbia 333
**************
#############
You will see on columbia side :
seas: 333
#############
If you private those haven't been getaddressed of:
#############
You will see on seas side :
getaddr first before P2P messaging
#############

>>block
You can only block usr from given credentials.
**************
You should type on seas side:
block columbia 
**************
##############
You will see on seas side :
[>>>]:columbia is Blocked Successfully
#############
>>unblock
**************
You should type on seas side:
unblock columbia 
**************
##############
You will see on seas side :
[>>>]:columbia is Unblocked Successfully
##############
If you block usr not in credentials:
##############
You will see on seas side :
block_usr doesn't exist
#############
If you unblock usr not in your blacklist
##############
You will see on seas side :
unblock_usr doesn't exist in your blacklist
#############

>>logout
**************
You should type on seas side:
logout
**************
##############
You will see on columbia side :
>>>seas<<<logs out
#############

If seas does not logout normally, but with ctrl-C. Then after 5 secs, 
##############
You will see on columbia side :
>>>seas<<<logs out
#############

>>>>>guaranteed msg delivery<<<<<<<(bonus)
I set heartbeat send every 5 secs, during the 5 seconds, you will have guaranteed msg delivery.

If you send out a msg(thru message or private)without seeing any instruction/notification about how to send it in a right way, then the msg is guaranteed to be delivered, which means, if the receiver is offline abnormly, the msg will be saved as offline msg
on server side.


>>>>Bonus Part<<<<<
1.P2P Privacy and Consent
2.Guaranteed Message Deliver

#########



