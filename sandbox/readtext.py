#! /usr/bin/python3


fileread = open("sandbox/bsvalue.txt", "r")
valtext  = fileread.readline()
val = int(valtext)
print('value: %d'%(val))
fileread.close()
