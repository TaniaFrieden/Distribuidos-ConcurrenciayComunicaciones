import os
import pytest
from utils import git, docker, config, scripts, line_parser

CLIENT_CONFIG = {
  'loop_amount' : 500,
  'loop_period' : '150ms',
}

WINNING_NUMBER = 7574

def make_id(i):
  return str(i).zfill(8)

def generate_agency_file(filename, register_amount, winners):
  os.makedirs(os.path.dirname(f'{os.environ["REPO_PATH"]}/.data'), exist_ok=True)
  with open(f'{os.environ["REPO_PATH"]}/.data/{filename}', "w+") as file:
    for i in range(register_amount):
    
      if i in winners:
        number = WINNING_NUMBER
      else:
        number = i if i < WINNING_NUMBER else i + 1
        
      file.write(f'Name,Surname,{make_id(i)},2000-01-01,{number}\n')

@pytest.fixture(autouse=True, scope='module')
def setup():
  os.chdir(os.environ['REPO_PATH'])
  git.reset_branch()
  git.switch_branch('ej7')
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

def _test_winners(client_amount, bets_per_client):
  winners = {}
  received_bets_amount = 0

  docker.wait_for_clients(client_amount) # Ensure all clients have finished
  logs = docker.logs(follow=False) # Fetch all logs

  for line in logs:
    print(line, end='')
    msg = line_parser.parse(line)
    if not msg:
      continue
    assert msg['result'] != line_parser.Result.FAIL, 'No operation should fail'
    if msg['action'] == 'apuesta_recibida':
      received_bets_amount += int(msg['cantidad'])
    elif msg['action'] == 'consulta_ganadores' and msg['result'] == line_parser.Result.SUCCESS:
      winners[msg['source']] = int(msg['cant_ganadores'])

  assert len(winners) == client_amount, 'Did not capture all winners logs'
  assert received_bets_amount == client_amount*bets_per_client, 'All bets should have been received'
  return winners

def test_winners_with_3_clients():
  CLIENT_AMOUNT = 3
  BETS_PER_CLIENT = 100
  
  scripts.generate_docker_compose(client_amount=CLIENT_AMOUNT)
  generate_agency_file("agency-1.csv", BETS_PER_CLIENT, [0,99])
  generate_agency_file("agency-2.csv", BETS_PER_CLIENT, [50])
  generate_agency_file("agency-3.csv", BETS_PER_CLIENT, [])
  docker.up()
  
  winners = _test_winners(CLIENT_AMOUNT, BETS_PER_CLIENT)  

  assert winners['client1'] == 2, 'Client1 should have 2 winners, for mocked data'
  assert winners['client2'] == 1, 'Client2 should have 1 winner, for mocked data'
  assert winners['client3'] == 0, 'Client3 should have 0 winners, for mocked data'
  docker.down()

def test_winners_with_5_clients():
  CLIENT_AMOUNT = 5
  BETS_PER_CLIENT = 60
  
  scripts.generate_docker_compose(client_amount=CLIENT_AMOUNT)
  generate_agency_file("agency-1.csv", BETS_PER_CLIENT, winners=[1])
  generate_agency_file("agency-2.csv", BETS_PER_CLIENT, winners=[1,2])
  generate_agency_file("agency-3.csv", BETS_PER_CLIENT, winners=[1,2,3])
  generate_agency_file("agency-4.csv", BETS_PER_CLIENT, winners=[1,2,3,4])
  generate_agency_file("agency-5.csv", BETS_PER_CLIENT, winners=[1,2,3,4,5])
  docker.up()

  winners = _test_winners(CLIENT_AMOUNT, BETS_PER_CLIENT)  

  assert winners['client1'] == 1, 'Client1 should have 1 winners, for mocked data'
  assert winners['client2'] == 2, 'Client2 should have 2 winner, for mocked data'
  assert winners['client3'] == 3, 'Client3 should have 3 winners, for mocked data'
  assert winners['client4'] == 4, 'Client4 should have 4 winners, for mocked data'
  assert winners['client5'] == 5, 'Client5 should have 5 winners, for mocked data'
  docker.down()
