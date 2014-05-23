from multiprocessing import Pool, cpu_count
from threading import Lock
from operator import add, sub, mul, truediv, getitem
import time, weakref

def lazy(func):
    new_name = '_lazy_'+func.__name__
    globals()[new_name] = func
    func.__name__ = new_name
    func.__module__ = __name__
    lazyfunc = Lazy(func)
    return lazyfunc

class Lazy(object):

    POOL = None
    JOBS = weakref.WeakSet()
    CACHES = weakref.WeakValueDictionary()
    ACTIVE = 0
    CORES = cpu_count()

    @classmethod
    def set_cores(cls, num):
        cls.CORES = num
    def __init__(self, operator, remote=True, format='{0}({1})', debug=False):
        self.operator = operator
        self.remote = remote
        self.format = format
        self.func = True
        self.depth = -1
        self.args = None
        self.waitlock = None
        self.debug = debug
    def call(self, *args):
        cache_key = (self.operator, args)
        if cache_key in Lazy.CACHES:
            return Lazy.CACHES[cache_key]
        Lazy.CACHES[cache_key] = self
        self.func = False
        self.waitings = []
        self.value = None
        self.argscount = 0
        self.argsready = 0
        self.runtime = self.waittime = 0
        self.startrun = self.startwait = 0
        self.startwait = time.time()
        self.args = args
        for i in self.args:
            if isinstance(i, Lazy):
                if i.value is None:
                    self.argscount += 1
                    i.waitings.append(self)
                if i.debug:
                    self.debug = True
        if self.argscount == 0:
            if self.remote:
                Lazy.JOBS.add(self)
            else:
                self.startrun = time.time()
                args = tuple(getattr(i, 'value', i) for i in self.args)
                self.value = self.operator(*args)
                self.runtime = time.time() - self.startrun
        return self
    def setdepth(self, l=0):
        for i in self.args:
            if isinstance(i, Lazy):
                i.setdepth(l+(1 if i.remote else 0))
        self.depth = max(self.depth, l)
    def __call__(self, *args):
        s = Lazy(self.operator, self.remote, self.format, self.debug)
        return s.call(*args)
    def __add__(self, a):
        return ADD(self, a)
    def __radd__(self, a):
        return ADD(a, self)
    def __sub__(self, a):
        return SUB(self, a)
    def __rsub__(self, a):
        return SUB(a, self)
    def __mul__(self, a):
        return MUL(self, a)
    def __rmul__(self, a):
        return MUL(a, self)
    def __truediv__(self, a):
        return DIV(self, a)
    def __rtruediv__(self, a):
        return DIV(a, self)
    def __pow__(self, a):
        return POW(self, a)
    def __rpow__(self, a):
        return POW(a, self)
    def __getitem__(self, idx):
        return GETITEM(self, idx)
    def __eq__(self, other):
        return self.operator == other.operator and self.args == other.args
    def __hash__(self):
        return hash((self.operator, self.args))
    def opname(self):
        if self.operator.__name__.startswith('_lazy_'):
            return self.operator.__name__[6:]
        else:
            return self.operator.__name__
    def __str__(self):
        if self.func:
            return 'Lazy(%s)' % (self.opname(),)
        elif self.value is None:
            return self.format.format(self.opname(), ', '.join(map(str, self.args)), *self.args)
        else:
            return str(self.value)
    def __repr__(self):
        return self.__str__()
    def argsfinish(self):
        self.argsready += 1
        if self.argsready >= self.argscount:
            Lazy.JOBS.add(self)
    def finish(self, value):
        self.runtime = time.time() - self.startrun
        if self.debug:
            print(self, '==', value)
        self.value = value
        for i in self.waitings[:]:
            i.argsfinish()
        del self.waitings[:]
        if self.remote:
            Lazy.ACTIVE -= 1
        self.schedule()
        if self.waitlock:
            self.waitlock.release()
    def startjob(self):
        self.waittime = time.time() - self.startwait
        self.startrun = time.time()
        args = tuple(getattr(i, 'value', i) for i in self.args)
        Lazy.JOBS.discard(self)
        if self.remote:
            Lazy.ACTIVE += 1
            self.POOL.apply_async(self.operator, args, callback = self.finish)
        else:
            self.finish(self.operator(*args))
    def eval(self):
        if self.value is not None:
            return self.value
        if Lazy.POOL is None:
            Lazy.POOL = Pool(Lazy.CORES)
        self.remote = False
        self.setdepth(0)
        self.waitlock = Lock()
        self.waitlock.acquire()
        self.schedule()
        self.waitlock.acquire()
        return self.value
    @classmethod
    def schedule(cls):
        while cls.JOBS:
            next = max(list(cls.JOBS), key=lambda x:x.depth)
            if next.depth == -1 or next.remote and cls.ACTIVE >= cls.CORES:
                break
            next.startjob()

ADD = Lazy(add, remote=True, format='({2}+{3})')
SUB = Lazy(sub, remote=True, format='({2}-{3})')
MUL = Lazy(mul, format='({2}*{3})')
DIV = Lazy(truediv, format='({2}/{3})')
POW = Lazy(pow, format='({2}**{3})')
GETITEM = Lazy(getitem, remote=False, format='{2}[{3}]')
INT = Lazy(int, remote=False, format='{2}')

