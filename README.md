lazy-python
===========

A Python Lazy Programming library.

Overview
-----------

*Lazy Evaluation* is among useful features in Functional Programming. 
This tool help make lazy evaluation in Python easier.  The expression
is saved in directed graph and evaluated when necessary.  The process
of evaluation leverage multicore (``multiprocessing`` library in Python) 
and graph cut algorithm to compute the results in parallel.

Examples
-----------

This example illustrate how to calculate *Fibnoacci* by Lazy Evalution and
the cache mechanism of pure function call with the same parameters. By adding
parameter "*debug=True*", it is easy to show the evaluation process step by step.

    >>> from lazy import Lazy
    >>> def fib(n):
    ...     return Lazy(int, debug=True)(n) if n <= 1 else fib(n-1) + fib(n-2)
    ... 
    >>> a = fib(10)
    >>> a
    (((((((((1+int(0))+1)+(1+int(0)))+((1+int(0))+1))+(((1+int(0))+1)+(1+int(0))))+((((1+int(0))+1)+(1+int(0)))+((1+int(0))+1)))+(((((1+int(0))+1)+(1+int(0)))+((1+int(0))+1))+(((1+int(0))+1)+(1+int(0)))))+((((((1+int(0))+1)+(1+int(0)))+((1+int(0))+1))+(((1+int(0))+1)+(1+int(0))))+((((1+int(0))+1)+(1+int(0)))+((1+int(0))+1))))+(((((((1+int(0))+1)+(1+int(0)))+((1+int(0))+1))+(((1+int(0))+1)+(1+int(0))))+((((1+int(0))+1)+(1+int(0)))+((1+int(0))+1)))+(((((1+int(0))+1)+(1+int(0)))+((1+int(0))+1))+(((1+int(0))+1)+(1+int(0))))))
    >>> a.eval()
    int(0) == 0
    (1+0) == 1
    (1+1) == 2
    (2+1) == 3
    (3+2) == 5
    (5+3) == 8
    (8+5) == 13
    (13+8) == 21
    (21+13) == 34
    (34+21) == 55
    55
    >>> a
    55
    >>> b = fib(11)
    >>> b
    (55+34)
    >>> b.eval()
    (55+34) == 89
    89

Lazy Evaluation uses implicit parallel by *multiprocessing*. The following
example shows how the implicit parallel works by using decorator *lazy*.

    from lazy import lazy
    import time
    
    def f(name):
        print('Enter', name)
        time.sleep(5)
        print('Leave', name)
    
    @lazy
    def f1():
        f('f1')
        return 1
    
    @lazy
    def f2():
        f('f2')
        return 2
    
    @lazy
    def f3():
        f('f3')
        return 3
    
    @lazy
    def f4():
        f('f4')
        return 4
    
    if __name__ == '__main__':
        s = f1()*f2()+f3()*f4()
        print(s)
        s.eval()
        print(s)
    
    $ time python3 1.py
    ((f1()*f2())+(f3()*f4()))
    Enter f1
    Enter f2
    Enter f3
    Enter f4
    Leave f1
    Leave f3
    Leave f4
    Leave f2
    14
    
    real    0m5.173s
    user    0m0.111s
    sys 0m0.049s

