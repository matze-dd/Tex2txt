
#
#   test of shell.py with LT server
#

import subprocess
import time

server_cmd = 'python tests/test_shell_py/lt-server.py'
shell_cmd = 'python shell.py --server my tests/test_shell_py/latex.tex'

err_t = r"""=== tests/test_shell_py/latex.tex ===
1.) Line 3, column 6, Rule ID: None
Message: Error
Suggestion: is
This isx a test. 
     ^^^

"""

def test_shell():

    subprocess.Popen(server_cmd.split(), stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
    time.sleep(10)

    out = subprocess.run(shell_cmd.split(), stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL)
    err = out.stdout.decode('utf-8')
    assert err == err_t

