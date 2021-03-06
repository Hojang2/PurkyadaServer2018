from socket import socket, AF_INET, SOCK_STREAM, gaierror
from json import dumps
from time import sleep
manual = {
        "ls": "  Prints all files and directories in current directory",
        "help": "  Shows this help",
        "ssh": """  Secure Shell - connects you to target server 
                    usage ssh <username>@<target_ip>:<target_port>""",
        "cd": """   Change working directory 
                    usage: cd <target>  parametrs: 
                        cd /            - moves you to root directory
                        cd ..            - moves you to directory above 
                        cd <target_directory>    - moves you to target directory
                    errors:  DirectoryDoesNotExist - target directory doesn't exist""",
        "rename": """ change name of file or directory
            usage: rename <input_file.txt> <output_file.txt>""",
        "su": " Change your user to root",
        "exit": """ If you are connected to server you will be disconnect,
                else close the application""",
        "read": "   Read the content of the file",
        "pwd": "    Prints current working directory",
        "submit": "submit some text to server"
}

# Creating structures

############################################


class Directory:

    def __init__(self, name: str, permissions: list,
                 upper_directory, owner):
        self.name = name
        self.owner = owner
        self.path = self.name + "/"
        self.type = "directory"
        self.__content = []
        self.permissions = permissions
        if upper_directory:
            self.upper_directory = upper_directory
        else:
            self.upper_directory = self

    def __str__(self) -> str:
        return self.name

    def add(self, new_content) -> None:
        new_content.path = self.path + new_content.path
        self.__content.append(new_content)

    def check_permission(self, permission: str, index: int) -> bool:
        if permission in self.permissions[index]:
            return True
        else:
            return False

    def validate(self, user, permission: str) -> bool:
        if user.name == self.owner:
            return self.check_permission(permission, 0)
        elif user.name == "root":
            return self.check_permission(permission, 0)
        else:
            return self.check_permission(permission, 2)

    def ls(self, user) -> list:
        if self.validate(user, "r"):
            return self.__content
        else:
            return []


class File:

    def __init__(self, name: str, content: str,
                 permissions: list, owner):
        self.type = "file"
        self.name = name
        self.owner = owner
        self.__content = content
        self.permissions = permissions
        self.path = self.name
        
    def read(self) -> str:
        return self.__content

    def __str__(self) -> str:
        return self.name

##########################
# Client part


