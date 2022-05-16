Evaluation

Setup: 

1) copying id-rsa
2) sshd co fig file backup
3) ssh login to each host and deply the taska
4) ctrlr collext statistica

Using sshd requires a small bit of configuration, if ssh for the root user has not been set up already. 
We must first run ssh-keygen, which creates the directory /root/.ssh and then the public and private key 
files, id_rsa.pub and id_rsa respectively. There is no need, in this setting, to protect the keys with a 
password. The second step is to go to the .ssh directory and copy id_rsa.pub to the (new) file 
authorized_keys (if the latter file already exists, append id_rsa.pub to it). This will allow 
passwordless ssh connections between the different Mininet hosts.

Ctrlr statia tics'

1) fct 
2) each path packet sending rate
3) counter based path utilization rate
4) 