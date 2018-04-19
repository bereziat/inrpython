#include <inrimage/inrlocal.h>
#include <inrimage/image.h>
#include <inrimage/error.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static int err_recup();

static CHAR *tmpname;
static int tmpfd;

extern struct error error_;
extern int khoros_mode;
extern int debug_;

/*
 **** image
  	FUNCTION IMAGE(NOM,MODE,VERIF,GFMT)
	Inrimage *image_(nom,mode,verif,gfmt)
	char *nom, *mode, *verif;
	struct nf_fmt *gfmt;
ouvre un fichier image de nom nom.
Si le nom se termine par .Z ou .gz, on appelle zcat et on remplace par '<'
mode: 	"e" : image en entree, doit exister. test de format selon 'verif'.
		reste du format renvoye dans lfmt.
	"s" : en sortie. on la cree si n'existe pas. si existe, lfmt est compare
		a son format selon le parametre verif, le reste est renvoye
	"t" : image temporaire (mktemp). lfmt doit contenir le format
		(verif force a 'a'). Le fichier sera ensuite detruit
	"c": image en ecrasement, detruite et recree selon lfmt (verif force a 'a')
	"C": image en ecrasement, avec verification selon 'verif'
NB: si le 2e caractere de mode est 'x' (extension) gfmt est de type struct nf_fmt
	sinon c'est lfmt[9];
NB2: lors d'un appel a partir du fortran il faut TOUJOURS donner 2 caractères 
(espace ou x pour le 2e),
car le fortran ne met pas de nul à la fin des strings
verif : definit la partie du format a verifier (codage ou dimensions)
	si l'image existe on compare gfmt et le header du fichier
	si l'image n'existe pas, on demande interactivement la partie qui
		n'est pas a verifier
	"","  ": ne rien verifier.
	"t": verifier codage et type
	"tx" : verifier codage, type + bias et scale (il faut mode[1] == 'x')
	"d": verifier les dimensions
	"dx": verifier les dimensions + maille et offsets (il faut mode[1] == 'x')
	"a": equivalent a t + d
	"ax" : equivalent a tx + dx
NB: lors d'un appel a partir du fortran il faut TOUJOURS donner 2 caractères 
(espace ou x pour le 2e),
car le fortran ne met pas de nul à la fin des strings

NOTE: si le nom de fichier est precede de '>', le mode "s" est transforme' en 'C'
En mode KHOROS on reconnait fi;e= et shm=
*/

extern Inrimage *c_imouv();

#define LG_FNAME 512

/* copie au maximum maxsize char de src dans dest, jusqu'a '\0' exclu et ajoute un 0 */
static void fortstr_to_str(char *dest,char *src,int maxsize) {
  char c;
  while(maxsize-- > 0) {
    if((c = *src++) == 0)
      break;
    if (c == '\\' && *src == '0')
      break;
    *dest++ = c;
  }
  *dest = 0;
}

static Inrimage *imagepriv_(nom,mode,verif,gfmt)
char *nom,*mode,*verif;
struct nf_fmt *gfmt;
{
	Inrimage *nf;
	CHAR texte[LG_FNAME];
	register ext;
	//	CHAR *firstblank;
	register ver_opt = 0;
	char nvol[4], sf[4];  /* unused */
	register char lmod;
	register CHAR *name;

	/* initialisations */
	texte[LG_FNAME -1] = '\0';
	
	if ( (gfmt->DIMX != gfmt->NDIMX*gfmt->NDIMV) ||
	    (gfmt->DIMY != gfmt->NDIMY*gfmt->NDIMZ) ) {
		if(gfmt->DIMX == 0 || gfmt->DIMY == 0) {  /* non initialise */
			gfmt->DIMX = gfmt->NDIMX*gfmt->NDIMV;
			gfmt->DIMY = gfmt->NDIMY*gfmt->NDIMZ;
		} else {
			/* on suppose que c'est le format court */
			gfmt->NDIMX = gfmt->DIMX;
			gfmt->NDIMY = gfmt->DIMY;
			gfmt->NDIMV = gfmt->NDIMZ = 1;
			gfmt->EXP = 200;
		}
	}
	if(gfmt->EXP == 0)
		gfmt->EXP = 200;

