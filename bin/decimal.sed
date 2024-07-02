#!/bin/sed -Ef
#
# Add decimal separator to long digit sequences
#
# Diomidis Spinellis, October 2018
#

:a
# Add a , after a digit followed by three digits followed by non-digit or EOL
s/([0-9])([0-9]{3})([^0-9]|$)/\1,\2\3/

# Try the replacement again if the replacement succeeded
ta
