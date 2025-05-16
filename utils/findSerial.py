import os
import subprocess
from tkinter import *

class SerialNumberFinder:
  def __init__(self):
    self.paths = [
        r"C:\Running_Capture",
        r"\\USER1-PC\ProNetworks\Test Sheet 2",
        r"\\USER1-PC\ProNetworks\Test Sheet",
        r"C:\Users\vinhb\Projects\CiscoScript\sample\ssss"
    ]
    self.window = None
    self.input_box = None
    self.status_label = None
    self.setUpGUI()

  def openFile(self, event=None):
    serialNumber = self.input_box.get().strip()
    filename = f"{serialNumber}.txt"
    found = False
    for path in self.paths:
      full_path = os.path.join(path, filename)
      if os.path.isfile(full_path):
        try:
          subprocess.Popen(['notepad.exe', full_path])
          self.status_label.config(text=f"Found in path: {path}", fg="green")
          found = True
          break
        except subprocess.CalledProcessError as e:
          self.status_label.config(text=f"Failed to open {full_path}: {e}", fg="red")
    if not found:
      self.status_label.config(text=f"{filename} not found in any directory!", fg="red")
    self.input_box.delete(0, END)
    self.input_box.focus_set()

  def setUpGUI(self):
    self.window = Tk()
    self.window.geometry('600x400')  # More reasonable size
    self.window.title('Serial Number Finder')
    self.window.config(background="black")

    # Title label
    Label(
      self.window, 
      text="Scan Serial #", 
      bg="black", 
      fg="white", 
      font=("Arial", 14)
    ).pack(padx=20, pady=20)

    # Input box
    self.input_box = Entry(self.window, font=("Arial", 12))
    self.input_box.pack()
    self.input_box.focus_set()
    self.input_box.bind("<Return>", self.openFile)

    # Status label (NOW PROPERLY ASSIGNED)
    self.status_label = Label(
      self.window, 
      text="", 
      bg="black", 
      fg="white", 
      font=("Arial", 12)
    )
    self.status_label.pack(pady=10)

    self.window.attributes('-topmost', True)
    self.window.mainloop()

if __name__ == "__main__":
  app = SerialNumberFinder()