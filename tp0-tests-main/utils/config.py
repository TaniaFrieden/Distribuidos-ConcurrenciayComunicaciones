def client(address = "server:12345", loop_amount = 3, loop_period= "50ms", log_level="INFO", max_amount=10):
	file = open("./client/config.yaml", "w")
	file.write(f'server:\n  address: "{address}"\nloop:\n  amount: {loop_amount}\n  period: "{loop_period}"\nlog:\n  level: "{log_level}"\nbatch:\n  maxAmount: {max_amount}\n')
	file.close()

def server(port=12345, ip="server", listen_backlog=5, logging_level="INFO"):
	file = open("./server/config.ini", "w")
	file.write(f'[DEFAULT]\nSERVER_PORT = {port}\nSERVER_IP = {ip}\nSERVER_LISTEN_BACKLOG = {listen_backlog}\nLOGGING_LEVEL = {logging_level}')
	file.close()
