
def run(connection):
    try:
        output = connection.send_command("enable")
        print(output)

    except Exception as e:
        print(f"Error running test command: {e}")