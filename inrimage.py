# -*- coding: utf-8 -*-

"""
Inrimage wrapper for python (only python2 at this time is supported)
"""
__author__ = "Dominique Béréziat (dominique.bereziat@lip6.fr)"
__date__   = "march 2018"
__version__ = "0.1"

from ctypes import c_wchar_p, c_char_p, c_int, c_uint8, c_float, c_double, c_void_p, cast
import numpy as np
import sys
from os import environ

# TODO
#   * pas de capture des erreurs inrimage pour les exceptions python
#     => pas d'autre choix que d'introduire de nouvelles fonctions dans libinrimage
#   * prefix installation inrimage et python
#
# BUGS
#   * Marche pas en python3 :(
assert sys.version_info.major == 2
#

if environ.get('INRPYTHONPATH'): libinrpath=environ.get('INRPYTHONPATH')+'/lib'
lib = np.ctypeslib.load_library('libinrimage',libinrpath)

#######################
# initialize inrimage
#######################
_c_argv = c_char_p * 1
_argv = _c_argv('inrpython')
lib.inr_init.restype = None
lib.inr_init.argtypes = [c_int,_c_argv,c_char_p,c_char_p,c_char_p]
lib.inr_init(len(_argv),_argv,'0.1','inrimage python wrapper','')

#####################
# inrimage bindings
#####################
# image_()
c_lfmt = np.ctypeslib.ndpointer(dtype=c_int,ndim=1)
lib.image_.restype = c_void_p
lib.image_.argtypes = [c_char_p,c_char_p,c_char_p,c_lfmt]
# c_lecflt()
c_floatp = np.ctypeslib.ndpointer(dtype=c_float)
lib.c_lecflt.argtypes = [c_void_p,c_int,c_floatp]
# c_ecrflt()
lib.c_ecrflt.argtypes = [c_void_p,c_int,c_floatp]
# fermnf_()
lib.fermnf_.argtypes = [c_void_p]
# c_lect()
lib.c_lect.argtypes = [c_void_p,c_int,c_void_p]
# c_ecr()
lib.c_ecr.argtypes = [c_void_p,c_int,c_void_p]
# c_lptset()
lib.c_lptset.argtypes = [c_void_p,c_int]
# c_lptget()
lib.c_lptget.rettype = [c_int]
lib.c_lptget.argtypes = [c_void_p]
# c_pckbt
lib.c_pckbt.argtypes = [c_void_p,c_void_p,c_int,c_int]
# c_unpkbt
lib.c_unpkbt.argtypes = [c_void_p,c_void_p,c_int,c_int]
# ird_ctrgb
lib.ird_ctrgb.rettype = [c_int]
lib.ird_ctrgb.argtypes = [c_void_p,c_lfmt,c_lfmt,c_void_p,c_void_p,c_void_p,c_int]
# iwr_ctrgb
lib.iwr_ctrgb.argtypes = [c_void_p,c_int,c_int,c_void_p,c_void_p,c_void_p]
# set_hdr_min
lib.set_hdr_min.argtypes = [c_int]

#################
# various stuff
#################
try:
    if sys.ps1: interpreter = True
except AttributeError:
    interpreter =  False
    if sys.flags.interactive: interpreter = True

