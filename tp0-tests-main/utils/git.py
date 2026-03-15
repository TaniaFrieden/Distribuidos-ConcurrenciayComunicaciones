from . import shell_cmd

class GitException(Exception):
  def __init__(self, message):
    message = 'Git: ' + message
    self.message = message
    super().__init__(self.message)

def reset_branch():
  return_code = shell_cmd.silent('git checkout .')
  
  if (return_code != 0):
    raise GitException('Can\'t reset branch')

  return_code = shell_cmd.silent('git clean -fd')
 
  if (return_code != 0):
    raise GitException('Can\'t clean branch')

def switch_branch(branch_name):
  reset_branch()
  return_code = shell_cmd.silent(f'git switch {branch_name}')
  if (return_code != 0):
    raise GitException(f'Can\'t switch to {branch_name}')
