import eventlet
from eventlet.green import os 
from eventlet.green import socket
from eventlet.green.time import gmtime, strftime
from eventlet.green.urllib import parse
import argparse
import sys
import dicts
from generateDirectoryIndex import generateDirectoryIndex

def RespondNotSupported(client):
    http_response = 'HTTP/1.1 ' + dicts.responseCodes['405'] + '\r\n'
    http_response += 'Date: {date}\r\n'.format(date=strftime("%a, %d %b %Y %X GMT", gmtime()))
    http_response += 'Server: TPHW\r\n'
    http_response += '\r\n'
    client.sendall(http_response.encode())


def Respond404(client, code:str):
    path404 = os.path.join(proc_dir, "404.html")
    f = open(path404, 'r')
    http_response = 'HTTP/1.1 ' + dicts.responseCodes['404'] + '\r\n'
    http_response += 'Date: {date}\r\n'.format(date=strftime("%a, %d %b %Y %X GMT", gmtime()))
    http_response += 'Server: TPHW\r\n'
    http_response += 'Content-Length: {0}\r\n'.format(os.stat(path404).st_size)
    http_response += 'Content-Type: {0}\r\n'.format(dicts.contentTypes['html'])
    http_response += '\r\n'
    client.sendall(http_response.encode())

    offset = 0
    while True:
        sent = os.sendfile(client.fileno(), f.fileno(), offset, 4096)
        if sent <= 0:
            break
        offset += sent
    f.close()


def RespondHead(client, file:str):
    filepath = file.split('?')
    path = os.getcwd() + parse.unquote(filepath[0])
    print("requesting file: " + str(path))
    f = None
    if (os.path.isfile(path)):
        try:
            f = open(path, 'r')
            http_response = 'HTTP/1.1 200 OK\r\n'
            http_response += 'Date: {date}\r\n'.format(date=strftime("%a, %d %b %Y %X GMT", gmtime()))
            http_response += 'Server: TPHW\r\n'
            http_response += 'Content-Length: {0}\r\n'.format(os.stat(path).st_size)
            http_response += 'Content-Type: {0}\r\n'.format(dicts.contentTypes.get(path.split(".")[-1], 'application/octet-stream'))
            http_response += '\r\n'
            client.sendall(http_response.encode())
        except PermissionError:
            print("Permission error on " + path)
            Respond404(client, '403')
        except IOError:
            print("File not found on " + path)
            Respond404(client,'404')
    elif (os.path.isdir(path)):
        try:
            f = open(os.path.join(path, 'index.html'), 'r')
            http_response = 'HTTP/1.1 200 OK\r\n'
            http_response += 'Date: {date}\r\n'.format(date=strftime("%a, %d %b %Y %X GMT", gmtime()))
            http_response += 'Server: TPHW\r\n'
            http_response += 'Content-Length: {0}\r\n'.format(os.stat(path).st_size)
            http_response += 'Content-Type: {0}\r\n'.format(dicts.contentTypes.get(path.split(".")[-1], 'application/octet-stream'))
            http_response += '\r\n'
            client.sendall(http_response.encode())
        except PermissionError:
            print("Permission error on " + path)
            Respond404(client, '403')
        except IOError:
            print("File not found on " + path)
            #filteredPath = os.path.dirname(path)
            #f = generateDirectoryIndex(filteredPath, os.getcwd())
            Respond404(client, '403')
    else:
        Respond404(client, '404')
    return f
    
def RespondWithFile(client, file):
    if (type(file) is str):
        client.sendall(file.encode())
    else:
        offset = 0
        while True:
            sent = os.sendfile(client.fileno(), file.fileno(), offset, 4096)
            if sent <= 0:
                break
            offset += sent
        file.close()

def handle(client):
    print('{date}: Client Connected'.format(date=strftime("%a, %d %b %Y %X GMT", gmtime())))
    s = client.recv(10000)
    headers = s.decode().split("\r\n")
    request = headers[0].split(' ')
    print(request)
    file = None
    if request[0] not in dicts.supportedRequests:
        RespondNotSupported(client)
    else:
        file = RespondHead(client, request[1])
    if (("GET" in headers[0]) and (file is not None)):
        RespondWithFile(client, file)
    client.shutdown(socket.SHUT_RDWR)
    client.close()
    print('{date}: Connection Closed'.format(date=strftime("%a, %d %b %Y %X GMT", gmtime())))

def main():
    parser = argparse.ArgumentParser(description='Python Web Server')
    parser.add_argument('-p', type = int, help = 'Port Number', default = 8080)
    parser.add_argument('-r', type = str, help = 'Document Root Path', default = os.getcwd())
    parser.add_argument('-c', type = int, help='CPU Number', default = 1)
    parser.add_help = True
    args = vars(parser.parse_args())
    port = args['p']
    cpus = args['c']
    os.chroot(args['r'] or os.getcwd())
    print("Starting server on port: ", port)
    server = eventlet.listen(('0.0.0.0', port), backlog = 100)

    for i in range(cpus):
        pid = os.fork()
        # os.fork() returns 0 in the child process and the child's
        # process id in the parent. So if pid == 0 then we're in
        # the child process.
        if pid == 0:
            pool = eventlet.GreenPool(10000)
            childpid = os.getpid()
            print('Started the Fork with PID: {0}'.format(childpid))
            try:
                while True:
                    new_sock, address = server.accept()
                    pool.spawn_n(handle, new_sock)
            except KeyboardInterrupt:
                print('Exiting the Child Process')
                sys.exit()
    try:
        os.waitpid(-1, 0)
    except KeyboardInterrupt:
        print('Killing the Server')
        sys.exit()

if __name__ == '__main__':
    proc_dir = os.getcwd()
    main()
