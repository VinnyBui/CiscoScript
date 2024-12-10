# $language = "Python"
# $interface = "1.0"

def Main():
    while True:
        # Wait for the initial prompt and enter privileged EXEC mode
        crt.Screen.Send("\r")
        crt.Screen.WaitForString("Switch>")
        crt.Screen.Send("\r")
        crt.Screen.Send("enable\r")
        crt.Screen.WaitForString("Switch#")
        crt.Screen.Send("\r")

        # Delete all files from flash
        crt.Screen.Send("format flash:\r")
        for _ in range(6):
            crt.Screen.Send("\r")
        crt.Sleep(1000)

        # crt.Screen.WaitForString("Switch#")

        # # Configure boot system
        # crt.Screen.Send("conf t\r")
        # crt.Screen.WaitForString("Switch(config)#")
        # crt.Screen.Send("boot system flash:/c2960x-universalk9-mz.152-4.E.bin\r")
        # crt.Screen.WaitForString("Switch(config)#")
        # crt.Screen.Send("\r")

        # # Configure interface with DHCP
        # crt.Screen.Send("int fa0\r")
        # crt.Screen.WaitForString("Switch(config-if)#")
        # crt.Screen.Send("ip add dhcp\r")
        # crt.Screen.WaitForString("Switch(config-if)#")
        # crt.Screen.Send("no shut\r")
        # crt.Screen.WaitForString("Switch(config-if)#")
        # crt.Screen.Send(chr(26) + "\r")  # Exit to privileged EXEC mode
        # crt.Screen.WaitForString("%DHCP-6-ADDRESS_ASSIGN:")

        # # Copy IOS image from TFTP server
        # crt.Screen.Send("copy tftp://192.168.0.1/c2960x-universalk9-mz.152-4.E.bin flash:/c2960x-universalk9-mz.152-4.E.bin\r")
        # crt.Screen.WaitForString("Destination filename [c2960x-universalk9-mz.152-4.E.bin]? ")
        # crt.Screen.Send("\r")
        # crt.Screen.WaitForString("Loading c2960x-universalk9-mz.152-4.E.bin")
        # crt.Screen.Send("\r")

        # crt.Screen.WaitForString("#")

        # # Reload the switch
        # crt.Screen.Send("reload\r")
        # crt.Screen.WaitForString("System configuration has been modified. Save? [yes/no]: ")
        # crt.Screen.Send("no\r")
        # crt.Screen.Send("\r")

        # crt.Screen.WaitForString("*")
        # crt.Screen.Send("\r")
        # crt.Screen.WaitForString("Press RETURN to get started!")
        # crt.Screen.Send("\r")

        # # Skip initial configuration dialog
        # crt.Screen.WaitForString("Would you like to enter the initial configuration dialog? [yes/no]:")
        # crt.Screen.Send("no\r")
        # crt.Screen.Send("\r")
        # crt.Screen.WaitForString("Switch>")

        # # Enter diagnostic tests
        # crt.Screen.Send("enable\r")
        # crt.Screen.WaitForString("Switch#")
        # for i in range(1, 7):
        #     crt.Screen.Send(f"diagnostic start switch {i} test all\r")
        # crt.Screen.Send("diagnostic start test all\r")
        # crt.Screen.WaitForString("Do you want to continue? [no]: ")
        # crt.Screen.Send("yes\r")
        # crt.Screen.WaitForString("#")

        # # Erase configuration and prepare for reload
        # crt.Screen.Send("write erase\r")
        # crt.Screen.WaitForString("Erasing the nvram filesystem will remove all configuration files! Continue? [confirm]")
        # crt.Screen.Send("\r")
        # crt.Screen.WaitForString("#")
        # crt.Screen.Send("reload\r")
        # crt.Screen.WaitForString("System configuration has been modified. Save? [yes/no]: ")
        # crt.Screen.Send("no\r")
        # crt.Screen.WaitForString("Proceed with reload? [confirm]")
        # crt.Screen.Send("\r")

        # # Begin logging show commands
        # hostname = "Switch"
        # crt.Session.LogFileName = f"C:\\Running_Capture\\{hostname}.txt"
        # crt.Screen.Send("term length 0\r")
        # crt.Session.Log(True)
        # for cmd in ["show license", "show inventory", "show version", "show env all", "show post"]:
        #     crt.Screen.Send(cmd + "\r")
        #     crt.Screen.WaitForString("#")
        # crt.Session.Log(False)

        # # End of loop
        # crt.Screen.Send("!\r")
        # crt.Sleep(1000)
        # crt.Screen.Send("\r")
        # crt.Screen.WaitForString("#")

Main()
