PY = .venv/bin/python

.PHONY: lean-dry lean restore verify citations results pdf pdf-arxiv pdf-gov arxiv help
TEXBIN = $(HOME)/texlive/bin/universal-darwin

help:
	@echo "make pdf        # compile paper/main.tex -> paper/main.pdf (full TeX Live, two passes)"
	@echo "make verify     # re-run deterministic experiments, assert golden numbers reproduce (no data needed)"
	@echo "make results    # regenerate RESULTS.md from results/*.json + integrity check"
	@echo "make lean-dry   # show what raw data WOULD be freed (deletes nothing)"
	@echo "make lean       # delete re-downloadable raw data (~62 GB); keeps the <2 GB reproducible core"
	@echo "make restore    # re-download all raw data into the repo (all 8 CloudSEN12 bands incl B1/B8A)"
	@echo "make arxiv      # de-anonymized build + paper/arxiv_submission.tar.gz for arXiv upload"
	@echo "make citations  # resolve every bibliography entry against arXiv + Crossref"

pdf:
	cd paper && PATH="$(TEXBIN):$$PATH" pdflatex -interaction=nonstopmode main.tex && \
	  PATH="$(TEXBIN):$$PATH" pdflatex -interaction=nonstopmode main.tex
	@echo "-> paper/main.pdf (SaTML / security framing)"

pdf-arxiv:
	cd paper && PATH="$(TEXBIN):$$PATH" pdflatex -interaction=nonstopmode -jobname=main_arxiv "\def\arxivbuild{}\input{main.tex}" && \
	  PATH="$(TEXBIN):$$PATH" pdflatex -interaction=nonstopmode -jobname=main_arxiv "\def\arxivbuild{}\input{main.tex}"
	@echo "-> paper/main_arxiv.pdf (de-anonymized preprint build)"

arxiv: pdf-arxiv
	rm -rf paper/arxiv_submission && mkdir -p paper/arxiv_submission/figures
	cp paper/figures/*.png paper/arxiv_submission/figures/
	cp paper/IEEEtran.cls paper/algorithm.sty paper/algorithmic.sty paper/arxiv_submission/
	printf '%% arXiv build: de-anonymized toggle forced on (arXiv compiles main.tex directly).\n\\def\\arxivbuild{}\n' > paper/arxiv_submission/main.tex
	cat paper/main.tex >> paper/arxiv_submission/main.tex
	cd paper && COPYFILE_DISABLE=1 tar --exclude='.DS_Store' -czf arxiv_submission.tar.gz arxiv_submission
	@echo "-> paper/arxiv_submission.tar.gz (upload this to arXiv)"

pdf-gov:
	cd paper && PATH="$(TEXBIN):$$PATH" pdflatex -interaction=nonstopmode -jobname=main_gov "\def\govbuild{}\input{main.tex}" && \
	  PATH="$(TEXBIN):$$PATH" pdflatex -interaction=nonstopmode -jobname=main_gov "\def\govbuild{}\input{main.tex}"
	@echo "-> paper/main_gov.pdf (higher-altitude / AI-accountability framing)"

verify:
	$(PY) scripts/verify_repro.py

results:
	$(PY) scripts/collect_results.py

citations:
	$(PY) scripts/verify_citations.py paper/main.tex

lean-dry:
	$(PY) scripts/prune.py

lean:
	$(PY) scripts/prune.py --yes

restore:
	$(PY) scripts/restore.py
