/* procedure d'ecriture de n ligne d'image
   subroutine ecr(nf,nlig,buf)
 = ecr_(nf,nlig,buf)
 versions "C direct" :
 		c_ecr(nf,nlig,buf)
 		c_xecr(nf,nlig,buf,flg_pad)
		arg passes par valeur, flg_pad =1 ==> le padding y est deja 

	c_pecr(nf,nlig,buf,iy,lock)
	idem, mais on precise numero de ligne et si on veut un lock

!!!ATTENTION! on interdit l'ecriture sur une image reelle qui n'a pas
le meme type de flottant que la machine hote
*/



#include <inrimage/image.h>
#include <inrimage/error.h>
#include <stdio.h>
#include <stdlib.h>

#define BUFSIZE	256

extern debug_;

ecr_(nf,nlig,a)
struct image **nf;
register Fort_int *nlig;
register CHAR *a;
{
	c_xecr(*nf,(int)*nlig,a,0);
}

c_ecr(nf,nlig,a)
register struct image *nf;
register int nlig;
register void *a;
{
	c_xecr(nf,nlig,a,0);
}

/*
 * écriture image avec capture du point de reprise en cas
 * d'erreur (uitle pour bind Python par exemple)
 */

c_ecrce(nf,nlig,a)
register struct image *nf;
register int nlig;
register void *a;
{
  int ier = 0;

  silent_err();
  c_erreur(ier);
  if( ier != 0) return ier;
  c_xecr(nf,nlig,a,0);
  return 0;
}

/* ecriture generalisee pour machine parallele */
c_pecr(nf,nlig,a,iy,lock)
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
	c_xecr(nf,nlig,a,0);
#ifdef HAS_PTHREADS
	if(lock > 0)
		pthread_mutex_unlock(&nf->nf_lock);
#endif
}

c_xecr(nf,nlig,a,flg_pad)
register struct image *nf;
int nlig;
CHAR a[];
int flg_pad;
{

	int no_byte, 	/* numero du byte de depart de l'ecriture */
	    nb_byte;	/* nb de bytes a ecrire */
	int hors_tout,	/* taille hors_tout d'une ligne d'image */
	    bits_ligne;	/* taille en bits d'une ligne */

	if (debug_) fprintf(stderr,"%s ecr:%s(%d) %d lignes a partir de %d\n",xargv[0],
			nf->nom,nf->fd,nlig,nf->no_ligne );

	/* ecrire le header si necessaire */
	if(!(nf->hdr_stat & HST_HISTSET))
		nf->hdr_stat |= HST_HIST2SET;
	wr_imdesc(nf);
/* tests de validite */

	if ( 	nf->no_ligne > nf->DIMY ||
		nf->no_ligne < 1           ||
		nf->no_ligne + nlig -1 > nf->DIMY ) {
			imerror(9,"%s ecr:probleme avec %s ligne %d, nlig %d, DIMY %d\n",xargv[0],
				nf->nom,nf->no_ligne,nlig,nf->DIMY);
			exit(-1);
			}

	/* test de validite du flottant */
	if(nf->TYPE == REELLE) {
		if(nf->flt_conv > 0) {
			imerror(9,"%s ecr :PB!! flottant de %s different de celui de la machine hote\n",
				xargv[0],nf->nom);
			exit(-1);
		}
	}
	/* test de validite de l'ordre des bytes */
	if(nf->swap_needed != 0) {
		if(nf->swap_needed < 0) {
			nf->swap_needed = 0;
			fprintf(stderr,"ecr : Warning!! unknown byte order on %s\n",nf->nom);
		} else {
			imerror(9,"ecr : cannot write on %s (illegal byte order)\n",nf->nom);
		}
	}
/* calcul de l'adresse dans le fichier */

	bits_ligne = nf->bits_lig; /* taille d'une ligne en bits */

	hors_tout = nf->hors_tout; /* taille d'une ligne y compris padding */
	no_byte = (nf->no_ligne -1) * hors_tout;
	nb_byte = (nlig) * hors_tout;

	no_byte += nf->desc_size;

	if(debug_) fprintf(stderr,"%s ecr:buff @ 0x%x no_byte %d nb_byte %d\n",xargv[0],
			&a[0],no_byte,nb_byte);

/* lseek seulement si necessaire */

	if ( no_byte != nf->byte_pnt )
		{
		if (debug_) fprintf(stderr,"%s ecr:lseek byte %d\n",xargv[0],no_byte);
		if ( (nf->byte_pnt = lseek(nf->fd,(off_t)no_byte,0L)) == -1 )
			{
			perror("ecr");
			imerror(1,"ecr: seek error %d\n",errno);
			exit(-1);
			}
		}

/* ecriture dans le fichier */

	if ( hors_tout * 8 != bits_ligne && flg_pad == 0)

		{ /* on padde chaque ligne a frontiere d'octet */

		if ( write_pad(nf->fd,a,nlig,bits_ligne) == -1 )
			{
			perror("ecr");
			imerror(1,"%s ecr:(write err %d) %s ligne %d\n",
				xargv[0],errno,nf->nom,nf->no_ligne);
			exit(-1);
			}


		}
	else

		{ /* on est deja a frontiere d'octet */

		if ( write(nf->fd,a,nb_byte) == -1 )
			{
			perror("ecr");
			imerror(1,"%s ecr:(write err %d) %s ligne %d\n",
				xargv[0],errno,nf->nom,nf->no_ligne);
			exit(-1);
			}
		}
/* mise a jour des pointeurs */

	nf->no_ligne += nlig;
	nf->byte_pnt += nb_byte;

}

/* ecriture de lignes paddees pour les mettre a frontiere d'octet */

write_pad(fd,a,nlig,bits_ligne)
int fd,nlig,bits_ligne;
CHAR a[];
{

	int b,emetteur,recepteur,move,nb_char,n;
	CHAR buffer[BUFSIZE];


	recepteur = emetteur = 1 ; /* mvbits compte a partir de 1 */
	nb_char = 0;

	while ( nlig-- )
		{	/* pour chaque ligne */

		b = bits_ligne;

		while ( b > 0 )
			{ /* on transfere au maximum BUFSIZE octets */

			move = ( b < BUFSIZE*8 ? b : BUFSIZE*8 );
			c_mvbits(a,buffer,emetteur,recepteur,move);

			b -= move;
			emetteur += move;

			move = (move+7)/8;
			if ( (n = write(fd,buffer,move)) == -1 ) return(-1);
			nb_char += n;
			}
		}

	return(nb_char);
}
