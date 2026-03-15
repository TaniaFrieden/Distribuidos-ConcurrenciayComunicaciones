import os
import pytest
from utils import git, docker, config, scripts, line_parser

CLIENT_CONFIG = {
  'loop_amount' : 500,
  'loop_period' : '150ms'
}

@pytest.fixture(autouse=True, scope='module')
def setup():
  os.chdir(os.environ['REPO_PATH'])
  git.reset_branch()
  git.switch_branch('ej5')
  docker.stop_all()
  docker.prune()
  #Build images only once
  docker.build()

@pytest.fixture(autouse=True)
def beforeEach():
  docker.down()
  git.reset_branch()
  scripts.generate_docker_compose(1)
  config.server(logging_level='DEBUG')
  config.client(**CLIENT_CONFIG)

def test_dni():
  docker.up()
  logs = docker.logs()
  
  sent_dni = ''
  received_dni = ''

  for line in logs:
    print(line, end='')
    msg = line_parser.parse(line)
    if not msg:
      continue

    assert (msg['result'] != line_parser.Result.FAIL), 'No operation should fail'

    if msg['action'] == 'apuesta_enviada':
      sent_dni = msg['dni']
    if msg['action'] == 'apuesta_almacenada':
      received_dni = msg['dni']
    if sent_dni and received_dni:
      break

  assert sent_dni != '', 'There should be a "apuesta_enviada" log present, and it should have a "dni" field'
  assert received_dni != '', 'There should be a "apuesta_almacenada" log present, and it should have a "dni" field'
  assert sent_dni == received_dni, 'Sent and received DNIs must match'
  docker.down()
