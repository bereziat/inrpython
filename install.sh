#!/bin/bash
# installation du module (version beta et naive)

INRPYTHONDIR=/home/icare_l1/usr-fedora/inrpython
INRIMAGESRC=http://inrimage.gforge.inria.fr/dist/latest/inrimage.tar.gz

# Récupérer inrimage, ne compiler que la bibliothèque en mode partagée, et
# l'installer dans un répertoire isolé

case $1 in
    -h|-help|--help)
	cat <<EOF
usage : install.sh [-nc]
      -nc : no compile (libinrimage.a)
EOF
	exit 0
	;;
    -nc)
	
	;;
    *)
	TMPDIR=$(mktemp -d)
	mkdir -p $INRPYTHONDIR $TMPDIR
	patch=$(pwd)/patch
	(
	    cd $TMPDIR
	    wget $INRIMAGESRC
	    tar xfz inrimage.tar.gz
	    ls -la
	    cd inrimage-*
	    ./configure --prefix=$INRPYTHONDIR --enable-shared
	    cd src/inrimage
	    cp $patch/*.c .
	    make
	    make install
	)
	rm -rf $TMPDIR
	;;
esac

sed -r "/INRPYTHONPATH/d; s,libinrpath,'$INRPYTHONDIR/lib'," <inrimage.py >$INRPYTHONDIR/inrimage.py &&
    echo "-> install $INRPYTHONDIR/inrimage.py done"

read -p'Should I modify your ~/.bashrc ? (y/N)' yesno

case $yesno in
    y)
	echo "export PYTHONPATH=$INRPYTHONDIR:\$PYTHONPATH" >> ~/.bashrc
	;;
esac
