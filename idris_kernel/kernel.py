from IPython.kernel.zmq.kernelbase import Kernel
from subprocess import check_output
import pexpect
import tempfile
import sexpdata
import sys
import os

class IdrisKernel(Kernel):
    implementation = 'idris_kernel'
    implementation_version = '0.1'

    language_info = {
        'name': 'idris',
        'mimetype': 'text/idris',
        'file_extesion': '.idr'
    }

    _banner = None

    @property
    def banner(self):
        if self._banner is None:
            self._banner = check_output(['idris', '--version']).decode('utf-8')
        return self._banner

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        self.tmp_file_name = '/home/michaelpj/tmp.idr'
        self.tmp_file = open(self.tmp_file_name, 'wb')
        self._start_idris()

    def _start_idris(self):
        self.idris = pexpect.spawn('idris --ide-mode', logfile=sys.stdout)
        self.idris.expect(':protocol-version')

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        self.tmp_file.write(code)
        self.tmp_file.flush()
        self.load_file(self.tmp_file_name)
        #evaled = { n: self.eval_expr(e) for (n, e) in user_expressions.iteritems() }
        return { 'status': 'ok', 'execution_count': 1, 'payload': [], 'user_expressions': {}}

    def load_file(self, fname):
        msg = make_message([sexpdata.Symbol(':load-file'), fname])
        self.idris.sendline(msg)
        index = self.idris.expect([":ok", ":error"])
        if index == 1:
            raise ValueError('Error from idris')

    def eval_expr(self, expr):
        msg = make_message([sexpdata.Symbol(':interpret'), expr])
        self.idris.sendline(msg)
        response = parse_message(self.idris.readline())
        print(response)

def make_message(py_sexp):
    py_sexp = [py_sexp, 1]
    sexp = sexpdata.dumps(py_sexp)
    return ("%06x" % len(sexp)) + sexp

def parse_message(msg):
    length = int(msg[:6], 16)
    sexp = msg[6:]
    assert len(sexp) == length
    return sexpdata.loads(sexp)
        
if __name__ == '__main__':
    from IPython.kernel.zmq.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=IdrisKernel)
