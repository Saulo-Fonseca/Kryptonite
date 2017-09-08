#!/usr/bin/env python3
# Author: Saulo Fonseca
# Python version: 3.6.0
# Tcl 8.5 & Tk 8.5 (8.5.15)
# Description: Encrypted text editor
import sys
import os.path
import hashlib
from tkinter import *
from tkinter import messagebox
from tkinter import scrolledtext
from tkinter import filedialog
from threading import Timer

# Function to encrypt / decrpyt
def krypt(string):
	global password
	
	# Create digest of password
	hash = hashlib.new('sha512')
	passwrd = password.get()
	hash.update(passwrd.encode('utf-8'))
	digest = hash.digest()
	
	# Define digestLen to an unexpected value
	sumPass = 0
	for char in passwrd:
		sumPass += ord(char)
	digestLen = len(digest)/2
	digestLen += sumPass % digestLen # Will vary from 32 to 64 bytes

	# Xor each byte of both digest and income string up to digestLen
	# Repeat cropped digest up to income string length
	count = 0;
	krypt = bytearray()
	for char in string:
		xor = char ^ digest[count]
		krypt.append(xor)
		count += 1
		if count == digestLen:
			count = 0
	return krypt

# Start timeout thread that closes the program if inactivity
# reachs 10 minutes (it exists without saving changes)
def resetTimeout(event=None):
	global timeout
	global parent
	if timeout != None:
		timeout.cancel()
	timeout = Timer(10*60,lambda:parent.quit())
	timeout.start()

# Clear text
def clearText():
	global text
	global parent
	global fileName
	global indexSearch
	dialog = None
	fileName = ""
	password.set('')
	text.edit_reset()
	indexSearch = "1.0"
	text.delete('1.0',END)
	parent.title("Kryptonite")
	text.edit_modified(False)

# Set password (let you see it to be sure)
def setPass(event=None):
	global dialog
	global password
	callDialog('Set Password','Set',password,'',closeDiag)
	text.edit_modified(True)

# Read password
def readPass():
	global dialog
	global password
	callDialog('Read Password','Read',password,'*',closeDiag)

# New file
def newFile(event=None):
	global fileName
	global text
	global parent
	if text.edit_modified():
		result = messagebox.askyesnocancel(title='Changes not saved',message='Save changed file?')
		if result == True:
			saveFile()
			if fileName == "":
				return
			clearText()
		elif result == False:
			clearText()
	else:
		clearText()

# Open file dialog
def openDialog(event=None):
	global text
	global fileName

	# Check for modifications on current text
	if text.edit_modified():
		result = messagebox.askyesnocancel(title='Changes not saved',message='Save changed file?')
		if result == True:
			saveFile()
			if fileName == "":
				return
		elif result == None:
			return

	# Open dialog box
	dialogFile = filedialog.askopenfilename(filetypes=[('Kryptonite files', '.krypt'),('all files', '.*')])
	if dialogFile != "":
		clearText()
		fileName = dialogFile
		openFile()

# Open file
def openFile(event=None):
	global text
	global parent
	global fileName
	global password
	
	# Read password
	readPass()
	if password.get() == "":
		return
	
	# Read file in binary and decrypt
	content = open(fileName,'rb').read()
	decrypted = krypt(content)
	
	# Try to decode from utf-8
	try:
		text.insert(INSERT,decrypted.decode('utf-8'))
	except UnicodeDecodeError:
		messagebox.showerror('Error','Wrong Password!')
		clearText()
		return
	
	# Set opened file state
	parent.title(fileName + " - Kryptonite")
	text.edit_reset()
	text.edit_modified(False)

# Save file
def saveFile(event=None):
	global fileName
	global text

	# Check for modifications on current text
	if not text.edit_modified():
		return
	if fileName == "":
		saveFileAs()
		return

	# Enconte UTF-8, encrypt and save in binary
	content = text.get("1.0","end-1c")
	encrypted = krypt(content.encode('utf-8'))
	file = open(fileName,'wb')
	file.write(encrypted)
	file.close()
	text.edit_modified(False)

# Save As
def saveFileAs(event=None):
	global fileName
	global parent
	
	# Ask password if empty
	if password.get() == "":
		setPass()
		if password.get() == "":
			messagebox.showerror('Error','Password cannot be empty.\n\nFile not saved!')
			return

	# Add other fileName to the save() function
	dialogFile = filedialog.asksaveasfilename(defaultextension='.krypt',filetypes=[('Kryptonite files', '.krypt'),('all files', '.*')])
	if dialogFile != "":
		fileName = dialogFile
		parent.title(fileName + " - Kryptonite")
		saveFile()

# Quit the Application
def quit(event=None):
	global parent
	global text

	# Cancel timeout
	if timeout != None:
		timeout.cancel()

	# Check if there are changes
	if text.edit_modified():
		result = messagebox.askyesnocancel(title='Changes not saved',message='Save changed file?')
		if result == True:
			saveFile()
			if fileName == "":
				return
			clearText()
		elif result == None:
			return

	# Quit the application
	parent.quit()

# Undo action
def undo(event=None):
	
	# Because edit_undo() trow an error if there is nothing to undo
	global text
	try:
		text.edit_undo()
	except TclError:
		pass

