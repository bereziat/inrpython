#! /usr/bin/python

# Full test of inrimage.py
from inrimage import *
from numpy import *
from subprocess import call

call(["mkdir","-p", "tests"])

##################
# Class Inrimage #
##################

## tests on constructors
########################

# create scalar image
im = Image('uint8',32,8)
im.create('tests/uint8.inr')
im.write(arange(256,dtype=uint8).reshape((8,32)))
im.close()

# read it
im = Image('tests/uint8.inr')
assert im.getdims() == (32,8)
data = im.read()
im.close()
assert (data.reshape(256) == arange(256,dtype=uint8)).all()

# 2-component image
im = Image('uint8',16,8,2)
im.create('tests/uint8v2.inr')
im.write(arange(256,dtype=uint8).reshape((8,16,2)))
im.close()

im = Image('tests/uint8v2.inr')
assert im.getcomponents() == 2
data = im.read()
im.close()
assert (data.reshape(256) == arange(256,dtype=uint8)).all()

# 2-frame image
im = Image('uint8',16,8,1,2)
im.create('tests/uint8z2.inr')
im.write(arange(256,dtype=uint8).reshape((2,8,16)))
im.close()

im = Image('tests/uint8z2.inr')
assert im.getframes() == 2
data = im.read(access='frame')
assert (data.reshape(256) == arange(256,dtype=uint8)).all()

# 2-frame and 2-component image

im = Image('uint8',8,8)
im.setcomponents(2)
im.setframes(2)
im.create('tests/uint8v2z2.inr')
im.write(arange(256,dtype=uint8).reshape((2,8,8,2)))
im.close()

im = Image('tests/uint8v2z2.inr')
data = im.read(access='frame')
assert (data.reshape(256) == arange(256,dtype=uint8)).all()


# copying format
im2 = Image(im)
assert im2.getdims() == im.getdims()
assert (im2.getcomponents(),im2.getframes()) == (im.getcomponents(),im.getframes())
assert im2.getcoding() == im.getcoding()
im2.create('tests/c_unit8v2z2.inr')
im2.write(data)
im2.seek(1,'frame')
data2 = im2.read(0,'frame')
im2.close()
im.close()
assert (data2 == data).all()

# explicit
im = Image()
im.setdims((8,8))
im.setcomponents(2)
im.setframes(2)
im.setcoding('uint8')
im.create ('tests/unit8v2z2.inr')
im.write(arange(256,dtype=uint8).reshape((2,8,8,2)))
im.close()

im = Image()
im.open('tests/uint8v2z2.inr')
data = im.read(access='frame')
im.close()
assert (data.reshape(256) == arange(256,dtype=uint8)).all()

# tests on value coding
########################

def iload(n):
    im = Image(n)
    data = im.read()
    im.close()
    return data
    