	if ( nom[0] == '?' ) { /* interactif */
#ifdef NONINTERACTIF
		imerror(9,"Cette version de 'image' n'admet pas le mode interactif\n");
#else
		fortstr_to_str(texte,&nom[1],LG_FNAME-1);
		gtnmim_(texte,nvol,texte,sf);
#endif
	} else { /* non interactif */
	  /*	if(strlen(nom) > LG_FNAME -1)
		imerror(9,"image_ : nom de fichier trop long (max %d)\n",LG_FNAME-1); */
		fortstr_to_str(texte,nom,LG_FNAME-1);
		//  on veut accepter des noms de fichiers avec des espaces
		//		if ( (firstblank = index(texte,' ')) != 0 ) *firstblank = '\0';

	}
	// verif stricte des paramètres mode et verif
	if(verif[0] != 0 && 
	   (verif[1] != ' ' && verif[1] != 'x' && verif[1] != 0))
	  imerror(9,"image: paramètre verif incorrect\n");
	ver_opt = 0;
	ext = 0;
	if(mode[0] != 0) {
	  if(mode[1] == 'x') {
	    ver_opt = VER_EXTEND;
	    if(verif[1] == 'x') ext = 1;
	  }
	  else if(mode[1] != ' ' && mode[1] != 0)
	    imerror(9,"image: paramètre mode incorrect\n");
	}
	switch ( verif[0] ) {
	case 'd' : /* dimensions imposees */
		ver_opt = VER_DIM;
		if(ext)
			ver_opt |= VER_OFF;
		break;
	case 't' : /* type et codage imposes */
		ver_opt |= VER_COD;
		if(ext) ver_opt |= VER_XCOD;
		break;
	case '\0' : /* rien n'est impose */
	case ' ' :
		break;

	case 'a' :
		/* tout est impose */
		ver_opt |= VER_DIM | VER_COD;
		if(ext) ver_opt |= VER_OFF | VER_XCOD;
		break;
	default: /* erreur */
		imerror(9,"%s:image, verif %s inconnue\n",
			xargv[0],verif);
		exit(-1);
	}
	tmpname = (CHAR *) 0;
	name = texte;
	lmod = mode[0];
#ifdef INR_KHOROS
	if(khoros_mode) {
		if(strncmp(name,"file=",5) == 0) {
			name += 5;
		} else if(strncmp(name,"shm=",4) == 0) 
			imerror(9,"Sorry! file type shm= not yet implemented");
		if((lmod == 's') && (khoros_mode == 2))
			lmod = 'C';
	}
#endif

	/* tester noms precedes de '>' */
	if((*name == '>') && (*(name +1) != 0)) {
		name++;
		if(lmod == 's')
			lmod = 'C';
	}
	switch ( lmod) {
	case 'e' : /* image en entree */
		if((*name == '<') && (*(name +1) != 0))
			imerror(9,"bad filename %s\n",texte);
		if ( access(name,4) == -1 && *name != '<' ) {
			imerror(1,"%s: access error %d with %s\n",
				xargv[0],errno,name);
			exit(-1);
		}

		break;
		
	case 's' : /* image en sortie */
		
		break;
		
	case 't' : /* image temporaire */
		
		ver_opt = ver_opt & VER_EXTEND ? VER_MASK : VER_COD | VER_DIM;
		tmpfd = mkstemp(name);
		tmpname = name;
		break;
		
	case 'c' : /* image en ecrasement */
		
		ver_opt = ver_opt & VER_EXTEND ? VER_MASK : VER_COD | VER_DIM;
		unlink(name);
		break;
		
	case 'C' : /* image en ecrasement, avec verif */
		
		unlink(name);
		break;
		
	default:
		imerror(9,"%s:image, mode %s inconnu\n",xargv[0],mode);
		exit(-1);
	}

	if(tmpname != (CHAR *)0) {
		error_.retadr = err_recup;
	}
	nf = c_imouv(name,gfmt,ver_opt);
	/* unlink si fichier temporaire */
	if(tmpname != (CHAR *)0) {
		unlink(tmpname);
		close(tmpfd);
	}
	return(nf);
}

static int err_recup(ier)
int ier;
{
	if(tmpname != (CHAR *)0) {
		unlink(tmpname);
		close(tmpfd);
	}
	bcherr_();
}


/* 
 * Ouverture image avec format simple.
 * Le caractere 'x' du mode s'il existe est systématiquement enlevé.
 */

Inrimage *image_(char *nom, char *mode, char *verif, Fort_int *gfmt) {
  char mode_[] = " ";
  mode_[0] = mode[0];
  if( mode[0] != '\0' && mode[1] == 'x')
    imerror(9, "mode etendu non permis\n");
  return imagepriv_(nom,mode_,verif,(NF_fmt*)gfmt);
}

/*
 * Ouverture image avec format étendu.
 * Le caractère 'x' du mode est systématiquement ajouté.
 */

Inrimage *imagex_( char *nom, char *mode, char *verif, NF_fmt *gfmt) {
  char mode_[] = " x";
  mode_[0] = mode[0];
  return imagepriv_(nom,mode_,verif,gfmt);
}

/*
 * Ouverture image et capture du point de reprise en cas 
 * d'erreur (utile pour bind pour Python par exemple)
 */

Inrimage *imagece_( char *nom, char *mode, char *verif, Fort_int *gfmt) {
  char mode_[] = " ";

  silent_err();
  c_erreur( gfmt[9]);
  if( gfmt[9] != 0) return NULL;
  
  mode_[0] = mode[0];
  if( mode[0] != '\0' && mode[1] == 'x')
    imerror(9, "mode etendu non permis\n");    
  return imagepriv_(nom,mode_,verif,(NF_fmt*)gfmt);
}
