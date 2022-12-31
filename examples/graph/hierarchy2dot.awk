#!/usr/bin/env -S awk -F| -f
BEGIN {
	print "digraph g {"
	print "\tgraph [layout=circo mindist=.3];"
	print "\tnode [fontname=Arial fontsize=12 style=filled penwidth=0 fillcolor=yellow]"
	print "\tedge [fontname=Arial fontsize=12 penwidth = 5]"
	print "\t\"Colloid and Surface Chemistry\" [label=\"Colloid and\\nSurface Chemistry\"]"
	print "\t\"General Biochemistry, Genetics and Molecular Biology\" [label=\"General Biochemistry,\nGenetics and Molecular Biology\"]"
	print "\t\"General Economics, Econometrics and Finance\" [label=\"General Economics,\nEconometrics and Finance\"]"
	print "\t\"Physical and Theoretical Chemistry\" [label=\"Physical and\nTheoretical Chemistry\"]"
}

#{ print "\t\"" $1 "\\n(" $2 ")\" -> \"" $4 "\\n(" $5 ")\" [taillabel=\"citing " $3 "\" headlabel = \"cited " $6 "\"]" }
{
	pw = $8 / 3.6e6 * 6
	value = ($7 - .75) * 5
	sat = 1 - value
	print "\t\"" $1 "\" -> \"" $4 "\" [penwidth=" pw " color=\" 0.36 " sat + .2 " " value + .2 "\" ]" }
END { print "}" }
