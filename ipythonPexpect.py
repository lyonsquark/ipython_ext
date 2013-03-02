# ipythonPexpect

# THIS IS AN IPYTHON EXTENSION MODULE
# Load with %load_ext ipythonPexpect

"""Handle a pexpect.py session with an external program."""


import pexpect

from IPython.testing.skipdoctest import skip_doctest
from IPython.core.magic import (Magics, magics_class, cell_magic, line_magic, line_cell_magic)
from IPython.core.magic_arguments import (argument, magic_arguments, parse_argstring)
from IPython.core.error import UsageError

__version__ = '0.0.1'

# Strip quotes if necessary
def stripQuotes(s):
  if s[0] == '"' or s[0] == "'":
    q = s[0]
    if s[-1] == q:
      return s[1:-1]
  return s

# The PexpectMagics class
@magics_class
class PexpectMagics(Magics):
  """A set of magics for interacting with an external command-line application with pexpect."""

  def __init__(self, shell):
    super(PexpectMagics, self).__init__(shell)

    # Hang on to our instance of a pexpect child
    #   (maybe one day have a dictionary of these things)
    self._shell = shell
    self._child = None
    self._expectSearch = None
    self._prompt = None
    self._name = None
    self._isDefault = False
  
    self._shell.pexpect_locked = False

  #--Magics follow ------------------------------
  # Arguments for spawning
  @skip_doctest
  @magic_arguments()
  @argument(
      '-p', '--prompt', type=str,
      help='Pexpect Regex for the main application prompt [mandatory]'
    )

  @argument(
      '-c', '--continuation', type=str,
      help='Pexpect Regex for the continuation prompt [optional]'
    )
  
  @argument(
      '-i', '--init', type=str,
      help='Initialization command, if necessary'
    )

  @argument(
      '-t', '--timeout', type=int,
      help='Timeout (in s) for expect'
  )
  
  @argument(
      '-w', '--searchWindow', type=int,
      help='Search window size'
  )

  @argument(
    'command',
     nargs='*',
     help='The command to run including arguments'
    )
      
  @line_magic
  def pexpect_spawn(self, line):
    '''
      Line-level magic that spawns a pexpect session
      
      You can send an initalization string to set the prompt.
      
      The prompt should start with \r\n
      
      For example,
      
      Bash: (Set the prompt to a known quantity)
      %pexpect_spawn -i 'PS1="bash> "' -p '\r\nbash> ' -c '\r\n> ' /usr/bin/env bash
      
      R:
      %pexpect_spawn -p "\r\n> " -c "\r\n[+] " R
      
      CERN Root:
      %pexpect_spawn -p "\r\nroot \[\d+\] " -c "\r\n> " root
    '''
    
    args = parse_argstring(self.pexpect_spawn, line)

    # Make sure we have a prompt
    if getattr(args, 'prompt') is None:
      raise UsageError("You did not supply -p or --prompt")

    # Determine the command to run
    commandParts = args.command
    command = ' '.join(commandParts)

    prompt = args.prompt
        
    continuation = None
    if getattr(args, 'continuation') is not None:
      continuation = args.continuation
        
    timeout = None
    if getattr(args, 'timeout') is not None:
      timeout = args.timeout
  
    searchwindowsize = None
    if getattr(args, 'searchWindow') is not None:
      searchwindowsize = args.searchWindow
        
    initCommand = None
    if getattr(args, 'init') is not None:
      initCommand = stripQuotes(args.init)

    self.spawn(command, prompt, continuation, initCommand, timeout, searchwindowsize)
  
  #--------------------------------
  def spawn(self, command, prompt, continuation=None, initCommand=None, timeout=None, searchwindowsize=None):
    
    # If we already have a child, close it
    if self._child:
      self._child.close(True)
      self._child = None
      print 'Closing old connection'

    # Determine the prompt
    self._expectSearch = prompt
    if continuation:
      self._expectSearch = [prompt, continuation ]

    # Let's spawn
    self._child = pexpect.spawn(command)
        
    # Set timeout and windowsize
    if timeout:
      self._child.timeout = timeout
      
    if searchwindowsize:
      self._child.searchwindowsize = searchwindowsize

    # Run the init command
    if initCommand:
      # Run the command, discarding output
      self._child.sendline(initCommand)
    
    print 'Opened connection to %s' % command
    
    # Get to the prompt
    self._child.expect( self._expectSearch )  # Get the prompt
    print self._child.before
    self._prompt = self._child.after.lstrip()
    
    self._name = command

  #--------------------------------
  @line_magic
  def pexpect_spawn_bash(self, line):
    """Spawn a bash shell"""
    self.spawn("/usr/bin/env bash", "\r\nbash> ", "\r\n> ", "PS1='bash> '") 

  #--------------------------------
  @line_magic
  def pexpect_spawn_bash(self, line):
    """Spawn a bash shell"""
    self.spawn("/usr/bin/env bash", "\r\nbash> ", "\r\n> ", "PS1='bash> '")

  #--------------------------------
  @line_magic
  def pexpect_spawn_R(self, line):
    """Spawn an R session"""
    self.spawn("R", "\r\n> ", "\r\n[+] ")
    
  @line_magic
  def pexpect_spawn_root(self, line):
    """Spawn a Root session"""
    self.spawn("root", "\r\nroot \[\d+\] ", "\r\n> ")

  #--------------------------------
  @line_magic
  def pexpect_get_child(self, line):
    """Return the pexpect child object (for debugging)"""
    return self._child

  #--------------------------------
  @skip_doctest
  @magic_arguments()
  @argument(
    '-t', '--timeout', type=int,
    help='Timeout (in s) for this command'
    )
  
  @argument(
    '-w', '--searchWindow', type=int,
    help='Search window size for this command'
    )

  @argument(
            '-p', '--prompt', type=str,
            help='New Pexpect Regex for the main application prompt [mandatory]'
            )
  
  @argument(
            '-c', '--continuation', type=str,
            help='New Pexpect Regex for the continuation prompt [optional]'
            )
  
  @argument(
     '-e', '--evalLast',
     help='Return the output of the last command to python along with displaying (evaluate)',
     action='store_true',
     default=False
    )

  @argument(
    'code',
    nargs='*',
    )
  
  @line_cell_magic
  def P(self, line, cell=None):
    '''
    Send line or cell to the application and print the output
    '''
    
    if not self._child:
      raise UsageError("No connection")

    args = parse_argstring(self.P, line)
    if cell is None:
      code = ''
    else:
      code = cell
        
    timeout = -1
    if getattr(args, 'timeout') is not None:
      timeout=args.timeout

    searchwindowsize = -1
    if getattr(args, 'searchWindow') is not None:
      searchwindowsize=args.searchWindow
    
    # Determine the prompt search
    if getattr(args, 'prompt') is not None:
      self._expectSearch = stripQuotes( args.prompt )
    
    if getattr(args, 'continuation') is not None:
      self._expectSearch = [self._expectSearch, stripQuotes( args.continuation ) ]
    
        
    code = ' '.join(args.code) + '\r\n' +  code

    codeLines = [ x.strip() for x in code.split("\n") ]

    # Send each line one at a time
    for line in codeLines:
      if line:
        self._child.sendline( line )
        
        index = self._child.expect( self._expectSearch, timeout=timeout, searchwindowsize=searchwindowsize)
        
        print self._prompt + self._child.before
        self._prompt = self._child.after.lstrip()

    if args.evalLast:
      # Strip out the first line
      lines = [x.strip() for x in self._child.before.split("\n") ]
      if len(lines) > 1:
        return '\n'.join(lines[1:])
  

  #--------------------------------
  @skip_doctest
  @magic_arguments()
  @argument(
            '-t', '--timeout', type=int,
            help='Timeout (in s) for this command'
            )
  
  @argument(
            '-w', '--searchWindow', type=int,
            help='Search window size for this command'
            )
  
  @line_magic
  def pexpect_next_prompt(self, line):
    '''
      Typically to clear a timeout or other problem
    '''
    
    if not self._child:
      raise UsageError("No connection")
    
    args = parse_argstring(self.P, line)

    timeout = -1
    if getattr(args, 'timeout') is not None:
      timeout=args.timeout
    
    searchwindowsize = -1
    if getattr(args, 'searchWindow') is not None:
      searchwindowsize=args.searchWindow

    index = self._child.expect( self._expectSearch, timeout=timeout, searchwindowsize=searchwindowsize)

    print self._prompt + self._child.before
    self._prompt = self._child.after.lstrip()

  #--------------------------------
  @line_magic
  def pexpect_close(self, line):
    '''
      Close the connection and quit the application
    '''
    if not self._child:
      raise UsageError("No connection")

    self._child.close(True)
    self._child = None
    print 'Closed connection to %s' % self._name

  #--------------------------------
  @line_magic
  def pexpect_lock(self, line):
    '''
      Lock the notebook to send EVERY executed cell through pexpect
      
      Do %pexpect_unlock to unlock
    '''
    self._shell.pexpect_locked = True

    print 'WARNING: All future cell execution will be processed through pexpect!'
    print 'To return to IPython, issue %pexpect_unlock'

  #--------------------------------
  @line_magic
  def pexpect_unlock(self, line):
    '''
      Unlock the notebook to return to regular IPython
      '''
    self._shell.pexpect_locked = False
    
    print 'Notebook will use IPython'

# Let's rewrite InteractiveShell.run_cell to do automatic processing with pexpect
from IPython.core.interactiveshell import InteractiveShell

# Let's copy the original "run_cell" method (we do this only once so we can reload)
if not getattr(InteractiveShell, "run_cell_a", False):
  InteractiveShell.run_cell_a = InteractiveShell.run_cell

# Now rewrite run_cell
def run_cell_new(self, raw_cell, store_history=False, silent=False, shell_futures=True):
  
  # Are we locked in pexpect?
  if self.pexpect_locked:
  
    # Don't alter cells that start with %%P or say %pexpect_unlock
    if raw_cell[:3] == '%%P' or raw_cell[:15] == '%pexpect_unlock':
      pass
    else:
      # We're going to add a %%P to the top
      raw_cell = "%%P\n" + raw_cell

  self.run_cell_a(raw_cell, store_history, silent, shell_futures)

# And assign it
InteractiveShell.run_cell = run_cell_new

# Register
def load_ipython_extension(ipython):
  pexpectMagics = PexpectMagics(ipython)
  ipython.register_magics(pexpectMagics)

