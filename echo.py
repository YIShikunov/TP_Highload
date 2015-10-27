import eventlet
from eventlet.green import os 
from eventlet.green import socket
from eventlet.green.time import gmtime, strftime
import dicts

def RespondWithTestFile(client):
	print('{date}: Client Connected'.format(date=strftime("%a, %d %b %Y %X GMT", gmtime())))
	f = open("1.txt", 'r')
	
	http_response = 'HTTP/1.1 200 OK\r\n'
	http_response += 'Date: {date}\r\n'.format(date=strftime("%a, %d %b %Y %X GMT", gmtime()))
	http_response += 'Content-Length: {0}\r\n'.format(os.stat("1.txt").st_size)
	http_response += 'Content-Type: text/plain\r\n'
	http_response += 'Content-Encoding: utf-8\r\n'
	http_response += '\r\n'
	client.sendall(http_response.encode())

	offset = 0
	while True:
		sent = os.sendfile(client.fileno(), f.fileno(), offset, 4096)
		if sent <= 0:
			break
		offset += sent
	f.close()
	client.shutdown(socket.SHUT_RDWR)
	client.close()
	print('{date}: Connection closed'.format(date=strftime("%a, %d %b %Y %X GMT", gmtime())))


def handleS(client):
	print("Client connected")
	s = client.recv(10000)
	headers = str(s).split("\\r\\n")
	if "GET" in headers[0]:
		print(headers)
	client.sendall(s)
	client.shutdown(socket.SHUT_RDWR)
	client.close()

server = eventlet.listen(('0.0.0.0', 8080))
pool = eventlet.GreenPool(10000)
while True:
    new_sock, address = server.accept()
    pool.spawn_n(handleS, new_sock)


