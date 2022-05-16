from socket import socket

import paramiko
import logging
logger = logging.getLogger('SSHDeployer')
hdlr = logging.FileHandler('../log/SSHDeployer.log')
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

class SSHDeployer:

    def __init__(self, host, port, username,password,timeout=10):
        self.password = password
        self.timeout = timeout
        self.username = username
        self.port = port
        self.host = host

    def connect(self):
        try:
            #Paramiko.SSHClient can be used to make connections to the remote server and transfer files
            print("Establishing ssh connection")
            self.client = paramiko.SSHClient()
            #Parsing an instance of the AutoAddPolicy to set_missing_host_key_policy() changes it to allow any host.
            #self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            #Connect to the server
            # if (self.password == ''):
            #     private_key = paramiko.RSAKey.from_private_key_file(self.pkey)
            #     self.client.connect(hostname=self.host, port=self.port, username=self.username, pkey=private_key, timeout=self.timeout, allow_agent=False,look_for_keys=False)
            #     print("Connected to the server",self.host)
            # else:
            #     self.client.connect(hostname=self.host, port=self.port, username=self.username, password=self.password,timeout=self.timeout, allow_agent=False,look_for_keys=False)
            #     print("Connected to the server",self.host)
            self.client.connect(hostname=self.host, username=self.username, password=  self.password, allow_agent=False,look_for_keys=False)
        except paramiko.AuthenticationException:
            logger.info("Authentication failed, please verify your credentials")
            isconnected_flag = False
        except paramiko.SSHException as sshException:
            print("Could not establish SSH connection: %s" % sshException)
            isconnected_flag = False
        except socket.timeout as e:
            print("Connection timed out")
            isconnected_flag = False
        except Exception as e:
            print("Exception in connecting to the server")
            print("PYTHON SAYS:",e)
            isconnected_flag = False
            self.client.close()
        else:
            isconnected_flag = True
        return isconnected_flag

    def executeCommands(self,  commands, hostName = None, startTimerAsString = None):
        self.ssh_output = None
        result_flag = True
        try:
            if self.connect():
                for command in commands:
                    if((startTimerAsString is not None) and (hostName is not None)):
                        command = command + " " + startTimerAsString+ " "+hostName
                    print("Executing command --> {}".format(command))
                    stdin, stdout, stderr = self.client.exec_command(command)
                    # self.ssh_output = stdout.read()
                    # self.ssh_error = stderr.read()
                    # if self.ssh_error:
                    #     print("Problem occurred while running command:"+ command + " The error is " + self.ssh_error)
                    #     result_flag = False
                    # else:
                    #     print("Command execution completed successfully",command)
            else:
                print("Could not establish SSH connection")
                result_flag = False
            self.client.close()
            print("connection closed")
        except Exception as e :
            print("Failed to execute the command!",command)
            print("Exceptio is ",str(e))
            self.client.close()
            result_flag = False

        return result_flag

    def executeCommand(self, command):
        self.ssh_output = None
        result_flag = True
        try:
            if self.connect():
                print("Executing command --> {}".format(command))
                stdin, stdout, stderr = self.client.exec_command(command)
                # self.ssh_output = stdout.read()
                # self.ssh_error = stderr.read()
                # if self.ssh_error:
                #     print("Problem occurred while running command:"+ command + " The error is " + self.ssh_error)
                #     result_flag = False
                # else:
                #     print("Command execution completed successfully",command)
                self.client.close()
            else:
                print("Could not establish SSH connection")
                result_flag = False
        except socket.timeout as e:
            print("Command timed out.", command)
            self.client.close()
            result_flag = False
        except paramiko.SSHException:
            print("Failed to execute the command!",command)
            self.client.close()
            result_flag = False
        return result_flag