for t in ['b.inr','p.inr']:
    d = array([[0,64,128,255]])/255.

    for b in range(1,17)+range(25,33):
        im = Image('uint'+str(b),4,1)
        im.create('tests/uint'+str(b)+t)
        im.writef(d)
        im.close()

    assert (iload('tests/uint1'+t) == array([[0,0,1,1]])).all()
    assert (iload('tests/uint2'+t) == array([[0,1,2,3]])).all()
    assert (iload('tests/uint3'+t) == array([[0,2,4,7]])).all()
    assert (iload('tests/uint4'+t) == array([[0,4,8,15]])).all()
    assert (iload('tests/uint5'+t) == array([[0,8,16,31]])).all()
    assert (iload('tests/uint6'+t) == array([[0,16,32,63]])).all()
    assert (iload('tests/uint7'+t) == array([[0,32,64,127]])).all()
    assert (iload('tests/uint8'+t) == array([[0,64,128,255]])).all()
    assert (iload('tests/uint9'+t) == array([[0,128,257,511]])).all()
    assert (iload('tests/uint10'+t) == array([[0,257,514,1023]])).all()
    assert (iload('tests/uint11'+t) == array([[0,514,1028,2047]])).all()
    assert (iload('tests/uint12'+t) == array([[0,1028,2056,4095]])).all()
    assert (iload('tests/uint13'+t) == array([[0,2056,4112,8191]])).all()
    assert (iload('tests/uint14'+t) == array([[0,4112,8224,16383]])).all()
    assert (iload('tests/uint15'+t) == array([[0,8224,16448,32767]])).all()
    assert (iload('tests/uint16'+t) == array([[0,16448,32896,65535]])).all()
    assert (iload('tests/uint25'+t) == array([[0,8421505,16843009,33554431]])).all()
    assert (iload('tests/uint26'+t) == array([[0,16843010,33686019,67108863]])).all()
    assert (iload('tests/uint27'+t) == array([[0,33686020,67372039,134217727]])).all()
    assert (iload('tests/uint28'+t) == array([[0,67372040,134744079,268435455]])).all()
    assert (iload('tests/uint29'+t) == array([[0,134744080,269488159,536870911]])).all()
    assert (iload('tests/uint30'+t) == array([[0,269488160,538976319,1073741823]])).all()
    assert (iload('tests/uint31'+t) == array([[0,538976320,1077952639,2147483647]])).all()
    assert (iload('tests/uint32'+t) == array([[0,1077952640,2155905279,4294967295]])).all()
    

    d = array([[-128,-65,0,64,127]])/127.

    for b in range(3,17)+range(25,33):
        im = Image('int'+str(b),5,1)
        im.create('tests/int'+str(b)+t)
        im.writef(d)
        im.close()

    assert (iload('tests/int3'+t) == array([[-4,-2,0,2,3]])).all()
    assert (iload('tests/int4'+t) == array([[-8,-4,0,4,7]])).all()
    assert (iload('tests/int5'+t) == array([[-16,-8,0,8,15]])).all()
    assert (iload('tests/int6'+t) == array([[-32,-16,0,16,31]])).all()
    assert (iload('tests/int7'+t) == array([[-64,-33,0,32,63]])).all()
    assert (iload('tests/int8'+t) == array([[-128,-66,0,64,127]])).all()
    assert (iload('tests/int9'+t) == array([[-256,-131,0,129,255]])).all()
    assert (iload('tests/int10'+t) == array([[-512,-262,0,258,511]])).all()
    assert (iload('tests/int11'+t) == array([[-1024,-524,0,516,1023]])).all()
    assert (iload('tests/int12'+t) == array([[-2048,-1048,0,1032,2047]])).all()
    assert (iload('tests/int13'+t) == array([[-4096,-2096,0,2064,4095]])).all()
    assert (iload('tests/int14'+t) == array([[-8192,-4193,0,4128,8191]])).all()
    assert (iload('tests/int15'+t) == array([[-16384,-8386,0,8256,16383]])).all()
    assert (iload('tests/int16'+t) == array([[-32768,-16771,0,16513,32767]])).all()
    assert (iload('tests/int25'+t) == array([[-16777216,-8586764,0,8454659,16777215]])).all()
    assert (iload('tests/int26'+t) == array([[-33554432,-17173528,0,16909319,33554431]])).all()
    assert (iload('tests/int27'+t) == array([[-67108864,-34347056,0,33818639,67108863]])).all()
    assert (iload('tests/int28'+t) == array([[-134217728,-68694112,0,67637279,134217727]])).all()
    assert (iload('tests/int29'+t) == array([[-268435456,-137388224,0,135274559,268435455]])).all()
    assert (iload('tests/int30'+t) == array([[-536870912,-274776448,0,270549119,536870911]])).all()
    assert (iload('tests/int31'+t) == array([[-1073741824,-549552896,0,541098239,1073741823]])).all()
    assert (iload('tests/int32'+t) == array([[-2147483648,-1099105792,0,1082196479,2147483647]])).all()


# tests on dimensions

# tests on image access
#im = Image('uint8',4,3,1,5)
#im.create('tests/frames.inr')
#for i in range(5):
#    im.write(ones((3,4))*i)
#im.close()


# tests on colormap


# tests on function
