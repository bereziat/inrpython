/* procedure de lecture de n ligne d'image 
   subroutine lect(nf,nlig,buf)
 = lect_(nf,nlig,buf)
 versions "C direct" :
 		c_lect(nf,nlig,buf)
 		c_xlect(nf,nlig,buf,flg_pad)
		arg passes par valeur, flg_pad =1 ==> ne pas supprimer le padding de ligne 

	c_plect(nf,nlig,buf,iy,lock)
	idem, mais on precise numero de ligne et si on veut un lock

!!! CONVERSION AUTOMATIQUE des flottants en lecture selon le type de machine 
SWAP AUTOMATIQUE des entiers > 8 bits si necessaire
*/

#include <sys/types.h>
#include <stdio.h>
#include <stdlib.h>
#include <inrimage/image.h>
#include <inrimage/error.h>

extern off_t lseek();

#define BUFSIZE	256

extern debug_;

lect_(nf,nlig,a)
struct image **nf;
register Fort_int *nlig;
register CHAR *a;
{
	c_xlect(*nf,(int)*nlig,a,0);
}

c_lect(nf,nlig,a)
register struct image *nf;
register nlig;
register void *a;
{
	c_xlect(nf,nlig,a,0);
}

/*
 * lecture image avec capture du point de reprise en cas
 * d'erreur (uitle pour bind Python par exemple)
 */
c_lectce(nf,nlig,a) 
  register struct image *nf;
  register nlig;
  register void *a;
{
  int ier = 0;

  silent_err();
  c_erreur( ier);
  if( ier != 0) return ier;

  c_xlect(nf,nlig,a,0);
  return 0;
}

/* lecture generalisee pour machine parallele */
c_plect(nf,nlig,a,iy,lock)
register struct image *nf;
register nlig;
register void *a;
register iy, lock;
{
#ifdef HAS_PTHREADS
	if(lock > 0)
		pthread_mutex_lock(&nf->nf_lock);
#endif
	c_lptset(nf,iy);
	c_xlect(nf,nlig,a,0);
#ifdef HAS_PTHREADS
	if(lock > 0)
		pthread_mutex_unlock(&nf->nf_lock);
#endif
}

