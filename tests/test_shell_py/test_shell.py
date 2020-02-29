
#
#   test of shell.py with own "LT server"
#

import subprocess
import time
import urllib.request

server_cmd = 'python tests/test_shell_py/lt-server.py'
shell_cmd = 'python shell.py --server my tests/test_shell_py/latex.tex'

server_stop = 'http://localhost:8081/stop'

err_t = r"""=== tests/test_shell_py/latex.tex ===
1.) Line 3, column 6, Rule ID: None
Message: Error
Suggestion: is
This isx a test. 
     ^^^

"""

def test_shell():

    # start "LT server"
    subprocess.Popen(server_cmd.split(), stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
    time.sleep(10)

    # run shell.py
    out = subprocess.run(shell_cmd.split(), stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL)
    err = out.stdout.decode('utf-8')

    # stop server
    requ = urllib.request.Request(server_stop, 'x'.encode('ascii'))
    try:
        urllib.request.urlopen(requ)
    except:
        pass

    assert err == err_t

