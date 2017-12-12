#!/usr/bin/env python

'''
primes-cgi.py
@author: Lorenzo Cipriani <lorenzo1974@gmail.com>
@contact: https://www.linkedin.com/in/lorenzocipriani
@since: 2017-10-23
@see:

'''

primesToFind = 1000000

num = 0
found = 0

def isPrime(num):
    if num > 1:
        for i in range(2, num):
            if (num % i) == 0: return False
        else: return True
    else: return False
    

print "Content-Type: text/html\n\n"
    
print """
<html>
<head><title>CGI Script for Prime Numbers Search</title></head>
<body>
"""
print ("<h1>Search for the first {} prime numbers</h1>\n".format(primesToFind))

print "<body>\n<dl>\n"

primesList = []

while primesToFind > 0:
    num += 1
    if isPrime(num):
        primesList.append(num)
        found += 1
        print("<dt>{}</dt><dd><strong>{}<strong> - ".format(found, num))
        for item in primesList: print("{}, ".format(item))
        print "</dd>\n"
        primesToFind -= 1

print "</dl>\n</body>\n</html>"
