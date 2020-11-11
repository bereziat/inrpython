#!/bin/bash
# installation du module (version beta et naive)

INRPYTHONDIR=/usr/local/inrimage/python
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
esac

read -p"inrpython will be installed in $INRPYTHONDIR. Is that correct? (y/N) "  yesno
case $yesno in
    y|Y) ;;
    *) echo "Edit this file and change the value of INRPYTHONDIR variable (line 4)"
       echo "Installation aborted"
       exit 1;;
esac

case $1 in    
    -nc)
	;;
    *)
	TMPDIR=$(mktemp -d)
	mkdir -p $INRPYTHONDIR $TMPDIR
	patch=$(pwd)/patch
	(
	    cd $TMPDIR
	    pwd
	    wget $INRIMAGESRC
	    tar xfz inrimage.tar.gz
	    ls -la
	    cd inrimage-*
	    ./configure --prefix=$INRPYTHONDIR --enable-shared
	    cd src/inrimage
	    cp $patch/*.c .
	    make
	    if [ -w $INRPYTHONDIR ]; then
		make install
	    else
		sudo make install
	    fi
	)
	rm -rf $TMPDIR
	;;
esac

set -x
TMPFILE=$(mktemp)
sed -r "/INRPYTHONPATH/d; s,libinrpath,'$INRPYTHONDIR/lib'," <inrimage.py >$TMPFILE

if [ -w $INRPYTHONDIR ]; then
    mv $TMPFILE $INRPYTHONDIR/inrimage.py
    cp -r bin $INRPYTHONDIR/
else
    sudo mv $TMPFILE $INRPYTHONDIR/inrimage.py
    sudo cp -r bin $INRPYTHONDIR/
fi

read -p'Should I patch your ~/.bash_profile? (y/N) ' yesno
case $yesno in
    y|Y)
	[ -f ~/.bash_profile ] && cp ~/.profile_bash ~/.bash_profile-$$
	echo "export PYTHONPATH=$INRPYTHONDIR:\$PYTHONPATH" >> ~/.bash_profile
	;;
esac
