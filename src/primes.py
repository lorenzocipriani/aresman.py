#!/usr/bin/env python
'''
primes.py
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
    
    
if __name__ == '__main__':
    
    print("Search for the first {} prime numbers:".format(primesToFind))
    
    while primesToFind > 0:
        num += 1
        if isPrime(num):
            found += 1
            print(found, num)
            primesToFind -= 1
