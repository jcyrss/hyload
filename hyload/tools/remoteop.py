import paramiko
import sys,os


class RemoteOp:

    def __init__(self,HOST,PORT,USER, PASSWD, SSHKEY):

        print(f'connect to {HOST}:{PORT} ...',end='')

        self.ssh = paramiko.SSHClient()

        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.ssh.load_system_host_keys()

        if SSHKEY:
            self.ssh.load_host_keys(SSHKEY)
            self.ssh.connect(HOST,PORT,username=USER)
        else:
            if PASSWD:
                self.ssh.connect(HOST,PORT,username=USER, password=PASSWD)
            else:
                self.ssh.connect(HOST,PORT,username=USER)

        print('ok')



    def remoteCmd(self, cmd, printCmd=True,printOutput=True):
        if printCmd:
            print(f'$ {cmd}')
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        output = stdout.read().decode('utf8')
        errinfo = stderr.read().decode()
        if printOutput:
            print(output+errinfo)
        return output+errinfo

    def putFile(self, localPath, remotePath):
        print(f'upload {localPath} to {remotePath} ...',end='')
        
        sftp = self.ssh.open_sftp()
        
        sftp.put(localPath, remotePath)
        sftp.close()

        print('ok')

    
    def getFile(self, remotePath, localPath ):
        print(f'download from {remotePath} to {localPath} ...',end='')
        
        sftp = self.ssh.open_sftp()
        
        sftp.get(remotePath,localPath)
        sftp.close()

        print('ok')


def uploadFile(HOST,PORT,USER, PASSWD, SSHKEY, localPath,remotePath):    
    ro = RemoteOp(HOST,PORT,USER, PASSWD, SSHKEY)
    ro.putFile(localPath,
               remotePath)
    
    print('ok')


def uploadFileAndUnGz(HOST,PORT,USER, PASSWD, SSHKEY,localPath,remotePath):    
    ro = RemoteOp(HOST,PORT,USER, PASSWD, SSHKEY)
    ro.putFile(localPath,
               remotePath)

    if '/' in remotePath:
        remoteDir,remoteFile = os.path.split(remotePath);
        cmd = f'cd {remoteDir} && tar zxf {remoteFile}'
    else:
        cmd = f'tar zxf {remotePath}'
    
    print(f'{cmd}')
    ro.remoteCmd(cmd)
    print('ok')




def  downloadFiles(HOST,PORT,USER, PASSWD, SSHKEY,remoteDir,filesStr,localDir):
    os.makedirs(localDir,exist_ok=True)


    ro = RemoteOp(HOST,PORT,USER, PASSWD, SSHKEY)

    # package files 

    out = ro.remoteCmd(f'cd {remoteDir};rm -rf tmp.tar.gz;tar zcvf tmp.tar.gz {filesStr}')

    if 'Exiting with failure' in out:
        return


 

    localFilePath = os.path.join(localDir,'tmp.tar.gz')
    ro.getFile(remoteDir+'/tmp.tar.gz', localFilePath)


    import tarfile
    tar = tarfile.open(localFilePath, "r:gz")
    tar.extractall(localDir)
    tar.close()
    
    print ('ok.')
    
    # unziptool = os.path.join(toolsDir,'7z.exe')
    # 
    # file1 = localDir + os.sep + 'tmp.tar.gz'
    # cmd = f'cd /d {localDir} && {unziptool} x -y {file1}'
    # print (cmd)
    # ret = os.system(cmd)
    # 
    # if ret != 0:
    #     print ("\n!!uncompress gz file failed with 7z.exe, errCode = %s" % ret)
    #     return
    # 
    # file2 = localDir + os.sep + 'tmp.tar'
    # cmd = f'cd /d {localDir} && {unziptool} x -y {file2}'
    # print (cmd)
    # ret = os.system(cmd)
    # 
    # if ret != 0:
    #     print ("\n!!uncompress tar file failed with 7z.exe, errCode = %s" % ret)
    #     return
    # else:
    #     print ('unpackage record file successfully.')
    # 
    # import subprocess
    # subprocess.Popen(rf'explorer "{localDir}"') 
    



def  testSSHConnection_using_password(HOST,PORT,USER, PASSWD):
    
    ssh = paramiko.SSHClient()

    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
   
    ssh.connect(HOST,PORT,username=USER, password=PASSWD, look_for_keys=False)
     
    print('* ssh login ok *')