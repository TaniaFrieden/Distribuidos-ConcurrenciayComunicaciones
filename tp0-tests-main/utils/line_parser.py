EXIT_ID_STR = " exited with code "
ACTION_ID_STR = "action:"

class LineParserException(Exception):
	def __init__(self, message):
		message = 'Line parser: ' + message
		self.message = message
		super().__init__(self.message)

class Result:
	SUCCESS = "success"
	IN_PROGRESS = "in_progress"
	FAIL = "fail"

def parse_exit(line_str):
	if EXIT_ID_STR not in line_str:
		return None
	source, code = line_str.split(EXIT_ID_STR)
	return {
		"source": source,
		"action": "exit",
		"result":  Result.SUCCESS if int(code) == 0 else Result.FAIL
	}

def parse_action(line_str):
	if ACTION_ID_STR not in line_str:
		return None

	#Catch not enough
	source, action, result, *details = line_str.split('|')

	source = source.strip()
	action = action.split(':')[-1].strip()
	result = result.split(':')[-1].strip()

	if result not in [Result.FAIL, Result.SUCCESS, Result.IN_PROGRESS]:
		raise LineParserException(f'Unknown result type in "{result}"')
		
	msg = {
	"source": source,
	"action": action,
	"result": result
	}
	for detail in details:
		last_colon = detail.rfind(':')
		if last_colon < 0:
			raise LineParserException(f'Missing colon (:) in detail "{detail}"')

		detail_name = detail[:last_colon].strip()
		if detail_name in ["source", "action", "result"]:
			raise LineParserException(f'Invalid detail name in detail "{detail}"')
		detail_value = detail[last_colon+1:].strip()

		msg[detail_name] = detail_value

	return msg

def parse(line_str):
	line_str_stripped = line_str.rstrip()
	return parse_action(line_str_stripped) or parse_exit(line_str_stripped)
