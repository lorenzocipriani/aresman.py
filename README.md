# aresman.py
Automatic Resource Management - A system tool for improving servers business continuity (Python)


The script is into src folder and it's named aresmam.py

On any Linux environment with python 2.x or 3.x it can be executed with this 
command (sudo or root credentials are mandatory):
```sudo python aresman.py```

To improve the performances and reduce the memory footprint it can be compiled
into bytecode then executed with one of these 2 commands set:
```python -m py_compile aresman.py
sudo python aresman.pyc```
or this one that has a better optimization:
```python -OO -m py_compile aresman.py
sudo python aresman.pyo```

Into the test folders there is:
- the primes-cgi.py cgi script that has been used for test, it needs to be copied into the Apache HTTPD cgi-bin folder;
- the aresman.jmx test plan to be used with Apache Jmeter.