# Select All
def selectAll(event=None):
	global text
	text.tag_add(SEL,'1.0',END)

# Close dialog
def closeDiag(event=None):
	global dialog
	dialog.destroy()

# Dialog
def callDialog(title,button,stringVar,showStr,function):
	global parent
	global dialog
	
	# Check if there are other opened windows
	if dialog != None:
		closeDiag()

	# Create dialog window
	parent.update_idletasks()
	oldEntry = stringVar.get()
	pos = "+"+str(parent.winfo_x()+100)+"+"+str(parent.winfo_y()+100) # Parent position
	dialog = Toplevel(parent,takefocus=TRUE)
	dialog.title(title)
	dialog.geometry('250x25'+pos)
	dialog.resizable(width=FALSE, height=FALSE)
	dialog.transient(parent) # Put window always on front of parent
	dialog.grab_set()
	dialog.protocol("WM_DELETE_WINDOW",lambda:[stringVar.set(oldEntry),closeDiag()])
	
	# Create field and button
	entry = Entry(dialog,textvariable=stringVar,show=showStr)
	entry.select_range(0,END)
	entry.pack(side=LEFT,fill=X,expand='yes')
	entry.focus_set()
	button = Button(dialog,text=button,command=function)
	button.pack(side=LEFT)
	dialog.wm_attributes("-topmost", 1) # Help force focus on this window
	dialog.focus_force()
	parent.wait_window(dialog)
	dialog.grab_release()

# Find
def find(event=None):
	global indexSearch
	global dialog
	global toSearch
	indexSearch = '1.0'
	callDialog('Find','Find',toSearch,'',findNext)

# Find Next
def findNext(event=None):
	global indexSearch
	global dialog
	global toSearch
	global text
	
	# Destroy the find window
	closeDiag()
	
	# Go back to find() if user not yet informed search string
	if toSearch.get() == "":
		find()
		return

	# Search up to next char
	if indexSearch != '1.0':
		indexSearch += "+1c"

	# Search not case sensitive
	countVar = StringVar()
	indexSearch = text.search(toSearch.get(),indexSearch,nocase=TRUE,count=countVar)
	if indexSearch != "":
		indexEnd = indexSearch+"+"+countVar.get()+"c" # End of searched string
		text.tag_remove(SEL,'1.0',END)         # Remove previous selections
		text.tag_add(SEL,indexSearch,indexEnd) # Select searched string
		text.see(indexSearch)
		text.mark_set('insert',indexSearch)    # Set the cursor position
	else:
		messagebox.showerror('Search','String not found')
		indexSearch = '1.0'

# About
def about(event=None):
	global parent
	string = '''\
Kryptonite version 1.0
	 
Developed by
Saulo Fonseca
(saulo@astrotown.de)
		 
It works like a normal text editor,
but encrypts the saved text with a
custom algorithm based on SHA-512.

This is unhackable!

This software is a freeware.
'''
	messagebox.showinfo('About',string)
		
########## MAIN ##########	
	
# Create parent window
parent = Tk()
parent.title('Kryptonite')
parent.geometry('500x800')

# Create menu
menubar = Menu(parent)
parent.config(menu=menubar)

# File menu
fileMenu = Menu(menubar,tearoff=0)
fileMenu.add_command(label='New',command=newFile)
fileMenu.add_command(label='Open...',command=openDialog)
fileMenu.add_command(label='Save',command=saveFile)
fileMenu.add_command(label='Save As...',command=saveFileAs)
fileMenu.add_separator()
fileMenu.add_command(label='Quit',command=quit)
menubar.add_cascade(label='File',menu=fileMenu)

# Edit menu
editMenu = Menu(menubar,tearoff=0)
editMenu.add_command(label='Undo',command=undo)
editMenu.add_command(label='Select All',command=selectAll)
editMenu.add_command(label='Find...',command=find)
editMenu.add_command(label='Find Next',command=findNext)
editMenu.add_command(label='Change Password...',command=setPass)
menubar.add_cascade(label='Edit',menu=editMenu)

# Help menu
helpMenu = Menu(menubar,tearoff=0)
helpMenu.add_command(label='About Kryptonite',command=about)
menubar.add_cascade(label='?',menu=helpMenu)

# General bindings
parent.bind_all('<Key>',resetTimeout)     # If any key is pressed

# Define protocol
parent.protocol("WM_DELETE_WINDOW", quit)

# Create text widget
text = scrolledtext.ScrolledText(parent,wrap=WORD,undo=TRUE)
text.pack(side=LEFT,fill=BOTH,expand=TRUE)
text.focus_set()
text.edit_modified(False)

# Define global vars
dialog = None
fileName = ""
indexSearch = "1.0"
toSearch = StringVar()
password = StringVar()

# Start timeout
timeout = None
resetTimeout()

# Open file if given as argument
arg = ""
if len(sys.argv) > 1:
	arg = sys.argv[1]
if arg != "":
	if os.path.isfile(arg):
		fileName = arg
		openFile()
	else:
		messagebox.showerror('Error','File %s does not exists' % arg)

# Main loop
parent.mainloop()