###############################
# A class to read/write images
###############################
class InrImage:
    """
    A simple Python wrapper to Inrimage library. See 'man Intro' for
    an introduction to the Inrimage format.

    An Inrimage image has the following characteristics:
      - <<nframes>> of images called frame (video, sequence of images)
      - a frame has <<height>> lines, each line having <<width pixels>>
      - a pixel has <<components>> values (usually 1 or 3 but may be any 
        positive integer value)
      - a value can be coded using :
        - flotting precision (single or double precision),
        - fixed precision with an arbitrary size between 1 and 32 bits
        - value with fixed precision may be signed or unsigned
        - exposant of fixed precision can also be coded
      - images can also make use of a colormap

    """
    def __init__( self, arg1=None, arg2=None, arg3=None, arg4=None, arg5=None):
        """ Constructors:
        InrImage() - just create an Image instance
        InrImage(coding,width,height,[components,[frames]]) 
                   - create a new image, equivalent to
                     img = InrImage()
                     img.setcoding(coding)
                     img.setdims((width,height))
                     img.setcomponents(components)
                     img.setframes(frames)
        InrImage(img) - create a new image from an existing image instance,
                        equivalent to:
                        img2 = InrImage()
                        img2.setcoding(img.getcoding(img))
                        img2.setdims(img.getdims(img))
                        img2.setcomponents(img.getcomponents(img))
                        img2.setframes(img.getframes(img))
        InrImage(file) - open an existing image file, equivalent to :
                         img = InrImage()
                         img.open(file)
        """
        self._nf   = 0
        self._storage = ''

        # codage par défaut 1 octet non signé
        self._lfmt = np.array( [0,0,1,0,0,0,1,1,200],dtype=c_int)

        if arg1 and isinstance(arg1,str) and arg2 and isinstance(arg2,int) and \
           arg3 and isinstance(arg3,int):
            self.setcoding(arg1)
            self.setdims((arg2,arg3))
            if arg4: self.setcomponents(arg4)
            if arg5: self.setframes(arg5)
        elif arg1 and isinstance(arg1,str):
            self.open(arg1)
        elif arg1 and isinstance(arg1,InrImage):
            for i in range(9):
                self._lfmt[i] = arg1._lfmt[i]
        
    def open(self,filename):
        """ 
        str -> NoneType

        Open an existing image (for read or write).
        
        See also: close()
        """
        if self._nf == 0:
            self._nf = lib.image_(filename,'e',' ',self._lfmt)
            self._setstorage()
            self._filename = filename
            if interpreter: self._msg('opened for read/write '+filename)

    def create(self,filename,hdr=None):
        """
        str * int -> NoneType

        Create an image on the disk. Require that coding and dimensions
        are correctly defined (see __init__(), setcoding(), setdims(),
        and optionnaly setcomponents(), setframes()).
        If the image exists on disk, it is erased. To modify an existing 
        image use open().

        See also: close()
        """
        if self._nf == 0:
            if hdr: lib.set_hdr_min(hdr)
            self._nf = lib.image_(filename,'c',' ',self._lfmt)
            if hdr: lib.set_hdr_min(1)
            self._filename = filename
            self._setstorage()
            if interpreter: self._msg('created '+filename)

    def close(self):
        """
        NoneType -> NoneType

        Close the image file descriptor (after a call of open() or create()).
        """
        if self._nf != 0:
            lib.fermnf_(c_void_p(self._nf).value)
            self._nf = 0

    def readf(self, count=0, access=None):
        """
        int * str -> Array(dtype=single)

        Read data from disc. This function is similar to read() excepted that it
        always returns a float matrix. Image values with flotting precision are 
        directly read, image values with fixed precision are normalized between
        [0,1] or [-1,1] if image values are signed (see man lecflt).

        See also read(), writef()
        """
        if self._nf == 0: return None
        ccount = count
        if access == 'frame':
            if ccount == 0: ccount = self._lfmt[7] - self.tell('frame') + 1
            nframes = ccount
            ccount = ccount*self._lfmt[5] - self.tell() + 1
        elif ccount == 0:
            ccount = self._lfmt[5]

        # read data
        if self._lfmt[3] == 1 and self._lfmt[2] == 8:
            # hack to read double precision image
            data = np.empty( (ccount,self._lfmt[0]), dtype=c_double)
            ptr = data.__array_interface__['data'][0]
            lib.c_lect( self._nf, ccount, cast(ptr,c_void_p))
        else:
            data = np.empty( (ccount,self._lfmt[0]), dtype=c_float)
            lib.c_lecflt( self._nf, ccount, data)

        # reshape matrix
        if access=='frame' and self._lfmt[7]>1:
           if  self._lfmt[6]>1:
               data = np.reshape(data,(nframes,self._lfmt[5],self._lfmt[4],
                                       self._lfmt[6]))
           else:
               data = np.reshape(data,(nframes,self._lfmt[5],self._lfmt[4]))
        elif self._lfmt[6]>1:
            data = np.reshape(data,(ccount,self._lfmt[4],self._lfmt[6]))

        if interpreter:
            print 'read a total of ' + str(ccount) + ' lines from ' + self._filename

        return data

    def writef(self,data):
        """
        Array -> int

        Write data to image. This function is similar to write() excepted
        that data values are converted to the image format according to 
        Inrimage rules (see man lecflt).

        See also: write(), readf()
        """
        nframes = ndimv = 1
        if data.ndim == 4:
            nframes,nlines,ncols,ndimv = data.shape
        elif data.ndim == 3:
            if self._lfmt[6]>1: 
                nlines,ncols,ndimv = data.shape
            else:
                nframes,nlines,ncols = data.shape
        elif data.ndim == 2:
            nlines,ncols = data.shape
        elif data.ndim == 1:
            nlines,ncols = 1,data.size
        else:
            print('write:error: too many dimensions in data')
            
        # check consistence between image and data dimensions
        if ncols != self._lfmt[4]:
            print('write:error: incompatible size (width) between image and data')
            return
        if ndimv != self._lfmt[6]:
            print('write:error: incompatible size (components) between image and data')
            return
        if nframes>1 and nlines != self._lfmt[5] != nlines:
            print('write:error: incompatible size (height) between image and data')

        # write data
        if self._lfmt[3] ==1 and self._lfmt[2] == 8:
            data_copy = np.array(data,dtype=c_double)
            ptr = data_copy.__array_interface__['data'][0]
            lib.c_ecr( self._nf, nframes*nlines, cast(ptr,c_void_p))
        else:
            data_copy = np.array(data,dtype=c_float)
            lib.c_ecrflt( self._nf, nframes*nlines, data_copy)

        if interpreter:
            print 'write a total of ' + str(nframes*nlines) + \
                'lines to ' + self._filename

        return nframes*nlines
        
    def read(self, count=0, access=None):
        """
        int * str -> Array

        Read 'count' lines from an image. 
          - If count = 0, read all lines from the current position up to the
                          last line of the current frame
          - If access = 'frame' count is a number of frames and count = 0
                          means to read from the current frame up to the
                          last frame

        The function returns a Numpy array, the type of the array is
        determinated according to the image class storage on the disc. 
        It could be 'float32', 'float64', 'uint8', 'int8', 'uint16',
        'int16', 'uint32' or 'int32'.

        The dimension of the array can be 2, 3 or 4 depending on the
        dimension of the image on disc and on access value.  With
        access value to None, the array is a matrix of <<height>> rows
        an <<width>> columns. If the image has more than one
        components per pixel (for instance, a color image has 3
        compoments), the array has 3 dimensions, and the third
        dimension address components.  If access value is set to
        'frame' and if the image has more than one frame, read()
        always returns an hypermatrix, and the first dimension address
        frames.

        Examples:
            a=img.read() # read one frame from img. 
                         # if img is 1-frame, read the whole image.
            a=img.read(1) # read one line from img.
            a=img.read(1,'frame') # read one frame from img
            a=img.read(access='frame') # read all frames from img

        See also: write()
        """
        if self._nf == 0: return None
        ccount = count
        if access == 'frame':
            if ccount == 0: ccount = self._lfmt[7] - self.tell('frame') + 1
            nframes = ccount
            ccount = ccount*self._lfmt[5]
        elif ccount == 0:
            ccount = self._lfmt[5] - self.tell() + 1

        data = np.empty( (ccount, self._lfmt[0]), dtype=self._storage)
        # address of data C-buffer ! 
        ptr = data.__array_interface__['data'][0]
        # cast to void*
        lib.c_lect( self._nf, ccount, cast(ptr,c_void_p))
        
        # unpack data if needed
        if self._lfmt[3] == -1:
            lib.c_unpkbt(cast(ptr,c_void_p),cast(ptr,c_void_p),
                         ccount*self._lfmt[0],-self._lfmt[2])

        # reshape matrix            
        if access=='frame' and self._lfmt[7]>1:
           if  self._lfmt[6]>1:
               data=np.reshape(data,(nframes,self._lfmt[5],self._lfmt[4],self._lfmt[6]))
           else:
               data=np.reshape(data,(nframes,self._lfmt[5],self._lfmt[4]))
        elif self._lfmt[6]>1:
            data=np.reshape(data,(ccount,self._lfmt[4],self._lfmt[6]))

        if interpreter:
            print 'read a total of ' + str(ccount) + ' lines from ' + self._filename
            
        return data

    def write(self, data):
        """Array -> int

        Write in an image according to dimensions of parameter data. 

        Array values are first converted to the image format (see
        getcoding()) using Numpy conversion rules.

        Dimensions of array data and targeted image should be
        compatible. As Inrimage write line by line, number of pixels
        and components by line should be the same between data array
        and image format. Function write() writes the number of lines
        (or frames) given by parameter data.


        See also: read()

        """
        # proposition:
        #  data est m*n, ou m*n*p, ou m*n*p*q
        #  data.ndim = 2 : pas d'ambiguite on ecrit les m lignes
        #                   de data dans l'image a partir de la position
        #                   courante
        #  data.ndim = 4 : on ecrira m plans vectoriels 
        #  data.ndim = 3 : si image -z 1 -v > 1 => c'est le meme cas que
        #                   ndims = 2, on ecrit m lignes
        #                   si image -z > 1 -v 1 , c'est le meme cas que
        #                   data.ndims = 4 avec q=1, on ecrira m plans
        
        if self._nf == 0: return
        nframes = ndimv = 1
        if data.ndim == 4:
            nframes,nlines,ncols,ndimv = data.shape
        elif data.ndim == 3:
            if self._lfmt[6]>1: 
                nlines,ncols,ndimv = data.shape
            else:
                nframes,nlines,ncols = data.shape
        elif data.ndim == 2:
            nlines,ncols = data.shape
        elif data.ndim == 1:
            nlines,ncols = 1,data.size
        else:
            print('write:error: too many dimensions in data')
        
        # check consistence between image and data dimensions
        if ncols != self._lfmt[4]:
            print('write:error: incompatible size (width) between image and data')
            return
        if ndimv != self._lfmt[6]:
            print('write:error: incompatible size (components) between image and data')
            return
        if nframes>1 and nlines != self._lfmt[5] != nlines:
            print('write:error: incompatible size (height) between image and data')

        
        # pack data if needed, copy in auxiliary array, as pack works inplace
        data_copy = np.array(data,dtype=self._storage)
        if self._lfmt[3] == -1:           
            ptr = data_copy.__array_interface__['data'][0]
            lib.c_pckbt( cast(ptr,c_void_p), cast(ptr,c_void_p),
                         nframes*nlines*self._lfmt[0], -self._lfmt[2])
        else:
            ptr = data_copy.__array_interface__['data'][0]

        # write data with cast to void*
        lib.c_ecr( self._nf, nframes*nlines, cast(ptr,c_void_p))

        # return
        if interpreter:
            print 'write a total of ' + str(nframes*nlines) + \
                'lines to ' + self._filename
        return nframes*nlines
 

    def seek(self,offset=1,access=None):
        """
        int * str -> None

        Set the file pointer position to a specific line in the
        current frame, or at the begin of a specific frame if
        access=='frame'. offset is an index beginning at 1.  Negative
        number gives a position from the end of the current frame.
        
        Examples:
           img.seek(1)          # go at the first line or current frame
           img.seek(2,'frame')  # go at the beginning of the second frame
           img.seek(-1)         # go at the beginning of the last line of current frame

        See also: tell()

        """
        if self._nf > 0:            
            if access and access == 'frame':
                # renormalize negative offset
                if offset < 0: offset = self._lfmt[7] + offset                
                if offset > 0 and offset <= self._lfmt[7]:
                    lib.c_lptset(self._nf, 1 + (offset-1) * self._lfmt[5])
                else:
                    print('seek:error: bad offset')
            else: # offset is a line number in current frame
                # determine current frame
                fpt = (lib.c_lptget(self._nf)-1) // self._lfmt[5]
                # renormalize negative offset
                if offset < 0: offset = self._lfmt[5] + offset
                if offset > 0 and offset <= self._lfmt[5]:
                    lib.c_lptset(self._nf, fpt * self._lfmt[5] + offset)
                else:
                    print('seek error: bad offset')

    def tell(self, access=None):
        """
        str -> int

        Return the current line index in the current frame, or the
        current frame index if access == 'frame'. Indexes start to 1.

        See also: seek()

        """
        if self._nf >0:
            if access and access == 'frame':
                return 1 + (lib.c_lptget(self._nf)-1) // self._lfmt[5]
            elif access and access == 'absolute':
                return lib.c_lptget(self._nf)
            else:
                return 1 + (lib.c_lptget(self._nf)-1) % self._lfmt[5]

    def setdims(self,dims):
        """
        tuple[int,int] -> NoneType

        Set the dimensions (width,height) of the image.

        See also: setwidth(), setheight(), getdims()
        """
        self._lfmt[4],self._lfmt[5] = dims
        self._lfmt[0] = self._lfmt[4]*self._lfmt[6]
        self._lfmt[1] = self._lfmt[5]*self._lfmt[7]
        
    def getdims(self):
        """
        NoneType -> tuple[int,int]

        Return the dimensions (width,height) of the image.

        See also: getwidth(), getheight(), setdims()
        """
        return (int(self._lfmt[4]),int(self._lfmt[5]))

    def setwidth(self,width):
        """
        int -> NoneType

        Set the width (number of pixels per line) of the image.

        See also: getwidth(), setdims()
        """
        self._lfmt[4] = width
        self._lfmt[0] = self._lfmt[4]*self._lfmt[6]
        
    def getwidth(self):
        """
        NoneType -> int

        Get the width (number of pixels per line) of the image.

        See also: setwidth(), getdims()
        """
        return int(self._lfmt[4])

    def setheight(self,height):
        """
        int -> NoneType

        Set the height (number of line per frame) of the image.

        See also: getheight(), setdims()
        """
        self._lfmt[5] = height
        self._lfmt[1] = self._lfmt[5]*self._lfmt[7]

    def getheight(self):
        """
        NoneType -> int

        Get the height (number of line per frame) of the image.

        See also: setheight(), getdims()
        """
        return int(self._lfmt[5])

    def setcomponents(self,components):
        """
        int -> NoneType

        Set the number of components (number of values per pixel).

        See also: getcomponents()
        """
        self._lfmt[6] = components
        self._lfmt[0] = self._lfmt[4]*self._lfmt[6]
        
    def getcomponents(self):
        """
        NoneType -> int

        Get the number of components (number of values per pixel).

        See also: setcomponents()
        """
        return int(self._lfmt[6])

    def setframes(self,frames):
        """
        int -> NoneType

        Set the number of frames of a sequence of images.

        See also: getframes()
        """
        self._lfmt[7] = frames
        self._lfmt[1] = self._lfmt[5]*self._lfmt[7]
    
    def getframes(self):
        """
        NoneType -> int

        Get the number of frames of a sequence of images.

        See also: setframes()
        """
        return int(self._lfmt[7])    

    def setexponent(self,exponent):
        """
        int -> NoneType

        With writef() and readf(), image values are always considered
        as floating value. If precision is fixed, exponent gives the
        position of ..., i.e. image values are multiply by
        2**exponent.

        See also: getexponent()

        """
        if self._lfmt[3] != 1:
            if self._lfmt[8] > 0:
                self._lfmt[8] = 200+exponent
            else:
                self._lfmt[8] = -(200+exponent)

    def getexponent(self):
        """
        NoneType -> int

        Return the exponent of an image having a fixed precision. 

        See also: setexponent()
        """
        if self._lfmt[3] != 1:
            if self._lfmt[8] > 0:
                return self._lfmt[8] - 200
            else:
                return self._lfmt[8] + 200
        else:
            return 0

    def setcolors(self,colors):
        """
        Array(256,3) -> None

        Write a colormap in an image. The image header should have a
        size of 8.  Optionnal parameter hrd of create() can set the
        image header size. setcolors() on existing image with a too
        small header size is without effect.

        Examples:
          - on a existing image:
             im = InrImage('image.inr')
             gray = ...
             im.setcolors(gray)
          - creating a new image
             im = InrImage ('uint8',128,64)
             im.create('myimage.inr',hdr=8)
             im.setcolors(gray)

        """
        if self._nf:
            # r=colors[:,0] ne fonctionne pas car c'est une copie
            # de pointeur. colors est rangée en 'row major', alors
            # qu'il faudrait qu'elle soit 'column major'. On fait
            # donc des vraies copies (élément par élément) de vecteurs.
            r = np.array(colors[:,0],dtype=c_uint8)
            g = np.array(colors[:,1],dtype=c_uint8)
            b = np.array(colors[:,2],dtype=c_uint8)
            lib.iwr_ctrgb( self._nf, 0, 256,
                           cast(r.__array_interface__['data'][0],c_void_p),
                           cast(g.__array_interface__['data'][0],c_void_p),
                           cast(b.__array_interface__['data'][0],c_void_p))
        return None

    def getcolors(self):
        """
        None -> Array(255,3,dtype=uint8) | None

        Return the colors table of an image and None if the image has not.

        Example:
            im = InrImage('image.inr')
            # get colors table
            tcol = im.getcolors()
            # read image
            data = im.read()
            im.close()
            if tcol != None:
                # get the colored image
                cdata = tcol[data]
       
        See also: setcolors()
        """
        if self._nf:
            i0 = np.zeros(1,dtype=c_int)
            nb = np.zeros(1,dtype=c_int)
            tabr = np.zeros(256,dtype=c_uint8)
            tabg = np.zeros(256,dtype=c_uint8)
            tabb = np.zeros(256,dtype=c_uint8)
            ret = lib.ird_ctrgb( self._nf, i0, nb,
                                 cast(tabr.__array_interface__['data'][0],c_void_p),
                                 cast(tabg.__array_interface__['data'][0],c_void_p),
                                 cast(tabb.__array_interface__['data'][0],c_void_p),
                                 256)
            if ret > 0:
                colors=np.zeros((256,3),dtype=c_uint8)
                colors[:,0] = tabr
                colors[:,1] = tabg
                colors[:,2] = tabb
                return colors        
        return None
    
    def setcoding(self,coding):
        """ 
        NoneType -> str

        Define coding image values as they will be stored on the disc. Available coding are
         - 'float', 'float32', 'double', 'float64',
         - 'uintn' or 'intn' where n stands for the number of bits, 'uint8' for instance,
         - 'puintn' or 'pintn' for a 'PACKEE' format, for instance use 'puint1' to 
           code a binary image, each value getting exactly one bit on disk

        See also: getcoding()
        """
        bsize = 0
        mode = coding
        if mode == 'float' or mode == 'float32':    # format REELLE, simple precision
            itype,bsize,exp = 1,4,0
        elif mode == 'double' or mode == 'float64': # format REELLE, double precision
            itype,bsize,exp = 1,8,0
        else:
            if mode[0] == 'p':                      # format PACKEE
                itype,exp = -1,-200
                mode=mode[1:]
            else:                                   # format FIXEE
                itype,exp = 0,-200
            if mode[0] == 'u':
                exp = 200
                mode = mode[1:]
            if mode[0:3] == 'int':
                nbits=int(mode[3:])
                if nbits % 8 == 0 and itype == 0:
                    bsize= nbits//8
                else:
                    bsize=-nbits
        if bsize == 0:  print('setcoding: coding '+coding+' unknown')
        else:
            self._lfmt[2]=bsize
            self._lfmt[3]=itype
            self._lfmt[8]=exp

    def getcoding(self):
        """
        NoneType -> str

        Returns coding image values as they are stored on the disc.

        See also: setcoding()
        """
        # setcoding coding -> lfmt (interne)
        # getcoding lfmt (interne) -> coding
        coding=''
        if self._lfmt[3] == 1:
            if self._lfmt[2] == 4: coding = 'float32'
            if self._lfmt[2] == 8: coding = 'float64'
        else:
            if self._lfmt[3] == -1: coding = 'p'
            if self._lfmt[8]>0: coding += 'u'
            coding += 'int'
            if self._lfmt[2]<0: coding += str(-self._lfmt[2])
            else: coding += str(8*self._lfmt[2])
        return coding
    
    # utils
    def _setstorage(self):
        """
        Cette fonction calcule la classe Numpy adequate pour stocker les
        donnees d'une image. La valeur est placée dans la variable
        privée _storage.
        """
        if self._lfmt[3] in (0,-1):  # virgule fixe
            if self._lfmt[8]>0: self._storage='u'
            if self._lfmt[2] < 0: nbytes = (7-self._lfmt[2])//8;
            else: nbytes = self._lfmt[2]
            if nbytes == 1: self._storage += 'int8'
            elif nbytes == 2: self._storage += 'int16'
            elif nbytes == 4: self._storage += 'int32'
            else: print('error 4 (incorrect bit/type)')
                  
        elif self._lfmt[3] == 1: # virgule flottante
            if self._lfmt[2] == 4: self._storage = 'float32'
            elif self._lfmt[2] == 8: self._storage = 'float64'
            else: print('error 4 (incorrect bit/type)')

        else:
            print('error 4 (incorrect bit/type)')

    def _msg(self,deb):
        msg=deb+' ('+str(self._lfmt[4])+'x'+str(self._lfmt[5])
        if self._lfmt[6]>1: msg += 'x'+ str(self._lfmt[6])
        msg += ' with'
        if self._lfmt[3] == 0 and self._lfmt[2]==4: msg += ' single precision'
        elif self._lfmt[3] == 0 and self._lfmt[2]==8: msg += ' double precision'
        else:
            if self._lfmt[8]<0: msg += ' signed'
            if self._lfmt[3] == -1: msg += 'packed values on ' + str(-self._lfmt[2]) + ' bit(s)'
            else: msg += ' fixed values on ' + str(self._lfmt[2]) + ' byte(s)'
            
        if self._lfmt[7]>1: msg += ' and '+str(self._lfmt[7]) + ' frames'
        print (msg+')')
        
