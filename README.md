# Introduction
I have made this project as a part of the course **CS 348: Computer Networks** at **IIT Dharwad**.
In this project I have created a **socket programming system** in which:
- a server **manages client connections**
- facilitates **secure communication among clients**
- facilitates **video streaming among clients**

**Note:** In order to implement secure communication among clients, I have used **Public key Cryptography**(**RSA algorithm**, to be specific).

# Explanation and program structure
## server.py
- For encryption, we have used **RSA algorithm** implemented in pycryptodome package.

- Creates a thread for every client connected and handles them seperately.

- Structures like dictionaries and frames are **pickled** and then sent to the client.

- When broadcasting dictionaries, we **prefix the pickle object** with byte stream of string `"DICT"` followed by 
name of the client which is either newly connected or is disconnecting.

- When broadcasting messages, we **prefix the ciphertext** received from sending client with byte stream of string `"MSG"` followed by name of the sending client.
**Note:** Length of entire header is 100 but the max length available for name is 90 i.e. the client name can have a maximum of 90 characters.

- On the server side we have videos with **240p**, **720p** and **1080p** resolutions(**1440p** had rendering issues which is a system limitation).

- The directory you access video from is named **Available_videos**. You may change this as per your convenience.

- The list of available videos is sent prefixed with the header `"AVVID"` and before the video frames are sent, `"FRAMES"` string is sent.
This indicates the client that now the video frames would be sent by the server.

### Functions:
`broadcast_dict(client_name)`: Broadcasts the updated dictionary to all the available clients.
`broadcast_client_message(message, client_name)`: Pads the ciphertext received from client with `"MSG"` header and client name and broadcasts it to all the clients.
`extract_frames(video_path)`: Extract all the frames of the video in `video_path`
`get_video_frames(video)`: Select **one-third** of total number of frames from each resolution and **concatenate** them into one video.
`new_client(conn_socket, addr)`: Runs on a thread whenever a new client connects.

### Variables:
`clients`: dictionary to store client name and public key
`client_sockets`: list of all client socket objects

## client.py
- Every client has a sending and a receiving thread.

- **Semaphores** have been used in order to synchronize certain parts of the threads.

- When the client enters name, the public key is directly sent after it as it is already computed when the client is started.

- For each message sent, we **prefix the choice** entered by the user which is checked at the server and then the appropriate action is taken.

- For each of the messages received from server, we need to extract the actual data from it as it has been prefixed by a header.

### Functions:
`client_send()`: This function is run on a thread and is used to send messages to server.
`client_recv()`: This function is run on another thread and is used to receive messages from the server.	

### Variables:
`mykey`: The generated RSA private key
`lock_send, lock_recv`: Semaphores to synchronize sender and receiver threads for some initial message transfers.
`clients`: dictionary to store client name and public key, received from server everytime a client connects or disconnects.
`choice`: Choice of the client (1. Message a client, 2. Video streaming, 3. QUIT)

# Requirements
Python version: 3 and above
In order to install the required packages, execute the following:
```bash
python3 -m venv 210010001
source 210010001/bin/activate
pip3 install sockets
pip3 install pycryptodome
pip3 install opencv-python
```

# Demo instructions
- Open two terminal windows. In one run the server and in another run the client(you can run multiple instances of client if you want).
```bash
python3 210010001_server.py # Terminal 1
```
```bash
python3 210010001_client.py # Terminal 2
```

- Enter the name for each client(public key is sent automatically after that).

- Choose the action on the client side.

- Since there are two threads running parallely, a received message from server might pop up just before your input prompt.
You can nevertheless still input your choice and it would run as expected.

- When trying to stream video, put the name of the video(exclude '_\<resolution\>' eg. '_240') followed by ".mp4"

# Link to demo video
https://drive.google.com/file/d/1N_v8DQpIoDlST5Tz4_09TkmjB3QL2xxM/view?usp=drive_link
