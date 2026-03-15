import os
import pytest
from utils import git, docker, config, scripts, line_parser

CLIENT_CONFIG = {
  'loop_amount' : 500,
  'loop_period' : '150ms',
}

def generate_agency_file(filename, register_amount):
  os.makedirs(os.path.dirname(f'{os.environ["REPO_PATH"]}/.data'), exist_ok=True)
  with open(f'{os.environ["REPO_PATH"]}/.data/{filename}', "w+") as file:
    for i in range(register_amount):
      file.write(f'A,B,{str(i).zfill(8)},2000-01-01,{i}\n')

@pytest.fixture(autouse=True, scope='module')
def setup():
  os.chdir(os.environ['REPO_PATH'])
  git.reset_branch()
  git.switch_branch('ej6')
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

def _test_bet_amount(bets_amount):
  generate_agency_file("agency-1.csv", bets_amount)
  docker.up()
  docker.wait_for_clients(1)
  logs = docker.logs(follow=False)
  received_bets_amount = 0
  for line in logs:
    print(line, end='')
    msg = line_parser.parse(line)
    if not msg:
      continue

    assert (msg['result'] != line_parser.Result.FAIL), 'No operation should fail'

    if msg['action'] == 'apuesta_recibida':
      received_bets_amount += int(msg['cantidad'])

  assert received_bets_amount == bets_amount, 'All bets should have been received'
  docker.down()

def _test_batch_bet_grouping(bets_amount, batch_amount):
  config.client(max_amount=batch_amount)
  generate_agency_file("agency-1.csv", bets_amount)
  docker.up()
  docker.wait_for_clients(1)
  logs = docker.logs(follow=False)
  received_bets_amount = 0
  for line in logs:
    print(line, end='')
    msg = line_parser.parse(line)
    if not msg:
      continue

    assert (msg['result'] != line_parser.Result.FAIL), 'No operation should fail'

    if msg['action'] == 'apuesta_recibida':
      batch_bets_amount = int(msg['cantidad'])
      received_bets_amount += batch_bets_amount
      assert  batch_bets_amount == batch_amount or bets_amount == received_bets_amount, 'Only the last batch could contain less bets than the max amount specified in the config file'

  assert received_bets_amount == bets_amount, 'All bets should have been received'
  docker.down()

def test_bet_amount_A():
  _test_bet_amount(64)

def test_bet_amount_B():
  _test_bet_amount(99)

def test_bet_batch_grouping_total_divisible_by_batch_amount():
  _test_batch_bet_grouping(16, 64)

def test_bet_batch_grouping_total_not_divisible_by_batch_amount():
  _test_batch_bet_grouping(21, 99)