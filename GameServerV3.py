#
# TCP Server Project - Final
# CS3502 05 Mar 2018
# Capt Teal "Koala" Peterson
#
# GameServerV3.py
#
# Server for "Guess that Number!!" game.
# usage: GameServerV2.py [-h] [--version] [-a [ADDRESS]] [-t [GAME_TIME]]
#                       [-p [PLAYERS]]
#
# optional arguments:
#  -h, --help            show this help message and exit
#  --version             show program's version number and exit
#  -a [ADDRESS], --address [ADDRESS]
#                        Address that clients will connect to. Defaults to
#                        return from socket.gethostname() for the host running
#                        this .py
#  -t [GAME_TIME], --time [GAME_TIME]
#                        Sets how long game waits for answers. Defaults to 60
#                        seconds.
#  -p [PLAYERS], --players [PLAYERS]
#                        Sets how many players the server waits for before
#                        start. Defaults to 2 players.
#


import socket, sys, threading, time


class Server:
    '''Server object - server connection'''

    #Server Class defaults and constants
    D_PORT = 12000

    def __init__(self, host = socket.gethostname(),port=D_PORT, gameTime = 60):
        '''Initializer for the server.  If no host or port specified, the object defaults to use of
        localhost and port 1200'''

        self.__host = host
        self.__port = port
        self.__status = -1
        self.__sock = socket.socket() #defaults to AF_INET, SOCK_STREAM
        self.__connections = {}
        self.__numConnections = 0
        self.__playerNumber = 1
        self.__startTime = time.time()
        self.__game_time = gameTime
        self.__secretNumber = 0
        self.__connContr = None
        self.__main = threading.main_thread()
        self.__playingClients = {}
        self.__winners = []


        ### Public Variables ###
        self.gameOn = threading.Event()
        self.resultsReady = threading.Event()
        self.restart = True

    def start(self):
        '''Binds the server to the specified host/port, starts listening for connections,
        and starts a thread to continually accept connections as they're created.'''

        print("Starting server:",self.__host,self.__port)
        self.__sock.bind((self.__host,self.__port))
        self.__sock.listen(4)
        self.__status = 0
        self.__connContr = threading.Thread(target=self.__acceptConnections)
        self.__connContr.start()


    def __acceptConnections(self):
        '''Process thread in Server.start() to continually accept connections.
        Adds new connection to Server dictionary with connuction #, time, and socket.'''

        while self.__status == 0 and self.__main.is_alive():
            print("Waiting for a connection")
            try:
                newSocket, addr = self.__sock.accept()
            except OSError as exp:
                print("Server not accepting connections")
                return
            cxntime = time.time()
            self.__numConnections += 1
            print("Connected to {}.  Total connections now {}".format(addr,self.__numConnections))
            newPlayer = Server.PlayerInterface(addr,self.__playerNumber,cxntime,newSocket,self)
            self.__connections[addr] = newPlayer
            newPlayer.start()
            self.__playerNumber += 1


    def startGame(self):
        '''Starts the game timer and generates the random secret number'''

        self.gameOn.set()
        self.resultsReady.clear()
        self.__startTime = time.time()
        self.__secretNumber = random.randint(1,100)


    def getEndTime(self):
        '''Returns the time (since the epoch in seconds) when the game will end (float)'''
        return self.__startTime + self.__game_time


    def getTimeLeft(self):
        '''Returns the number of seconds remaining until game end (float)'''

        return self.__startTime + self.__game_time - time.time()


    def getMagic(self):
        '''Returns the secret number.'''

        return self.__secretNumber


    def stopGame(self):
        '''Signals server threads to stop the game. Clears game started event.'''

        self.gameOn.clear()
        self.resultsReady.clear()
        self.__playingClients = self.__connections #Stores list of players connected during the game


    def processResults(self):
        '''Process all guesses from participating clients. Returns winner list if required.
        Triggers event - results processed.'''

        ## Retrieve Guesses and find the winner ##
        self.__winners = [] #List in case there is a tie
        screwUps = []
        winnignDiff = 100
        print(self.__playingClients)
        for addr in self.__playingClients.keys():
            guess = self.__playingClients[addr].getGuess()
            print(addr,guess)
            
            #Handle clients with errors:
            if guess == '0' or guess == '-1':
                screwUps.append(addr)
                continue

            #Handle clients with guesses
            diff = abs(server.getMagic()-int(guess))
            if len(self.__winners) == 0 and addr not in screwUps:
                self.__winners = [addr] 
                winningDiff = diff
            elif winningDiff > diff:
                self.__winners = [addr] 
                winningDiff = diff
            elif winningDiff == diff:
                self.__winners.append(addr) #In case there is a tie

        print("Guess was {}, winner(s) is/are: {}".format(self.__secretNumber, self.__winners))
        self.resultsReady.set()

        return self.__winners

    def showWinners(self):
        '''Returns a list of winners.  Should call processResults first. (list)'''

        return self.__winners

    def __promptInput(self):
        selection = ''
        while selection not in {'y','Y','n','N'}:
            selection = input()
        if selection in {'n','N'}:
            self.restart = False


    def promptRestart(self):
        prompt = threading.Thread(target=self.__promptInput)
        prompt.start()
        print("")
        while prompt.is_alive():
            print("     <- Allow another game? (y/n)", end='\r')
            prompt.join(timeout=4)



    def getStatus(self):
        '''Returns server status code.'''

        return self.__status


    def getConnections(self):
        '''Returns server's dictionary, listing all connections.'''
        
        return self.__connections

    def numConnections(self):
        '''Returns current number of active connections. (int)'''

        return self.__numConnections


    def removeConnection(self,addr):
        '''Remove client from server dictionary.
        Returns 0 if client not in server dictionary.'''

        if addr in self.__connections:
            del self.__connections[addr]
            self.__numConnections -= 1
        else:
            return 0

    def stopServer(self):
        '''Stops server and closes all connections in server dictionary.
        Returns 1 if successful.'''

        self.__status = -1
        time.sleep(2)
        self.__sock.close()
        self.__connContr.join()
        return 1


    class PlayerInterface(threading.Thread):
        '''Player Object - contains data/execution thread for each new client.'''

        #I toyed with how much the server side should handle, vice how much the client should handle.
        #I decided to give the server more power, as it meant a lighter client that would require
        #less modification with later changes and I'm not worried about transmission rate.

        S_WAIT = 'W' #Wait to start
        S_TIMEOUT = 'T' #User Timeout
        S_BADGUESS = 'N' #No Guess/Bad Guess
        S_ACCEPTED = 'A' #Guess Accepted
        C_MAKEGUESS = 'P' #Make New Guess
        C_GUESSDONE = 'D' #Done Guessing
        C_CONFIRMTO = 'T' #Confirm Timout

        M_welcome ='\033[94m'+'''
       #######################################
       ##  Welcome to Guess that Number!!!  ##
       ##        You are player #{}          ##
       #######################################\n''' + '\u001b[0m'
        M_wait = S_WAIT +":Waiting for game to start."
        M_start = ":Game has started." #Game end time added prior to ':' on send.
        M_instructions = "Select a number between 1 and 100.  Seconds remaining for guess: "
        M_noTime = S_TIMEOUT +":You submitted your answer too late. Move more quicklier!!"
        M_invalidGuess = S_BADGUESS+":That is not a valid entry. Try again."
        M_goodGuess = S_ACCEPTED +":Guess of {} received."
        M_gameEnd = "The number is {} and your guess is {}. "
        M_winningGuess = "You win with the closest guess."
        M_losingGuess = "Better luck next time"



        def __init__(self,addr,playerNum,cxntime,sock,parent):
            self.__addr = addr
            self.__playerNum = str(playerNum)
            self.__cxntime = cxntime
            self.__sock = sock
            self.__parentServer = parent
            self.__status = 1
            self.__guess = '0'
            self.__userAction = self.C_MAKEGUESS

            #Initialize thread portion of Thread Class inheritance
            super().__init__()

        def __str__(self):
            return str(self.__addr)

        def run(self):
            '''Execution thread for each client... sends interface messages, receives guesses,
            and control flags for the server.'''

            print("S0-" + str(self) + ": "+ self.send(self.M_welcome.format(self.__playerNum)))

            #Send game 'wait' status and wait for game start
            if not self.__parentServer.gameOn.is_set():
                print("S1-" + str(self) + ": " + self.send(self.M_wait))
                self.__parentServer.gameOn.wait()

                    
            while self.__parentServer.gameOn.is_set() and self.__userAction == self.C_MAKEGUESS:
                #Start Game
                print("S2-" + str(self) + ": " + self.send(str(self.__parentServer.getEndTime())+self.M_start))

                while self.__userAction == self.C_MAKEGUESS:
                    #Send Instructions
                    timeLeft = int(self.__parentServer.getTimeLeft())
                    print("S3-" + str(self) + ": " + self.send(self.M_instructions+str(timeLeft)))

                    #Receive Guess
                    self.__guess = self.receive()
                    print("C-" + str(self) + " Sent: ", self.__guess)


                    #This looks weird in that it seems like the user could submit an answer on time, then 
                    #still get a non-submitted in time error.  However, this window is so small, that the
                    #user wont notice that he submitted only a few milliseconds prior to end time.
                    if self.__parentServer.getTimeLeft() < 0:
                        #No time left
                        print("Time's up")
                        serverCode = self.S_TIMEOUT
                    else:
                        #Validate guess
                        try:
                            guess = int(self.__guess)
                            #Checks for Guess out of Range
                            if guess > 100 or guess < 1:
                                serverCode = self.S_BADGUESS
                            else:
                                #Guess in Range
                                serverCode = self.S_ACCEPTED
                        except ValueError:
                            #If input is not a number...
                            serverCode = self.S_BADGUESS

                    #Send Appropriate Acknowledgement
                    if serverCode == self.S_BADGUESS:
                        print("S4-" + str(self) + ": " + self.send(self.M_invalidGuess))
                        self.__guess = '0' 
                    elif serverCode == self.S_ACCEPTED:
                        print("S5-" + str(self) + ": " + self.send(self.M_goodGuess.format(self.__guess)))
                    elif serverCode == self.S_TIMEOUT:
                        print("S6-" + str(self) + ": " + self.send(self.M_noTime))

                    #This seemed to help with some random sync issues.
                    time.sleep(.25)

                    #Process user decision: (if/elif structure for clarity of execution only)
                    self.__userAction = self.receive()
                    if self.__userAction == self.C_GUESSDONE:
                        continue
                    elif self.__userAction == self.C_CONFIRMTO:
                        continue
                    elif self.__userAction == self.C_MAKEGUESS:
                        self.__guess = '0'
            
            #Wait for server to compile results, then send them to client
            self.__parentServer.resultsReady.wait()
            winnerList = self.__parentServer.showWinners()
            if self.__addr in winnerList:
                message = self.M_gameEnd.format(self.__parentServer.getMagic(),self.__guess) + self.M_winningGuess
                print("S7-" +str(self.__addr) + ": " + self.send(message))
            elif self.__addr not in winnerList:
                message = self.M_gameEnd.format(self.__parentServer.getMagic(),self.__guess) + self.M_losingGuess
                print("S8-" +str(self.__addr)+": " + self.send(message))

            self.close()
                                        
        
        def send(self, message):
            '''Handles dirty work of prepping message for send, then sends.
            Returns the input message for easier printing. (str)'''

            rmessage = message.encode()
            self.__sock.sendall(rmessage)
            return message


        def receive(self):
            '''Handles dirty work of receiving/decoding a message. (str)'''

            return self.__sock.recv(256).decode()


        def getGuess(self):
            '''Returns current contents of guess varible. Starts at 0. (str)'''

            return self.__guess


        def close(self):
            '''Closes client connection and joins client thread. Returns 1 if
            everything stops ok, 0 otherwise. (int)'''

            try:
                print("Closing connection with", self.__addr)
                self.__status = 0
                self.__sock.shutdown(socket.SHUT_RDWR)
                self.__sock.close()
                self.__parentServer.removeConnection(self.__addr)
                return 1
            except Exception as exp:
                print("Error closing connection with", self.__addr)
                print(exp)
                return 0


