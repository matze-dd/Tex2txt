
#
#   test of shell.py with own "LT server"
#

import subprocess
import time
import urllib.request

directory = 'tests/test_shell_py/'
file = directory + 'latex'

server_cmd = 'python ' + directory + 'lt-server.py'
shell_cmd = 'python shell.py --server my ' + file + '.tex'
shell_cmd_html = shell_cmd + ' --html'
server_stop = 'http://localhost:8081/stop'


def test_shell():

    # start "LT server"
    subprocess.Popen(server_cmd.split(), stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
    time.sleep(10)

    # run shell.py
    out = subprocess.run(shell_cmd.split(), stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL)
    out_txt = out.stdout.decode('utf-8')

    # run shell.py --html
    out = subprocess.run(shell_cmd_html.split(), stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL)
    out_html = out.stdout.decode('utf-8')

    # stop server
    requ = urllib.request.Request(server_stop, 'x'.encode('ascii'))
    try:
        urllib.request.urlopen(requ)
    except:
        pass

    f = open(file + '.txt')
    expect_txt = f.read()
    f.close()
    f = open(file + '.html')
    expect_html = f.read()
    f.close()

    assert out_txt == expect_txt
    assert out_html == expect_html

