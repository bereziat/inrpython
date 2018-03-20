#!/bin/bash
# installation du module (version beta et naive)

INRPYTHONDIR=$(pwd)/usr
INRIMAGESRC=http://inrimage.gforge.inria.fr/dist/latest/inrimage.tar.gz

# Récupérer inrimage, compiler que la bibliothèque en mode partagée, et
# l'installer dans un répertoire isolée

TMPDIR=$(mktemp -d)
mkdir -p $INRPYTHONDIR $TMPDIR

(
    exit
    cd $TMPDIR
    wget $INRIMAGESRC
    tar xfz inrimage.tar.gz
    ls -la
    cd inrimage-*
    ./configure --prefix=$INRPYTHONDIR --enable-shared
    cd src/inrimage
    make
    make install
)
rm -rf $TMPDIR
sed -r "/INRPYTHONPATH/d; s,libinrpath,'$INRPYTHONDIR/lib'," <inrimage.py >$INRPYTHONDIR/inrimage.py

read -p'Should I modify your ~/.bashrc ? (y/N)' yesno

case $yesno in
    y)
	echo "export PYTHONDIR=\$PYTHONDIR:$INRPYTHONDIR" >> ~/.bashrc
	;;
esac