/* si flg_pad == 1, on ne supprime pas le padding des lignes */
c_xlect(nf,nlig,a,flg_pad)
register struct image *nf;
int nlig;
CHAR a[];
int flg_pad;
{
	int no_byte, 	/* numero du byte debut de lecture */
	    nb_byte;	/* nb de bytes a lire */
	int hors_tout,	/* taille hors tout d'une ligne d'image */
	    bits_ligne;	/* taille en bits d'une ligne */

	int n,alire,dummies;
	CHAR *buf;
	buf = a;   /* pour garder l'adresse */
	if (debug_) fprintf(stderr,"%s lect:%s(%d) %d lignes a partir de %d\n",xargv[0],
			nf->nom,nf->fd,nlig,nf->no_ligne );

	
/* tests de validite */

	if ( 	nf->no_ligne > nf->DIMY ||
	    nf->no_ligne < 1           ||
	    nf->no_ligne + nlig -1 > nf->DIMY ) {
		imerror(9,
			"lect:debordement avec %s ligne debut %d et fin %d (DIMY %d)\n",
			nf->nom,nf->no_ligne,nf->no_ligne + nlig - 1,nf->DIMY);
		exit(-1);
	}


/* calcul de l'adresse dans le fichier */

	bits_ligne = nf->bits_lig; /* taille d'une ligne en bits */

	hors_tout = nf->hors_tout; /* taille d'une ligne
						y compris le padding */
	no_byte = (nf->no_ligne -1) * hors_tout;
	nb_byte = (nlig) * hors_tout;

	no_byte += nf->desc_size;

	if(debug_) fprintf(stderr,"%s lect:buff @ 0x%x, no_byte %d, nb_byte %d\n",xargv[0],
			&a[0],no_byte,nb_byte);

/* lseek seulement si necessaire */

	if ( no_byte != nf->byte_pnt )
		{
		if ( (nf->f_type & FL_PIPE) && no_byte > nf->byte_pnt ) {
			 /* c'est un pipe et on peut lire en avant */
			alire = (no_byte - nf->byte_pnt) / hors_tout;
			nf->no_ligne -= alire;
			while ( alire ) {  /* skip */
				dummies = ( alire < nlig ? alire : nlig );
				c_xlect(nf,dummies,a,flg_pad);
				alire -= dummies;
			}
		} else {
			if (debug_) fprintf(stderr,"%s lect:lseek byte %d\n",
					    xargv[0],no_byte);
			if ( (nf->byte_pnt = (int)lseek(nf->fd,(off_t)no_byte,0)) == -1) {
				perror("lect");
				imerror(1,"lect : seek error %d\n",errno);
				exit(-1);
			}
		}
	}

/* lecture dans le fichier */

	if ( hors_tout * 8 != bits_ligne && flg_pad == 0) { /* on supprime le padding sur chaque ligne */

		if ( (n = read_pad(nf->fd,a,nlig,bits_ligne)) <= 0 ) {
			if ( n != 0 ) perror("lect");
			imerror(1,
				"%s lect:read code %d (errno %d) avec %s entre les lignes %d et %d\n",
				xargv[0],n,errno,nf->nom,nf->no_ligne,nf->no_ligne + nlig - 1);
			exit(-1);
		}
	} else {
		 /* on est deja a frontiere d'octet */
		if((n = read_all(nf->fd,a,nb_byte)) != nb_byte) {
			imerror(1,
				"%s lect:read  code %d (errno %d) avec %s entre les lignes %d et %d\n",
				xargv[0],n,errno,nf->nom,nf->no_ligne,nf->no_ligne + nlig - 1);
			exit(-1);
		}
	}
/* mise a jour des pointeurs */

	nf->no_ligne += nlig;
	nf->byte_pnt += nb_byte;
	/* conversion de flottant si necessaire */
	if(nf->flt_conv < 0) {
		fprintf(stderr,"lect : Warning! float type undefined on %s\n",nf->nom);
		nf->flt_conv = 0;
		return 1 /* makes c99 happy */; 
	} else if(nf->flt_conv > 0) {
		if(nf->lfmt[I_BSIZE] == 8)
			n = c_cnvfl8((float *)buf,nlig * nf->DIMX,nf->float_typ);
		else
			n = c_cnvflt((float *)buf,nlig * nf->DIMX,nf->float_typ);
		if(n < 0)
			imerror(9,"lect: float conversion impossible\n");
		nf->cnv_ovf += n;
	}
	/* swap des int si necessaire */
	if(nf->swap_needed == 0) return 1 /* makes c99 happy */; 
	if(nf->swap_needed < 0) {
		fprintf(stderr,"lect : Warning! int byte order undefined on %s\n",nf->nom);
		nf->swap_needed = 0;
		return 1 /* makes c99 happy */; 
	}
	if(nf->swap_needed == 1)
		swapshort((unsigned short *)buf,nlig * nf->DIMX);
	else if(nf->swap_needed == 2)
		swapint4((u_int4 *)buf,nlig * nf->DIMX);
	else
		imerror(9,"lect : incorrect swap type (%d)\n",nf->swap_needed);
}




/* lecture de lignes paddees et suppression du padding */

read_pad(fd,a,nlig,bits_ligne)
int fd,nlig,bits_ligne;
CHAR a[];
{
	int b,emetteur,recepteur,move,n,alire,nb_char;
	CHAR buffer[BUFSIZE];
	CHAR *pbuf;

	recepteur = emetteur = 1 ; /* mvbits compte a partir de 1 */
	nb_char = 0;

	while ( nlig-- )
		{	/* pour chaque ligne */

		b = bits_ligne;

		while ( b > 0 )
			{ /* on transfere au maximum BUFSIZE octets */
	
			move = ( b < BUFSIZE*8 ? b : BUFSIZE*8 );
			alire = (move+7)/8;
#ifdef OLDVERSION
			pbuf = buffer;

			while ( alire > 0 ) /* on boucle jusqu'a lire nb_byte */
				{
				if ( (n = read(fd,pbuf,alire)) <= 0 )
							return(n);
				nb_char += n;
				alire -= n;
				pbuf += n;
				}
#else
			if((n = read_all(fd,buffer,alire)) != alire)
				return -1;
			nb_char += n;
#endif
			c_mvbits(buffer,a,emetteur,recepteur,move);

			b -= move;
			recepteur += move;
			}
		}

	return(nb_char);

}

