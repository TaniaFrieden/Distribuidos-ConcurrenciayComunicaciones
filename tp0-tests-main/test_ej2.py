import os
import pytest
from utils import git, docker, config, scripts, line_parser

CLIENT_CONFIG_A = {
	'loop_amount' : 5,
	'loop_period' : '100ms',
	'log_level' :'DEBUG'
}

CLIENT_CONFIG_B = {
	'loop_amount' : 2,
	'loop_period' : '250ms',
	'log_level' :'INFO'
}

SERVER_CONFIG_A = {
	'listen_backlog' : 8,
	'logging_level': 'DEBUG'
}

SERVER_CONFIG_B = {
	'listen_backlog' : 16,
	'logging_level': 'INFO'
}

def _test_config(client_config=None, server_config=None):
	config.server(**(server_config or {}))
	config.client(**(client_config or {}))
	scripts.generate_docker_compose(1)
	docker.up()
	logs = docker.logs()
	
	for line in logs:
		print(line, end='')
		msg = line_parser.parse(line)
		if not msg:
			continue

		assert(msg['result'] != line_parser.Result.FAIL)
		if msg['action'] == 'config':
			if msg['source'] == 'server':
				if not server_config:
					continue
				for key, value in server_config.items():
					assert (msg[key] == str(value)), f'Expected {key} to be {value}, but found {msg[key]}'
			else:
				if not client_config:
					continue
				for key, value in client_config.items():
					assert (msg[key] == str(value)), f'Expected {key} to be {value}, but found {msg[key]}'
		elif msg['action'] == 'exit':
			assert (msg['source'] != 'server'), 'Server should keep running even if clients disconnect'
			assert (msg['result'] == line_parser.Result.SUCCESS), 'Expected client to exit succesfuly'
		elif msg['action'] == 'loop_finished':
			break
	docker.down()


@pytest.fixture(autouse=True, scope='module')
def setup():
	os.chdir(os.environ['REPO_PATH'])
	git.reset_branch()
	git.switch_branch('ej2')
	docker.stop_all()
	docker.prune()
	#Build images only once
	docker.build()

@pytest.fixture(autouse=True)
def beforeEach():
	git.reset_branch()
	docker.down()

def test_client_config_A():
	_test_config(client_config=CLIENT_CONFIG_A)

def test_client_config_B():
	_test_config(client_config=CLIENT_CONFIG_B)

def test_server_config_A():
	_test_config(server_config=SERVER_CONFIG_A)

def test_server_config_B():
	_test_config(server_config=SERVER_CONFIG_B)
