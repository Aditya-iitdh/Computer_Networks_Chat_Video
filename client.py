from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from socket import *
import threading
import pickle
import cv2
import struct

try:
    client_socket = socket(AF_INET, SOCK_STREAM)
    print("Client Socket created!")
except:
    print("Error creating socket")

client_port = 8000

mykey = RSA.generate(2048)

mypublickey = mykey.public_key().export_key()

cipher = PKCS1_OAEP.new(mykey)

client_socket.connect(("", client_port))

lock_send = threading.Semaphore(0)
lock_recv = threading.Semaphore(1)

clients = {}    # dictionary containing name to key mapping
client_name = ""
choice = ""
video = ""

def client_send():
    lock_send.acquire()
    global client_name
    client_name = input()
    client_socket.send(client_name.encode())
    print("Name sent")
    lock_recv.release()
    
    lock_send.acquire()
    client_socket.send(mypublickey)
    print("Public key sent")
    lock_recv.release()

    while True:
        print("\nOptions:")
        print("1. Message a client")
        print("2. Video streaming")
        print("3. QUIT")
        print("What do you want to do? Enter S.No.")
        global choice
        choice = input(">")
        if choice == "3":                                   # Client wants to disconnect
            client_socket.send("QUIT".encode())
            lock_recv.release()
            break
        elif choice == "1":                                 # Client wishes to message a client
            print("Available clients:")
            for i in clients.keys():
                print(i)
            name = input("Whom do you want to message?")
            for i in clients.keys():
                if i.lower() == name.lower():
                    name = i
                    break
            message = input("Message: ")
            message = message.encode()

            try:
                public_key = RSA.import_key(clients[name])
                cipher_public = PKCS1_OAEP.new(public_key)
                ciphertext = cipher_public.encrypt(message)
                client_socket.send(choice.encode()+ciphertext)
            except:
                print("No such client", name)
        elif choice == "2":                                 # Client wants a video to be streamed
            client_socket.send(choice.encode())             # Tell server that clients wants to watch a video
            lock_send.acquire()
            client_socket.send(video.encode())              # Tell the video to be streamed from the list sent in receive thread
            lock_recv.release()

def client_recv():
    lock_recv.acquire()
    message = client_socket.recv(2048).decode()
    print(message)
    lock_send.release()
    
    lock_recv.acquire()
    message = client_socket.recv(2048).decode()
    print(message)
    lock_send.release()

    while True:
        if choice == "3":                       # If client is disconnecting then it should not be receiving anything
            break
        message = client_socket.recv(2048)
        if choice == "3":                       # In case client was already listening, we will check for the choice now.
            break
        elif message[0:4] == b"DICT":           # Received a broadcasted dictionary
            # client_data = message[4:]
            client_data_index = message.index(b":",5)
            name_affected = message[5:client_data_index]
            clients_modified = pickle.loads(message[client_data_index+1:])
            global clients
            if len(clients_modified) > len(clients):
                print("\nNew connection:", name_affected.decode(), '\n')
            elif len(clients_modified) < len(clients):
                print("\nClient", name_affected.decode(), "left\n")
            clients = clients_modified
        elif message[0:3] == b"MSG":            # Received a personal message from a client
            print("\nReceived a message from server")
            sender = message[message.index(b"From:")+5:message.index(b"\0")].decode()
            client_msg = message[100:]
            try:
                message1 = cipher.decrypt(client_msg)
                print("Message from:", sender)
                print("Decrypted message: ", message1.decode(), '\n')
            except:
                print("Well... the message isn't for me I guess :(\n")
        elif message[0:5] == b"AVVID":          # Server returns list of available videos when requested.
            print(message[6:].decode(), end='>')
            lock_recv.acquire()
            global video
            video = input()
            lock_send.release()
        elif message == b"FRAMES":              # Frames for the video requested.
            print("Receiving frames now")
            payload = b""
            payload_size = struct.calcsize("L")
            while True:
                while len(payload) < payload_size:
                    packet = client_socket.recv(4 * 1024)
                    if not packet:
                        break
                    payload += packet
                payload_msg_size = payload[:payload_size]
                payload = payload[payload_size:]
                msg_size = struct.unpack("L", payload_msg_size)[0]
                if msg_size == 0:
                    break
                while len(payload) < msg_size:
                    payload += client_socket.recv(64 * 1024)    # Changing the buffer size would alter the rate at which video is played
                frame_data = payload[:msg_size]
                payload = payload[msg_size:]
                frame = pickle.loads(frame_data)
                frame = cv2.resize(frame, (720, 540))
                cv2.imshow("Video", frame)
                if cv2.waitKey(25) & 0xFF == ord('q'):
                    break
            cv2.destroyAllWindows()

send_thread = threading.Thread(target=client_send)
recv_thread = threading.Thread(target=client_recv)

send_thread.start()
recv_thread.start()

send_thread.join()
recv_thread.join()

client_socket.close()