## BEGIN EXECUTION OF PROGRAM ##

if __name__ == "__main__":
    import argparse, random

    ### Program Defaults/Constants ###
    versNum = "Step 3"
    D_HOST = socket.gethostname()
    D_TIME = 60
    D_PLAYERS = 2

    ### Parse CLI args ###
    cliParser = argparse.ArgumentParser(description='Server for "Guess that Number!!" game.')
    cliParser.add_argument("--version", action = "version", version = ("%(prog)s:" + versNum))
    cliParser.add_argument("-a","--address", default=D_HOST, nargs='?', dest = "address", 
                           help=("Address that clients will connect to. " + 
                                 "Defaults to return from socket.gethostname() for the host running this .py"))
    cliParser.add_argument("-t","--time", default=D_TIME, nargs='?', type=int, dest = "game_time",
                           help="Sets how long game waits for answers. Defaults to 60 seconds.")
    cliParser.add_argument("-p","--players", default=D_PLAYERS, nargs='?', type=int, dest = "players",
                           help="Sets how many players the server waits for before start. Defaults to 2 players.")
    args = cliParser.parse_args()
    host = args.address
    game_time = args.game_time
    players = args.players
    print("Game starts with {} players.  Game time set to {}.".format(players,game_time))

    try:
        print('\u001b[31m'+'''
    ############################
    ##  GUESS THAT NUMBER!!!  ##
    ##       SERVER LOG       ##
    ############################
    '''+'\u001b[0m')

        server = Server(host = host, gameTime = game_time)
        server.start()

        
        while server.restart:

            ## Wait for required minimum number of players ##
            c = 0
            while server.numConnections() < players:
                time.sleep(1) #Minimize drain on CPU
                c += 1
                print("Waiting",c,end='\r')

            ## Collect players and guesses ##
            server.startGame()
            time.sleep(server.getTimeLeft())
            server.stopGame()
            server.processResults()
            c = 0
            while server.numConnections() > 0:
                time.sleep(1) #Minimize drain on CPU
                c += 1
                print("Waiting for all clients to disconnect",c, end='\r')
            server.promptRestart()

    finally:
        print("Server Stopping")
        server.stopServer()
        print("Server Stopped")
