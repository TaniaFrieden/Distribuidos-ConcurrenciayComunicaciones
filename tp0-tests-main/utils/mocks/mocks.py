import os
from utils import shell_cmd
from utils.docker import DockerException

def chdir():
  os.chdir(os.path.dirname(__file__))

def healthy_server_up():
    return_code = shell_cmd.silent('docker compose -f docker-compose-mock.yaml --profile healthy up -d')
    if (return_code != 0):
      raise DockerException('Can\'t start system')
    
def unhealthy_server_up():
    return_code = shell_cmd.silent('docker compose -f docker-compose-mock.yaml --profile unhealthy up -d')
    if (return_code != 0):
      raise DockerException('Can\'t start system')
    
def healthy_server_down():
    return_code = shell_cmd.silent('docker compose -f docker-compose-mock.yaml --profile healthy down')
    if (return_code != 0):
      raise DockerException('Can\'t stop system')
    
def unhealthy_server_down():
    return_code = shell_cmd.silent('docker compose -f docker-compose-mock.yaml --profile unhealthy down')
    if (return_code != 0):
      raise DockerException('Can\'t stop system')