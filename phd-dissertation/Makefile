FILE_TEX=dissertation

all: pdflatex

pdflatex: clean	
	pdflatex -shell-escape ${FILE_TEX}.tex
	# Uncomment makeindex if the document contains an index
	makeindex ${FILE_TEX}.nlo -s nomencl.ist -o ${FILE_TEX}.nls
	bibtex ${FILE_TEX}
	pdflatex -shell-escape ${FILE_TEX}.tex
	pdflatex -shell-escape ${FILE_TEX}.tex

rtf: clean	
	latex ${FILE_TEX}.tex
	# Uncomment makeindex if the document contains an index
	makeindex ${FILE_TEX}.nlo -s nomencl.ist -o ${FILE_TEX}.nls
	bibtex ${FILE_TEX}
	latex ${FILE_TEX}.tex
	latex ${FILE_TEX}.tex
	latex2rtf ${FILE_TEX}.tex

view:
	# Open the pdf document with evince
	evince ${FILE_TEX}.pdf &

preview:
	latexmk -pdf -pvc ${FILE_TEX}.tex

style:
	./style-check-0.14/style-check.rb */*tex | grep -v "paragraph break\|(queueing)\|(Queueing)\|(<)\|(>)\|(d\")\|(=\")\|:     \|[A-Z]\\. [A-Z])\|[0-9]-[0-9])"

clean:
	# Cleaning ${FILE_TEX} related files...
	ls ${FILE_TEX}.* | grep -v \.tex$ | grep -v \.bib$ | xargs rm -fv
	# Cleaning other tex related files if applicable...
	rm -fv *log *aux *dvi *lof *lot *bit *idx *glo *bbl *ilg *toc *ind *blg *out *nlo *brf *nls *pdf 
	# Cleaning in subdirectories *.aux files...
	find . -regex '.*.aux' -print0 | xargs -0 rm -rfv
	# Cleaning in subdirectories *.log files...
	find . -regex '.*.log' -print0 | xargs -0 rm -rfv
	# Cleaning in subdirectories *.bbl files...
	find . -regex '.*.bbl' -print0 | xargs -0 rm -rfv
	# Cleaning in subdirectories *.blg files...
	find . -regex '.*.blg' -print0 | xargs -0 rm -rfv
	# If there are other generated files, add the previous command again with the proper extension
	latexmk -C


