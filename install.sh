#!/bin/bash
# installation du module (version beta et naive)

INRPYTHONDIR=${INRPYTHONDIR:-/usr/local/inrpython}
INRIMAGESRC='--no-check-certificate http://www-pequan.lip6.fr/~bereziat/inrimage/dist/latest/inrimage.tar.gz'

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
    *) echo "To change the installation directory, type:"
       echo "INRPYTHONDIR=path_to_install_inrpython ./install.sh"
       echo "Installation aborted"
       exit 1;;
esac

case $1 in    
    -nc)
	;;
    *)
	TEMPD=$(mktemp -d)
	mkdir -p $INRPYTHONDIR $TEMPD
	(
	    cd $TEMPD
	    pwd
	    wget $INRIMAGESRC
	    tar xfz inrimage.tar.gz
	    ls -la
	    cd inrimage-*
	    ./configure --prefix=$INRPYTHONDIR --enable-shared
	    cd src/inrimage
	    make
	    if [ -w $INRPYTHONDIR ]; then
		make install
	    else
		sudo make install
	    fi
	)
	rm -rf $TEMPD
	;;
esac

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
