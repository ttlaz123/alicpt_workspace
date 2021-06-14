import socket
import threading
import sys
import multiprocessing


def client_send(clientMessage = 'Hello!'):
    HOST = '127.0.0.1'
    PORT = 8000
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    print('client send message: %s' % clientMessage)
    client.sendall(clientMessage.encode())

    serverMessage = str(client.recv(1024), encoding='utf-8')
    print('Client received message:', serverMessage)

def server():
    HOST = '127.0.0.1'
    PORT = 8000
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(10)
    print('Status: server is listening\n')
    while True:
        conn, addr = server.accept()
        clientMessage = str(conn.recv(1024), encoding='utf-8')

        print('Server received message:', clientMessage)

        serverMessage = 'I got it'
        print('server send message: %s' % serverMessage)
        conn.sendall(serverMessage.encode())
        conn.close()

if __name__ == '__main__':
    #event = threading.Event()
    job_server = threading.Thread(target=server)
    job_client = threading.Thread(target=client_send)
    #job_server = multiprocessing.Process(target=server)
    #job_client = multiprocessing.Process(target=client_send)
    job_server.start()
    job_client.start()
    '''
    try:
        job_server.start()
        job_client.start()

    except KeyboardInterrupt:
        print('Terminate program')
        #if job_server.is_alive() : job_server.join()
        #if job_client.is_alive() : job_client.join()
        #job_client.terminate()
        #job_server.terminate()
        sys.exit(1)
    #event.set()
    #client_send()
    '''