class Client:

    def __init__(self, commands, default_directory):
        self.commands = commands
        self.connected = False
        self.port = 0
        self.starter = "{}@{}:{}$"
        self.args = []
        self.action = ""
        self.__password = ""
        self.__sock = None
        self.root_commands = ["show", "shutdown", "kick", "reboot"]

        # Setting default values
        self.data = False
        self.data_send = None
        self.default_directory = default_directory
        self.cwd = default_directory
        self.path = default_directory.path
        self.default_address = "Kali_linux"
        self.address = self.default_address
        self.default_name = "guest"
        self.name = self.default_name

    def sock_init(self):

        self.__sock = socket(AF_INET, SOCK_STREAM)
        return True

    def run(self):
        while True:

            self.action = input(self.starter.format(self.name, self.address, self.path))
            self.action, *self.args = self.action.split(" ")
            if self.action in self.commands.keys() or self.action in self.root_commands:
                if self.connected:
                    self.run_connected()
                else:
                    self.run_local()
            else:
                print("Command not found")

    def connect(self):
        if self.sock_init():
            # Syntax of ssh will be 'ssh username@address:port

            try:
                tmp = self.args[0].split("@")
                name = tmp[0]
                tmp = tmp[1]
                address, port = tmp.split(":")
            except IndexError:
                print("Wrong address and port format")
                address, port, name = None, None, None
            except ValueError:
                print("Wrong address and port format")
                address, port, name = None, None, None

            try:
                self.__sock.connect((address, int(port)))
                print("new connection with {} on port: {}".format(address, port))
                print(self.__sock.recv(4096).decode("utf-8"))  # Prints banner
                self.validate(name, address, port)

            except gaierror:
                print("Wrong address or port")
            except TypeError:
                print("Wrong input after ssh")
            except ValueError:
                print("Port is not number but String")
            except:
                if self.action == "exit":
                    exit()
                print("Something goes wrong")

        else:
            print("Problem with socket initialization")

    def validate(self, name, address, port):
        self.__password = input("password: ")
        self.__sock.send(dumps({"name": name, "password": self.__password}).encode())
        self.data = self.__sock.recv(1024).decode("utf-8")
        if self.data == "True":
            self.connected = True
            self.path = self.__sock.recv(1024).decode("utf-8")
            self.name = name
            self.address = address
            self.port = port
        else:
            print("Invalid username or password")
            self.name = self.default_name
        self.run()

    def run_local(self):
        if self.action == "ssh":
            self.connect()

        elif self.action == "exit":
            exit()

        elif self.action == "help":
            self.show_help()

        elif self.action == "cd":
            self.cd()

        elif self.action == "ls":
            tmp = ""
            for obj in self.cwd.ls(self):
                tmp += obj.name + "\n"
            print(tmp)

        elif self.action == "pwd":
            print(self.path)

        if self.action == "read":
            if len(self.args) == 0:
                self.args = ["None"]
            else:
                self.args = self.args[0]
            tmp = ""
            for obj in self.cwd.ls(self):
                if obj.name == self.args:
                    if obj.type == "file":
                        tmp = obj.read()
                    else:
                        tmp = "Target is directory"
            print(tmp)

    def cd(self):
        if len(self.args) > 0:

            if self.args[0] == "..":

                self.cwd = self.cwd.upper_directory

            elif self.args[0] == "/":

                self.cwd = self.default_directory

            else:
                if len(self.cwd.ls(self)) == 1:
                    self.enter_directory(self.cwd.ls(self)[0])
                else:
                    for obj in self.cwd.ls(self):
                        self.enter_directory(obj)
        else:
            self.cwd = self.default_directory

        self.path = self.cwd.path

    def enter_directory(self, obj):
        if obj.name == self.args[0]:
            if obj.type == "directory":
                self.cwd = obj
            else:
                print("Target is not Directory")

    def show_help(self):
        for key in self.commands:
            print(key + "\t - " + self.commands[key])

    def help_command(self, command):
        print(command + "\t - " + self.commands[command])

    def run_connected(self):
        try:
            if self.action == "help":
                self.show_help()

            elif self.action == "exit":
                self.send_data(dumps({"action": "disconnect", "argv": []}))
                self.receive_data()
                self.disconnect()

            else:
                self.data_send = dumps({"action": self.action, "argv": self.args})
                self.send_data(self.data_send)
                self.receive_data()
                if self.action == "cd":
                    self.path = self.data
                else:
                    print(self.data)
        except ValueError:

            self.disconnect()
            print("Server stop responding disconnected from server")

    def disconnect(self):
        self.__sock.close()
        self.path = self.cwd.path
        self.name = self.default_name
        self.address = self.default_address
        self.connected = False

    def receive_data(self):
        self.data = self.default_directory.path
        try:
            self.data = self.__sock.recv(2048).decode("utf-8")
        except OSError:
            print("Error with receiving data")
            self.disconnect()
        except:
            print("Some error")
            self.disconnect()

    def send_data(self, data: str):
        try:
            if not data:
                data = "nothing"
            sleep(0.1)
            self.__sock.send(data.encode())

        except OSError:
            print("Error with sending data")
            self.disconnect()
        except:
            print("Some error")
            self.disconnect()


message = """Je skvele ze jsi se dostal/la az sem.
Dalsi napoveda jak resit ulohu je na teto strance:
bit.ly/uloha1  Stranka pozaduje heslo,
ktere je uvedeno zde: 01101110 01100101 01110101 01101000 01101111 01100100 01101110 01100101 01110011"""
            
main = Directory("", ["rwx", "rwx", "rwx"], None, "root")
d1 = Directory("home", ["rwx", "rwx", "rwx"], main, "root")
d2 = Directory("Documents", ["rwx", "rwx", "rwx"], d1, "root")
d3 = Directory("Desktop", ["rwx", "rwx", "rwx"], d1, "root")
d4 = Directory(".secret", ["rwx", "rwx", "rwx"], main, "root")
            
d6 = Directory("secret", ["rwx", "rwx", "rwx"], d3, "root")
d8 = Directory("example", ["rwx", "rwx", "rwx"], d3, "root")
d9 = Directory("files", ["rwx", "rwx", "rwx"], d6, "root")
d10 = Directory("something", ["rwx", "rwx", "rwx"], d3, "root")
f0 = File("secret.txt", message, ["rwx", "rwx", "rwx"], "root")
f1 = File("soubor.txt", "Zde nic neni!", ["rwx", "rwx", "rwx"], "root")


main.add(d1)
d2.add(f0)
main.add(d4)
d1.add(d2), d1.add(d3), d3.add(d6), d3.add(d8),
d6.add(d9), d3.add(d10), d4.add(f1)

client = Client(manual, main)
client.run()
