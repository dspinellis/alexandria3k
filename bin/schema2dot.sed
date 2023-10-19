#!/usr/bin/env -S sed -nf
#
# Create database schema when called (e.g. through bin/update-schema)
# on the output of the schema listing.
#

/CREATE TABLE/ {
  # Create table and line
  s|CREATE TABLE \([^\n]*\)(|\1 [label=<<TABLE BORDER="1" CELLSPACING="0" CELLBORDER="0">\n<TR><TD><B>\1</B></TD></TR><HR/>\n<TR ALIGN="LEFT"><TD  BALIGN="LEFT">|
  # Initialize hold space with this, so as to accumulate the complete table
  h
  # Remove first line from pattern space to continue processing
  s/.*\n//
}

# Field name
/^  / {
  s/ INTEGER PRIMARY KEY//
  # Put table fields in separate lines
  s|,$|<BR/>|
  # And append to hold space
  H
}

# Table has ended
/);/ {
  # Finish the table
  s|);|</TD></TR></TABLE>>];|
  # Append to hold space
  H
  # Move to patten space
  g
  # Remove embedded newlines
  s/\n *//g
  # Print
  p
}

# Terminate file with closing brace
$ {
  a}
  p
}