############

def imread(name,frame=None,nframes=None):
    """ 
    str * int * int -> Array

    Open an image, read it and return pixels values.
    
    If frame = None, read the whole image, otherwise start
    the reading at given frame number (index begin to 1).

    If nframes != None, read nframes frames from the position given 
    by parameter frame.
    
    """
    img = InrImage(name)
    tcol = img.getcolors()

    if frame:
        img.seek(frame,'frame')
        if nframes:
            data = img.read(nframes,'frame')
        else:
            data = img.read(0,'frame')
    else:
        data = img.read(0,'frame')
        
    if tcol: data = tcol[data]
    img.close()
    return data

def imwrite(name,data):
    """ a faire """
    dimv=dimz=1
    if data.ndim == 2:
        (dimx,dimy)=data.shape
    if data.ndim == 3:
        (dimx,dimy,dimv)=data.shape
    if data.ndim == 4:
        (dimz,dimx,dimy,dimv)=data.shape
    img = InrImage(str(data.dtype),dimx,dimy,dimv,dimz)
    img.create(name)
    img.write(data)
    img.close()

def imload(name):
    """ a faire """
    img = InrImage(name)
    data = img.readf()
    coding = img.getcoding()
    img.close()
    return (data,coding)

def imsave(name,data,coding):
    """ todo """
    print("inrsave: todo")


#if __name__ == '__main__':
#    import inrimage

