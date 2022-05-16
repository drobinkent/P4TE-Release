import os
from socket import socket

import paramiko
import logging
logger = logging.getLogger('SSHDeployer')
hdlr = logging.FileHandler('./log/SSHDeployer.log')
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)


SSH_WAIT_TIME = 400
class SSHDeployer:

    def __init__(self, host, port, username,password,timeout=SSH_WAIT_TIME):
        self.password = password
        self.timeout = timeout
        self.username = username
        self.port = port
        self.host = host
        self.client = None
        self.connect()
        self.isconnected_flag = False

    def close(self):
        try:
            if(self.client != None):
                self.client.close()
                self.isconnected_flag = False
                self.client = None
        except Exception as e:
            logger.info("Exception in closing ssh connection of "+str(self.host))
            logger.info("PYTHON SAYS:"+str(e))


    def connect(self):
        try:
            #Paramiko.SSHClient can be used to make connections to the remote server and transfer files
            logger.info("Establishing ssh connection to "+str(self.host))
            if(self.client == None) or (self.isconnected_flag == False):
                self.client = paramiko.SSHClient()
                #Parsing an instance of the AutoAddPolicy to set_missing_host_key_policy() changes it to allow any host.
                # self.client.load_system_host_keys()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                #Connect to the server
                # if (self.password == ''):
                #     private_key = paramiko.RSAKey.from_private_key_file(self.pkey)
                #     self.client.connect(hostname=self.host, port=self.port, username=self.username, pkey=private_key, timeout=self.timeout, allow_agent=False,look_for_keys=False)
                #     logger.info("Connected to the server",self.host)
                # else:
                #     self.client.connect(hostname=self.host, port=self.port, username=self.username, password=self.password,timeout=self.timeout, allow_agent=False,look_for_keys=False)
                #     logger.info("Connected to the server",self.host)
                self.client.connect(hostname=self.host, username=self.username, password=  self.password, allow_agent=False,look_for_keys=False,timeout=self.timeout)
                self.isconnected_flag = True
        except paramiko.AuthenticationException:
            logger.info("Authentication failed, please verify your credentials")
            self.isconnected_flag = False
        except paramiko.SSHException as sshException:
            logger.info("Could not establish SSH connection: %s" % sshException)
            self.isconnected_flag = False
        except socket.timeout as e:
            logger.info("Connection timed out")
            self.isconnected_flag = False
        except Exception as e:
            logger.info("Exception in connecting to the server")
            logger.info("PYTHON SAYS:"+str(e))
            self.isconnected_flag = False
            self.client.close()

        return self.isconnected_flag

    def executeCommands(self,  commands, hostName = None, startTimerAsString = None):
        self.ssh_output = None
        result_flag = True
        c = ""

        try:

            if self.connect():
                for command in commands:
                    c= command
                    if((startTimerAsString is not None) and (hostName is not None)):
                        command = command + " " + startTimerAsString+ " "+hostName
                    logger.info("Executing command --> {}".format(command))
                    stdin, stdout, stderr = self.client.exec_command(command, timeout=SSH_WAIT_TIME)

            else:
                logger.info("Could not Execute commands because connection is not established")
                result_flag = False
        except paramiko.AuthenticationException:
            logger.info("Authentication failed, please verify your credentials")
        except paramiko.SSHException as sshException:
            logger.into("Could not Execute commands because connection is not established. Reason is  paramiko.SSHException: %s" % sshException)
        except socket.timeout as e:
            logger.info("Could not Execute commands because connection is not established. Reason is Connection timed out")
        except Exception as e:
            logger.info("Exception in connecting to the server")
            logger.info("PYTHON SAYS:"+str(e))

        return result_flag

    def executeCommand(self, command):
        self.ssh_output = None
        result_flag = True
        try:
            if self.connect():
                logger.info("Executing command --> {}".format(command))
                stdin, stdout, stderr = self.client.exec_command(command, timeout=SSH_WAIT_TIME)
                # self.ssh_output = stdout.read()
                # self.ssh_error = stderr.read()
                # if self.ssh_error:
                #     logger.info("Problem occurred while running command:"+ command + " The error is " + self.ssh_error)
                #     result_flag = False
                # else:
                #     logger.info("Command execution completed successfully",command)
                self.client.close()
            else:
                logger.info("Could not establish SSH connection")
                result_flag = False
        except socket.timeout as e:
            logger.info("Command timed out."+ command)
            self.client.close()
            result_flag = False
        except paramiko.SSHException:
            logger.info("Failed to execute the command!"+command)
            self.client.close()
            result_flag = False
        finally:
            self.client.close()
        return result_flag