import eventlet
from eventlet.green import os 
from eventlet.green import socket
from eventlet.green.time import gmtime, strftime
from eventlet.green.urllib import parse
import dicts
from generateDirectoryIndex import generateDirectoryIndex

def RespondNotSupported(client):
    http_response = 'HTTP/1.1 ' + dicts.responseCodes['405'] + '\r\n'
    http_response += 'Date: {date}\r\n'.format(date=strftime("%a, %d %b %Y %X GMT", gmtime()))
    http_response += 'Server: TPHW\r\n'
    http_response += '\r\n'
    client.sendall(http_response.encode())


def Respond404(client):
    f = open("404.html", 'r')
    http_response = 'HTTP/1.1 ' + dicts.responseCodes['404'] + '\r\n'
    http_response += 'Date: {date}\r\n'.format(date=strftime("%a, %d %b %Y %X GMT", gmtime()))
    http_response += 'Server: TPHW\r\n'
    http_response += 'Content-Length: {0}\r\n'.format(os.stat("404.html").st_size)
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


def RespondHead(client, file):
    path = os.getcwd() + parse.unquote(file)
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
            Respond404(client)
        except IOError:
            print("File not found on " + path)
            Respond404(client)
    elif (os.path.isdir(path) or ("index.html" in str(path))):
        try:
            f = open(os.path.join(path, 'index.html'), 'r')
        except PermissionError:
            print("Permission error on " + path)
            Respond404(client)
        except IOError:
            print("File not found on " + path)
            filteredPath = os.path.dirname(path)
            f = generateDirectoryIndex(filteredPath)
            http_response = 'HTTP/1.1 200 OK\r\n'
            http_response += 'Date: {date}\r\n'.format(date=strftime("%a, %d %b %Y %X GMT", gmtime()))
            http_response += 'Server: TPHW\r\n'
            http_response += 'Content-Length: {0}\r\n'.format(len(f))
            http_response += 'Content-Type: {0}\r\n'.format("text/html")
            http_response += '\r\n'
            client.sendall(http_response.encode())
    else:
        Respond404(client)
    return f
    
#TODO

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
    print('{date}: Connection closed'.format(date=strftime("%a, %d %b %Y %X GMT", gmtime())))

server = eventlet.listen(('0.0.0.0', 8080))
pool = eventlet.GreenPool(10000)
while True:
    new_sock, address = server.accept()
    pool.spawn_n(handle, new_sock)
