
def main():
  session_names = [
    "testCOM1",
    "testCOM4",
    "testCOM5"
  ]
  for session in session_names:
    crt.Session.ConnectInTab("/S " + session)
    crt.Sleep(100)  # Optional: Add a short delay to avoid rapid execution

  # Optionally, activate the first tab after opening all sessions
  crt.GetTab(1).Activate()

main()
