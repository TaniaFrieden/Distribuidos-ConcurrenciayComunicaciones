from . import shell_cmd

def generate_docker_compose(client_amount):
	code = shell_cmd.silent(f'bash generar-compose.sh docker-compose-dev.yaml {client_amount}')
	if code != 0:
		raise Exception('Error generating docker-compose file')

def validate_echo_server():
	return shell_cmd.pipe(f'sh validar-echo-server.sh')