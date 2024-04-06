from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from socket import *
import threading
import pickle
import cv2
import os
import sys
import struct

try:
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    print("Server Socket created!")
except:
    print("Error creating socket")

server_port = 8000

server_socket.bind(("", server_port))
server_socket.listen(10)
print("Server listening...")

clients = {}    # dictionary to store client name and public key
client_sockets = [] # List of all client socket objects

def broadcast_dict():
    client_data = pickle.dumps(clients)
    for socket in client_sockets:
        socket.send("DICT".encode() + client_data)

def broadcast_client_message(message, client_name):
    for socket in client_sockets:
        header = "MSG:From:" + client_name
        nextra = 100 - len(header)
        header = header + "\0" * nextra     # An extra header buffer for a message put by server so that name of sender can be passed
        socket.send(header.encode() + message)

def extract_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames

def get_video_frames(video):
    # Paths to video files
    # video_paths = ["Videos/Beach_240.mp4", "Videos/Beach_720.mp4", "Videos/Beach_1080.mp4"]
    video_paths = ["Available_videos/"+video+"_240.mp4", "Available_videos/"+video+"_720.mp4", "Available_videos/"+video+"_1080.mp4"]

    # Extract frames from each video
    extracted_frames = []
    for video_path in video_paths:
        frames = extract_frames(video_path)
        extracted_frames.append(frames)

    # print(len(extracted_frames), len(extracted_frames[0]), len(extracted_frames[1]), len(extracted_frames[2]))  # ME

    # Calculate number of frames in one-third of each video
    total_frames = min(len(frames) for frames in extracted_frames)
    one_third_frames = total_frames // 3
    # print("One-third = ", one_third_frames)

    # Select frames for the edited video
    selected_frames = []
    # for frames in extracted_frames:
    selected_frames.extend(extracted_frames[0][:one_third_frames])
    selected_frames.extend(extracted_frames[1][one_third_frames:2*one_third_frames])
    selected_frames.extend(extracted_frames[2][2*one_third_frames:])
    
    print("Appropriate frames are selected")   # ME
    # print(len(selected_frames), len(selected_frames[0]))

    # for frame in selected_frames:
    #     frame = cv2.resize(frame, (1080,720))
    #     cv2.imshow("Edited Video", frame)
    #     if cv2.waitKey(25) & 0xFF == ord('q'):
    #         break
    # cv2.destroyAllWindows()

    # frames_data = pickle.dumps(selected_frames)
    # return frames_data
    return selected_frames

def new_client(conn_socket, addr):
    client_sockets.append(conn_socket)

    conn_socket.send("Enter your name:".encode())
    client_name = conn_socket.recv(2048).decode()
    print("Client name: ", client_name)

    conn_socket.send("Enter the public key:".encode())
    key = conn_socket.recv(2048)
    # public_key = RSA.import_key(key)
    print("Received client public key")
    # Q1a done----------------------------------------------------------

    clients[client_name] = key  # key is of type 'bytes'
    # print(clients)              # Broadcasting dictionary correctly. Commenting this print()
    # Q1b done----------------------------------------------------------

    broadcast_dict()

    while True:
        # print("Your choice?")
        client_msg = conn_socket.recv(2048)
        # print("Choice:", choice)
        if client_msg[:4] == b"QUIT":
            print("\nClient", client_name, "exited.\n")
            del clients[client_name]
            if len(clients) > 0:    # broadcast dictionary only if there is any client present
                print("\nBroadcasting updated dictionary...")
                broadcast_dict()
                print("Broadcasted successfully!\n")
            client_sockets.remove(conn_socket)  # discard the socket of the client which exited
            conn_socket.close()
            break
        elif client_msg[:1] == b"1":
            # message = conn_socket.recv(2048)
            print("\nReceived message to be broadcasted from client:", client_name)
            broadcast_client_message(client_msg[1:], client_name)
            print("Message broadcasted successfully")
        elif client_msg[:1] == b"2":
            print("List of available videos:")
            message = "AVVID:\nList of available videos:\n"
            files = os.listdir("Available_videos")
            for file in files:
                print(file)
                message += file+'\n'
            message += "\nWhich video would you like to see?\n"
            message = conn_socket.send(message.encode())
            video = conn_socket.recv(2048).decode()
            print("\nClient wants to play:", video)
            video = video[:video.index(".")]
            # frames = get_video_frames(video)
            # frame_data = pickle.dumps(frames)
            # frame_length = sys.getsizeof(frame_data)
            # conn_socket.send(b"FRM:"+str(frame_length).encode()+b":"+frame_data)

            video_paths = ["Available_videos/"+video+"_240.mp4", "Available_videos/"+video+"_720.mp4", "Available_videos/"+video+"_1080.mp4"]

            # Extract frames from each video
            extracted_frames = []
            for video_path in video_paths:
                frames = extract_frames(video_path)
                extracted_frames.append(frames)

            # print(len(extracted_frames), len(extracted_frames[0]), len(extracted_frames[1]), len(extracted_frames[2]))  # ME

            # Calculate number of frames in one-third of each video
            total_frames = min(len(frames) for frames in extracted_frames)
            one_third_frames = total_frames // 3
            # print("One-third = ", one_third_frames)

            # Select frames for the edited video
            selected_frames = []
            # for frames in extracted_frames:
            selected_frames.extend(extracted_frames[0][:one_third_frames])
            selected_frames.extend(extracted_frames[1][one_third_frames:2*one_third_frames])
            selected_frames.extend(extracted_frames[2][2*one_third_frames:])
            
            print("Appropriate frames are selected")

            # for frame in selected_frames:
            #     frame = cv2.resize(frame, (1080,720))
            #     cv2.imshow("Edited Video", frame)
            #     if cv2.waitKey(25) & 0xFF == ord('q'):
            #         break
            # cv2.destroyAllWindows()

            conn_socket.send(b"FRAMES")

            for i in range(0, len(selected_frames)):
                frame_data = pickle.dumps(selected_frames[i])
                message_size = struct.pack("L", len(frame_data))
                conn_socket.sendall(message_size + frame_data)
            message_size = struct.pack("L", 0)
            conn_socket.send(message_size)
                # conn_socket.send(b"FRM:" + str(len(frame_data)).encode() + b":" + frame_data)
            # conn_socket.send(b"FRM:0:")
            print("Sent zero frame")

            # for frame in frames:
            #     frame_data = pickle.dumps(frame)
            #     conn_socket.send(b"FRM"+frame_data)

    
    # message = "Hello".encode()
    # public_key = RSA.import_key(clients[addr][1])
    # cipher = PKCS1_OAEP.new(public_key)
    # ciphertext = cipher.encrypt(message)

    # conn_socket.send(ciphertext)

    # conn_socket.close()

while(True):
    new_conn, addr = server_socket.accept()

    print("\nNew client connected\nAddress: ", addr, "\n")
    threading.Thread(target=new_client, args=(new_conn, addr)).start()

    
