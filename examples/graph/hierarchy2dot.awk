#!/usr/bin/env -S awk -F| -f
BEGIN {
	print "digraph g {"
	print "\tgraph [layout=circo mindist=.3];"
	print "\tnode [fontname=Arial fontsize=12 style=filled penwidth=0 fillcolor=yellow]"
	print "\tedge [fontname=Arial fontsize=12]"
}

#{ print "\t\"" $1 "\\n(" $2 ")\" -> \"" $4 "\\n(" $5 ")\" [taillabel=\"citing " $3 "\" headlabel = \"cited " $6 "\"]" }
{ print "\t\"" $1 "\" -> \"" $4 "\" " }
END { print "}" }
