import os
from io import StringIO

def generateDirectoryIndex(dirpath):
	current_dir, filenames = dirpath, os.listdir(dirpath)
	output = StringIO()
	output.write("<!DOCTYPE html PUBLIC \"-//W3C//DTD HTML 3.2 Final//EN\"><html>")
	output.write("<title>Directory index for {0} </title>".format(current_dir))
	output.write("<body><h2>Directory index for {0} </h2><hr><ul>".format(current_dir))
	for filename in filenames:
		if os.path.isdir(os.path.join(dirpath, filename)):
			filename += '/'
		output.write("<li><a href=\"")
		output.write(filename)
		output.write("\">")
		output.write(filename)
		output.write("</a>")
	output.write("</ul><hr></body></html>")
	return output.getvalue()