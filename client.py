from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from socket import *
import threading
import pickle
import cv2
import sys
import struct

try:
    client_socket = socket(AF_INET, SOCK_STREAM)
    print("Client Socket created!")
except:
    print("Error creating socket")

client_port = 8000

mykey = RSA.generate(2048)

data = mykey.public_key().export_key()

cipher = PKCS1_OAEP.new(mykey)

client_socket.connect(("", client_port))

lock_send = threading.Semaphore(0)
lock_recv = threading.Semaphore(1)

clients = {}    # dictionary containing
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
    client_socket.send(data)
    print("Public key sent")
    lock_recv.release()
    #Q1 done------------------------------------------------------

    while True:
        # lock_send.acquire()
        print("\nOptions:")
        print("1. Message a client")
        print("2. Video streaming")
        print("3. QUIT")
        print("What do you want to do? Enter S.No.")
        global choice
        choice = input()
        if choice == "3":
            client_socket.send("QUIT".encode())
            lock_recv.release()
            break
        elif choice == "1":
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
            # public_key = RSA.import_key(list(clients.values())[0])
            public_key = RSA.import_key(clients[name])
            cipher_public = PKCS1_OAEP.new(public_key)
            ciphertext = cipher_public.encrypt(message)
            # client_socket.send(choice.encode())
            client_socket.send(choice.encode()+ciphertext)
        elif choice == "2":
            client_socket.send(choice.encode())
            lock_send.acquire()
            client_socket.send(video.encode())
            lock_recv.release()
            # available_videos = client_socket.recv(2048).decode()
            # print(available_videos)
        # lock_recv.release()

def client_recv():
    lock_recv.acquire()
    message = client_socket.recv(2048).decode()
    print(message)
    lock_send.release()
    
    lock_recv.acquire()
    message = client_socket.recv(2048).decode()
    print(message)
    lock_send.release()
    #Q1 done------------------------------------------------------

    while True:
        # lock_recv.acquire()
        if choice == "3":       # If client is disconnecting then it should not be receiving anything
            break
        # print("Next message")
        message = client_socket.recv(2048)
        # print(message)
        if choice == "3":   # In case client was already listening, we will check for the choice now.
            break
        elif message[0:4] == b"DICT":
            client_data = message[4:]
            global clients
            clients = pickle.loads(client_data)
            # print("\nClient data from server:\n",clients)   # Receiving dictionary correctly. Commenting this print()
        elif message[0:3] == b"MSG":
            print("\nReceived a message from server")
            sender = message[message.index(b"From:")+5:message.index(b"\0")].decode()   # Extract name of sender from received message
            client_msg = message[100:]
            # print("Received message:", client_msg)
            try:
                message1 = cipher.decrypt(client_msg)
                print("Message from:", sender)
                print("Decrypted message: ", message1.decode(), '\n')
            except:
                print("Well... the message isn't for me I guess :(\n")
        elif message[0:5] == b"AVVID":
            print(message[6:].decode(), end='>')
            lock_recv.acquire()
            global video
            video = input()
            lock_send.release()
        # elif message == b"FRM:0:":
            # print("Destroying frames...")
            # cv2.destroyAllWindows()
                # continue
        elif message == b"FRAMES":
            print("Receiving frames now")
            data = b""
            payload_size = struct.calcsize("L")
            while True:
                while len(data) < payload_size:
                    packet = client_socket.recv(4 * 1024)
                    if not packet:
                        break
                    data += packet
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("L", packed_msg_size)[0]
                if msg_size == 0:
                    break
                while len(data) < msg_size:
                    data += client_socket.recv(4 * 1024)
                frame_data = data[:msg_size]
                data = data[msg_size:]
                frame = pickle.loads(frame_data)
                frame = cv2.resize(frame, (1080,720))
                cv2.imshow("Video", frame)
                if cv2.waitKey(25) & 0xFF == ord('q'):
                    break
            cv2.destroyAllWindows()
        # elif message[0:3] == b"FRM":
            

            # while True:
            #     message = client_socket.recv(2048)
            #     if message[0:3] == b"FRM":
            #         frame_data_index = message.index(b":",4)
            #         frame_length = int(message[4:frame_data_index].decode())
            #         if frame_length == 0:
            #             break
            #         print(frame_length)
            #         length_captured = len(message) - (frame_data_index + 1)
            #         print(length_captured)
            #         frame_data = message[frame_data_index+1:]
            #         # print(frame_data)
            #         while length_captured < frame_length:
            #             print("Getting frame data...")
            #             data = client_socket.recv(65536)
            #             frame_data += data
            #             length_captured += len(data)
            #         print("Got the frame!")

            #         # print(len(frame_data))

            #         # if frame_length == 0:
            #         #     print("Destroying frames...")
            #         #     cv2.destroyAllWindows()
            #         #     continue
            #         # if frame_length > 0:
            #         frame = pickle.loads(frame_data)
            #         frame = cv2.resize(frame, (1080,720))
            #         cv2.imshow("Edited Video", frame)
            #         if cv2.waitKey(25) & 0xFF == ord('q'):
            #             break
            #         print("Displayed")
            #         # else:
            #         #     break
            # cv2.destroyAllWindows()


            # if cv2.waitKey(25) & 0xFF == ord('q'):
            #     break
            # cv2.destroyAllWindows()

            # frame = client_socket.recv(2048)
            # print(sys.getsizeof(pickle.loads(frame)))
            # print("Received frame :)")

            # while True:
            #     frame = client_socket.recv(2048)
        # client_data = client_socket.recv(2048)
        # global clients
        # clients = pickle.loads(client_data)

        # print("Client name: ", client_name)

        # message = "Hello".encode()
        # public_key = RSA.import_key(clients[client_name])
        # cipher_public = PKCS1_OAEP.new(public_key)
        # ciphertext = cipher_public.encrypt(message)
        # # ciphertext = client_socket.recv(2048)
        # message1 = cipher.decrypt(ciphertext)
        # print("Decrypted message: ", message1.decode())
        # lock_send.release()

    # lock_recv.acquire()
    # while True:
    # lock_send.release()

    # lock_recv.acquire()
    # ciphertext = client_socket.recv(2048)
    # message = cipher.decrypt(ciphertext)
    # print("Decrypted message: ", message.decode())
    # lock_send.release()

send_thread = threading.Thread(target=client_send)
recv_thread = threading.Thread(target=client_recv)

send_thread.start()
recv_thread.start()

send_thread.join()
recv_thread.join()

client_socket.close()
