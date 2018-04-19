/* procedure de lecture de n ligne d'image */
/* avec conversion en flottant si necessaire */
#include <stdio.h>
#include <inrimage/image.h>
#include <inrimage/error.h>
extern debug_;

lecflt_(nf,nlig,a)
struct image **nf;
Fort_int *nlig;
CHAR *a;
{
	c_lecflt(*nf,(int)*nlig,a);
}

c_lecflt(nf,nlig,a)
struct image *nf;
int nlig;
float *a;
{
	int nb_pixels;
	Fort_int icodo[2],iexpo;

	icodo[0] = sizeof(float);
	icodo[1] = REELLE;

	iexpo = 0;

	c_lect(nf,nlig,a);
	if ( nf->TYPE != REELLE || nf->BSIZE != sizeof(float)) {
		nb_pixels = nf->DIMX * nlig;
		c_cnvtbg(a,a,nb_pixels,&(nf->BSIZE),icodo,nf->EXP,iexpo);
	}


}

/*
 * écriture image avec capture du point de reprise en cas
 * d'erreur (uitle pour bind Python par exemple)
 */

c_lecfltce(nf,nlig,a)
struct image *nf;
int nlig;
float *a;
{
  int ier;
  silent_err();
  c_erreur(ier);
  if( ier != 0) return ier;
  lecflt_(&nf,&nlig,a);
  return 0;
}
