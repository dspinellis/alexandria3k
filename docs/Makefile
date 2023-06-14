# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile manpage

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Build the man page source.  This is located in a separate directory
# so that Sphinx will convert it alone
manpage: $(_BUILDDIR)/a3k.1

$(_BUILDDIR)/a3k.1:
	$(SPHINXBUILD) -b man -c "$(SOURCEDIR)" "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
