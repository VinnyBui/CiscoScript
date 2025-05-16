import os
import subprocess
from tkinter import *

# Define the network paths
paths = [
    r"C:\Running_Capture",
    r"\\USER1-PC\ProNetworks\Test Sheet 2",
    r"\\USER1-PC\ProNetworks\Test Sheet",
    r"C:\Users\vinhb\Projects\CiscoScript\sample\ssss"
]

def openFile(event=None):
  serialNumber = input_box.get().strip()
  filename = f"{serialNumber}.txt"
  found = False
  for path in paths:
    full_path = os.path.join(path, filename)
    if os.path.isfile(full_path):
      try:
        subprocess.Popen(['notepad.exe', full_path])
        status_label.config(text=f"Found in path: {path}", fg="green")
        found = True
        break
      except subprocess.CalledProcessError as e:
        status_label.config(text=f"Failed to open {full_path}: {e}", fg="red")
  if not found:
      status_label.config(text=f"{filename} does not exist in any of the specified directories!", fg="red")
  input_box.delete(0, END) #Clears the input field after scanning
  input_box.focus_set()

#Set up GUI
window = Tk()
window.geometry('800x800')
window.title('Find Serial#')
window.config(background="black")

# Label
label = Label(window, text="Scan Serial #", bg="black", fg="white", font=("Arial", 14))
label.pack(padx=20, pady=23)

# Text box for input
input_box = Entry(window, font=("Arial", 12))
input_box.pack()
input_box.focus_set()  # Set focus to the input box

# Bind the Enter key to the fileOpen function
input_box.bind("<Return>", openFile)

# Label to display status messages
status_label = Label(window, text="", bg="black", fg="white", font=("Arial", 12))
status_label.pack(pady=10)

window.attributes('-topmost', True) # Puts the window on top of other apps
window.mainloop()
