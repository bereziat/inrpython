/* procedure d'ecriture de n ligne d'image */
/* avec conversion en fixe si necessaire */
#include <stdio.h>
#include <inrimage/image.h>
#include <inrimage/error.h>
extern debug_;

ecrflt_(nf,nlig,a)
struct image **nf;
Fort_int *nlig;
CHAR *a;
{
	c_ecrflt(*nf,(int)*nlig,a);
}

c_ecrflt(nf,nlig,a)
struct image *nf;
int nlig;
float *a;
{
	Fort_int icodi[2], iexpi;
	int nb_pixels;

	icodi[0] = sizeof(float);
	icodi[1] = REELLE;

	iexpi = 0;

	if ( nf->TYPE != REELLE  || nf->BSIZE != sizeof(float)) {
		nb_pixels = nf->DIMX * nlig;
		c_cnvtbg(a,a,nb_pixels,icodi,&(nf->BSIZE),iexpi,nf->EXP);
	}
	c_ecr(nf,nlig,a);
}

/*
 * ecriture image avec capture du point de reprise en cas
 * d'erreur (uitle pour bind Python par exemple)
 */
c_ecrfltce(nf,nlig,a)
struct image *nf;
int nlig;
float *a;
{
  int ier = 0;
  silent_err();
  c_erreur(ier);
  if( ier != 0) return ier;
  c_ecrflt(nf,nlig,a);

}
