import os
import pytest
from utils import git, docker, config, scripts, line_parser

def _test_clients_msg_amount(client_amount, msg_amount):
	# Script setup
	config.server()
	config.client(loop_amount=msg_amount)
	scripts.generate_docker_compose(client_amount)

	# Build images every time with the new client and server config
	docker.build()
	docker.up()
	logs = docker.logs()

	# Each client has a list of expected messages
	msg_checklist = {}
	for client_id in range(1, client_amount + 1):
		msg_checklist[f'client{client_id}'] = [False] * msg_amount

	clients_left_to_end = client_amount
	for line in logs:
		print(line, end='')
		msg = line_parser.parse(line)
		if not msg:
			continue
		assert (msg['result'] != line_parser.Result.FAIL), 'No operation should fail'

		if msg['action'] == 'receive_message':
			if msg['source'] == 'server':
				continue

			# When a message is logged by a client we mark the checklist entry
			# corresponding to its id.
			msg_nmb_index = msg['msg'].rfind('°')
			assert (msg_nmb_index >= 0), 'In received message log, no º was found'
			msg_id = int(msg['msg'][msg_nmb_index + 1:]) - 1
			msg_checklist[msg['source']][msg_id] = True
		elif msg['action'] == 'exit':
			assert (msg['source'] != 'server'), 'Server should keep running even if clients disconnect'
			assert (msg['result'] == line_parser.Result.SUCCESS), 'Expected client to exit succesfuly'
		elif msg['action'] == 'loop_finished':
			clients_left_to_end -= 1
			if clients_left_to_end <= 0:
				break

	# All clients' checklist has to be marked at the end of the execution
	for client_id in range(1, client_amount + 1):
		assert all(msg_checklist[f'client{client_id}']) , f'Client{client_id} should have exchanged all expected messages'

	docker.down()

@pytest.fixture(autouse=True, scope='module')
def setup():
	os.chdir(os.environ['REPO_PATH'])
	git.reset_branch()
	git.switch_branch('ej1')
	docker.stop_all()
	docker.prune()

@pytest.fixture(autouse=True)
def beforeEach():
	git.reset_branch()
	docker.down()

def test_one_client_one_message():
	_test_clients_msg_amount(1, 1)

def test_one_client_multipple_messages():
	_test_clients_msg_amount(1, 3)

def test_two_clients_one_message():
	_test_clients_msg_amount(2, 1)

def test_multiple_clients_one_message():
	_test_clients_msg_amount(5, 1)

def test_multiple_clients_multiple_messages():
	_test_clients_msg_amount(5, 5)
