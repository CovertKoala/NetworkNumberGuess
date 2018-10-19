#
# TCP Client Project - Final
# CS3502 05 Mar 2018
# Capt Teal "Koala" Peterson
#
# GameClient.py
#
# Client for "Guess that Number!!" game.
# usage: GameClientV2.py [-h] [--version] [-a [ADDRESS]]
#
# optional arguments:
#  -h, --help            show this help message and exit
#  --version             show program's version number and exit
#  -a [ADDRESS], --address [ADDRESS]
#                        Address that client connects to. Defaults to return
#                        from socket.gethostname() for the host running this .py
#

import socket, sys, threading, time

class Client:
    '''Client object - client connection'''

    #Client Class defaults and constants
    D_PORT = 12000

    def __init__(self, host = socket.gethostname(),port=D_PORT):
        '''Initializer for the client.  If no host or port specified, the object defaults to use of
        localhost and port 1200'''

        self.host = host
        self.port = port
        self.status = -1
        self.sock = socket.socket() #defaults to AF_INET, SOCK_STREAM
        self.endTime = 0
        self.guess = 0


    def setHostName(self,hostname = None):
        '''Sets the client hostname.'''

        if hostname == None:
            hostname = input("Please provide the server hostname (or type 'quit' to exit): ")
        if hostname == "quit":
            exit()
        self.host = hostname
        return hostname


    def establishConnection(self):
        '''Establish client connection.  Default host is "localhost" unless set previously
         by clientObj.setHostName().  Returns client status code (0 if succussful).'''

        if self.status != 0:
            print("Connecting to " + self.host + ':' + str(self.port))
            self.status = self.sock.connect_ex((self.host, self.port))
            if self.status == 0:
                print("S0: " + client.receive())
            elif self.status == 111:
                print("Error: Could not connect to server; ensure server is accepting connections.")
            else:
                print("Error: Connection-Other...")
        else:
            print("Connection already established")

        return self.status

    def getStatus(self):
        '''Returns status of the connection (int)'''

        return self.status


    def getConnectionStatus(self):
        '''Returns a string describing the client connection status. (str)'''

        if self.status == -1:
            status_description = "Disconnected"
        elif self.status == 0:
            status_description = "Connected"
        elif self.status == 111:
            status_description = "Connection refused"

        return status_description


    def closeConnection(self):
        '''Closes client socket.'''

        if self.status == 0:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                time.sleep(1)
                self.sock.close()
            except Exception as exp:
                import traceback
                traceback.print_exc(file=sys.stdout)
            self.status = -1
            #print("\nConnection Closed")

    def send(self,message):
        '''Send a message.  Returns that message.'''

        rmessage = str(message).encode()
        try:
            self.sock.sendall(rmessage)
        except:
            pass
        return message

    def receive(self):
        '''Receive and return a message.'''

        message = self.sock.recv(256)
        message = message.decode()
        return str(message)


    #__input() and getGuess() were required to prompt when the user was out of time
    #and to put a time limit on user input.
    def __input(self):
        '''Get input'''

        self.guess = input()


    def getGuess(self):
        '''Starts a thread to get input from the user.  This allows printing of the game
        timeout message when it occurs.  Returns the input guess from the user. (str)'''

        clientIn = threading.Thread(target=self.__input)
        clientIn.start()
        now = time.time()
        timeLeft = self.endTime - now
        clientIn.join(timeout = timeLeft)
        #The timeout above was intended to close out input... doesn't seem to do that
        #investigating more in later versions
        return self.guess


    def setEndTime(self,time):
        '''Sets client end time... probably should be a private method... ... ...
        Returns the time set (another elipse) for easier printing. (float)'''

        self.endTime = time
        return time


    def getTimeLeft(self):
        '''Returns the number of seconds left in the game. (float)'''

        return self.endTime - time.time()

    def playGame(self):
        '''Method to start a single game iteration.'''

        #Message indexes
        S_CODE = 0
        S_MSG = 1

        S_WAIT = 'W' #Wait to start
        S_TIMEOUT = 'T' #User Timeout
        S_BADGUESS = 'N' #No Guess/Bad Guess
        S_ACCEPTED = 'A' #Guess Accepted
        C_MAKEGUESS = 'P' #Make New Guess
        C_GUESSDONE = 'D' #Done Guessing
        C_CONFIRMTO = 'T' #Confirm Timout

        if self.status == 0:
            #R: Welcome message - Handled as connection confirmation
            #Receive/print game status
            serverMsg = [S_WAIT]
            while serverMsg[S_CODE] == S_WAIT:  #Using a while loop ensures no progression until start message
                serverMsg = self.receive().split(':')
                print("S1|2: ",end='')
                print(serverMsg[S_MSG])

            #Syncs Server/Client end time
            self.setEndTime(float(serverMsg[S_CODE]))
    
            actionCode = C_MAKEGUESS
            while actionCode == C_MAKEGUESS:
                #Prompt for a guess
                print("S3: ",end='')
                print(self.receive())
                if self.getTimeLeft() > 0:
                    guess = self.getGuess()
                else:
                    #Server should catch timeout, the client does to
                    actionCode = C_CONFIRMTO
                    guess = '0'

                self.send(guess)

                serverMsg = self.receive().split(':')
                if len(serverMsg) == 2:
                    #Display server response
                    print("S4|5|6: ",end='')
                    print(serverMsg[S_MSG])


                #Get/send user action/decision code - will likely turn
                # these into constants for later versions
                serverCode = serverMsg[S_CODE]
                actionCode = ''
                if serverCode == S_ACCEPTED:
                    promptAgain = input("Reset answer (y/n)?: ")
                    #Add input checks
                    if promptAgain != 'n':
                        actionCode = C_MAKEGUESS
                    else:
                        actionCode = C_GUESSDONE
                        print("Waiting for results!!")
                        while self.getTimeLeft() > 0:
                            print("{:3}".format(int(self.getTimeLeft())),end='\r')
                            time.sleep(.5)
                elif serverCode == S_BADGUESS:
                    actionCode = C_MAKEGUESS
                    guess = '0'
                elif serverCode == S_TIMEOUT:
                    actionCode = C_CONFIRMTO
                self.send(actionCode)

            #Get win/lose notice
            if serverMsg[S_CODE] == S_ACCEPTED:
                print("S7|8: ",end='')
                print(self.receive())
            else:
                print("Type <enter> to exit: ",end='')

        else:
            print("Error: Must establish a connection with the server first. Use establishConnection().")


## BEGIN EXECUTION OF PROGRAM ##

if  __name__ == "__main__":
    import argparse

    ### Program Defaults/Constants ###
    versNum = "Step 3"
    D_HOST = socket.gethostname()

    ### Parse CLI args ###
    cliParser = argparse.ArgumentParser(description='Client for "Guess that Number!!" game.')
    cliParser.add_argument("--version", action = "version", version = ("%(prog)s:" + versNum))
    #Set hostname
    cliParser.add_argument("-a","--address", default=D_HOST, nargs='?', dest = "address", 
                           help=("Address that client connects to. " + 
                                 "Defaults to return from socket.gethostname() for the host running this .py"))
    args = cliParser.parse_args()
    host = args.address

    client = Client(host)
    client.establishConnection()

    if client.getStatus() == 0:
        client.playGame()

    client.closeConnection()
    print("Restart client to play again!!")

