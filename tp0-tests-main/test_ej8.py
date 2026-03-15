import os
import pytest
from utils import git, docker, config
from test_ej7 import test_winners_with_3_clients, test_winners_with_5_clients # Will run the same tests as ej7

CLIENT_CONFIG = {
  'loop_amount' : 500,
  'loop_period' : '150ms',
}

@pytest.fixture(autouse=True, scope='module')
def setup():
  os.chdir(os.environ['REPO_PATH'])
  git.reset_branch()
  git.switch_branch('ej8')
  docker.stop_all()
  docker.prune()
  #Build images only once
  docker.build()

@pytest.fixture(autouse=True)
def beforeEach():
  docker.down()
  git.reset_branch()
  config.server(logging_level='DEBUG')
  config.client(**CLIENT_CONFIG)

  