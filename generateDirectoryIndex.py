from eventlet.green import os
from io import StringIO

def generateDirectoryIndex(dirpath, root_dir):
	current_dir, filenames = dirpath, os.listdir(dirpath)
	output = StringIO()
	output.write(u"<!DOCTYPE html PUBLIC \"-//W3C//DTD HTML 3.2 Final//EN\"><html>")
	output.write(u"<title>Directory index for {0} </title>".format(current_dir))
	output.write(u"<body><h2>Directory index for {0} </h2><hr><ul>".format(current_dir))
	for filename in filenames:
		if os.path.isdir(os.path.join(dirpath, filename)):
			filename += '/'
		output.write(u"<li><a href=\"")
		output.write(filename)
		output.write(u"\">")
		output.write(filename)
		output.write(u"</a>")
	output.write(u"</ul><hr></body></html>")
	return output.getvalue()
