from IPython.kernel.zmq.kernelbase import Kernel
from subprocess import check_output
import pexpect
import tempfile
import sexpdata
import sys
import os

__tmp_file_name__ = '/home/michaelpj/tmp.idr'

class IdrisKernel(Kernel):
    implementation = 'idris_kernel'
    implementation_version = '0.1'

    language_info = {
        'name': 'idris',
        'mimetype': 'text/x-idris',
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
        self.tmp_file = open(__tmp_file_name__, 'wb')
        self.idris = Idris()

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        self.tmp_file.write(code)
        self.tmp_file.flush()
        response = self.idris.load_file(__tmp_file_name__)

        for written in response['written']:
            log(written)
        for warning in response['warnings']:
            log(warning)

        if len(response['errors']) != 0:
            return { 
                    'status': 'error',
                    'execution_count': 1,
                    'ename': 'Error',
                    'evalue': ",".join(response['errors'])
                }
        #evaled = { n: self.eval_expr(e) for (n, e) in user_expressions.iteritems() }
        return { 'status': 'ok', 'execution_count': 1, 'payload': [], 'user_expressions': {}}


class Idris(object):
    def __init__(self):
        self.idris = pexpect.spawn('idris --ide-mode', logfile=open('/tmp/idris.log', 'wb'))

    def load_file(self, fname):
        msg = make_message([sexpdata.Symbol(':load-file'), fname])
        self.idris.sendline(msg)
        return self.handle_responses()
        
    def eval_expr(self, expr):
        msg = make_message([sexpdata.Symbol(':interpret'), expr])
        self.idris.sendline(msg)
        return self.handle_responses()

    def read_message(self):
        length = int(self.idris.read(6), 16)
        log("Read length: " + str(length))
        msg = self.idris.read(length+1)
        log("Read message: " + msg)
        return msg

    def handle_responses(self):
        written = []
        warnings = []
        errors = []
        result = None
        while True:
            msg = sexpdata.loads(self.read_message())
            log("Parsed: " + str(msg))
            if not isinstance(msg[0], sexpdata.Symbol):
                continue

            msg_code = msg[0].value()
            log("Msg code: " + msg_code)

            if msg_code == ':write-string':
                written.append(msg[1])
            if msg_code == ':warning':
                warnings.append(msg[1][3])
            if msg_code == ':error':
                errors.append(msg[1][3])

            if msg_code == ':return':
                if msg[1][0] == ':ok':
                    result = msg[1][1]
                if msg[1][0] == ':error':
                    errors.append(msg[1][1])
                break


        return { 'written' : written, 'warnings': warnings, 'errors': errors, 'result': result }

def log(log_message):
    print(log_message)


def make_message(py_sexp):
    py_sexp = [py_sexp, 1]
    sexp = sexpdata.dumps(py_sexp)
    return ("%06x" % (len(sexp)+1)) + sexp

def parse_message(msg):
    msg = msg.rstrip()
    log("Parsing: " + msg)
    length = int(msg[:6], 16) - 1
    sexp = msg[6:]
    assert len(sexp) == length
    return sexpdata.loads(sexp)
        
if __name__ == '__main__':
    from IPython.kernel.zmq.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=IdrisKernel)
