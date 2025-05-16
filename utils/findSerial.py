import os
import subprocess
import tempfile
from tkinter import *

class SerialNumberFinder:
  def __init__(self):
    self.temp_dir = os.path.join(os.environ['TEMP'], "SerialPrints")
    os.makedirs(self.temp_dir, exist_ok=True)
    self.paths = [
      r"C:\Running_Capture",
      r"\\USER1-PC\ProNetworks\Test Sheet 2",
      r"\\USER1-PC\ProNetworks\Test Sheet",
      r"C:\Users\vinhb\Projects\CiscoScript\sample\ssss"
    ]
    self.blocked_keywords = [
      "technical support:", "copyright", "compiled", "gpl",
      "absolutely no warranty", "http://www.gnu.org/licenses/gpl-2.0.html", 
      "rom:", "uptime is", "uptime for this control processor", "system returned",
      "system image file is", "cryptographic", "governing import, export", 
      "delivery of cisco", "term", "third-party authority", "importers, exporters",
      "compliance", "software.", "export@cisco.com", "all rights reserved", 
      "documentation", "url", "reload", "laws",
      "http://www.cisco.com/wwl/export/crypto/tool/stqrg.html", "please",
      "uuu", "u u u", "u  u  u",
    ]
    self.setUpGUI()

  def is_blocked_line(self, line):
    #returns true if line contains ANY of keywords
    line_lower = line.lower()
    return any(keyword.lower() in line_lower for keyword in self.blocked_keywords)

  def print_filtered_content(self, content):
      try:
        # 1. Clean content
        content = (content.replace('\f', '').rstrip().replace('\x0c', '').rstrip())
        # Remove empty lines and whitespace-only lines
        non_empty_lines = [line for line in content.splitlines() if line.strip()]
        # Apply 100-line limit
        if len(non_empty_lines) > 100:
          non_empty_lines = non_empty_lines[:100]
          non_empty_lines.append("[TRUNCATED TO 100 LINES]")
        # Rebuild content
        filtered_content = "\n".join(non_empty_lines)

        # Create temp file in system temp directory
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', prefix='Filtered_', dir=self.temp_dir, encoding='utf-8',delete=False) as temp_file:
          temp_file.write(filtered_content)
          temp_path = temp_file.name
        
        # Print using Notepad's print command (/p flag)
        subprocess.Popen([
          'notepad.exe',
          '/p',
          temp_path
        ], shell=True)
        return True
      except Exception as e:
        self.status_label.config(text=f"Print error: {str(e)}", fg="red")
        return False

  def openFile(self, event=None):
    serialNumber = self.input_box.get().strip()
    found = False
    for path in self.paths:
      if not os.path.exists(path):
        continue
      for filename in os.listdir(path):
        if serialNumber in filename and filename.endswith('.txt'):
          full_path = os.path.join(path, filename)
          try:
            # Read and filter content
            with open(full_path, 'r', encoding='utf-8') as file:
              printable_content = [
                line for line in file 
                if not self.is_blocked_line(line)
              ]
            
            if printable_content:
              if self.print_filtered_content("".join(printable_content)):
                self.status_label.config(text=f"Printing: {filename}", fg="green")
                found = True
                break
          except Exception  as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")

    if not found:
      self.status_label.config(text=f"No matches for '{serialNumber}'", fg="red")

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
    self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    self.window.mainloop()

  def on_close(self):
    """Cleanup handler when window closes"""
    try:
      for f in os.listdir(self.temp_dir):
        if f.startswith('Filtered_'):
          os.remove(os.path.join(self.temp_dir, f))
    except Exception as e:
      print(f"Cleanup warning: {e}")
    self.window.destroy()

if __name__ == "__main__":
  app = SerialNumberFinder()