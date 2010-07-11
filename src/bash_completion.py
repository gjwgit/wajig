#!/usr/bin/env python
# -*- python -*-
# Time-stamp: <2005-11-09 05:59:02 Graham>

# Program to generate bash_completion function for wajig.
# It runs 'wajig command' and analyzes the output to build 'wajig' in the
# current directory.
# To use the output, place the generated file, 'wajig', in
# /etc/bash_completion.d. To test it source it in your .bashrc.

# Author Don Rozenberg
#
# Modifications Graham Williams
#	Write to standard out.

import os
import re
import pprint
pp = pprint.PrettyPrinter()

# Run wajig command
f = os.popen('python src/wajig.py commands', 'r')

lines = f.readlines()

option_patt = r'^(-[a-z]*)\|(--[a-z]*)'
option_patt_r = re.compile(option_patt)

command_patt = r'^([a-z-]*)'
command_patt_r = re.compile(command_patt)

o_str = []
o_str.append('')
o_i = 0

c_str = []
c_str.append('')
c_i = 0

for l in lines:
    l = l.strip()
    if l == '':
        continue
    if l.find(':') > -1:
        continue
    if l.find('Run') == 0:
        continue
    if l.find('-') == 0:
        mo = option_patt_r.search(l)
        if mo == None:
            continue
        o1 = mo.group(1)
        o2 = mo.group(2)
        if len(o_str[o_i]) > 30:
            o_str[o_i] = "%s %s" % (o_str[o_i], ' \\ \n')
            o_str.append('')
            o_i += 1
        o_str[o_i] = "%s %s" % (o_str[o_i], o1)
        if len(o_str[o_i]) > 30:
            o_str[o_i] = "%s %s" % (o_str[o_i], ' \\ \n')
            o_str.append('')
            o_i += 1
        o_str[o_i] = "%s %s" % (o_str[o_i], o2)
    else:
        mo = command_patt_r.search(l)
        if mo == None:
            continue
        cmd = mo.group(1)
        if len(c_str[c_i]) > 40:
            c_str[c_i] = "%s %s" % (c_str[c_i], '\\ \n')
            c_str.append('')
            c_i += 1
        c_str[c_i] = "%s %s" % (c_str[c_i], cmd)

# For debugging, print the commands and options.
#print
#pp.pprint(c_str)

#print
#pp.pprint(o_str)

part1 = '''
have wajig &&
_wajig()
{
        local cur prev opt

        COMPREPLY=()
        cur=${COMP_WORDS[COMP_CWORD]}
        prev=${COMP_WORDS[COMP_CWORD-1]}

        if [ "$COMP_CWORD" -ge "2" ]; then
           COMPREPLY=($( compgen -W "$(apt-cache pkgnames "$cur")" -- $cur ) )
        elif [[ "$cur" == -* ]]; then
            COMPREPLY=($( compgen -W \''''

part2 = ''' -- $cur ) )
        else
            COMPREPLY=($( compgen -W \''''

part3 = ''' -- $cur ) )
        fi

}
[ -n "${have:-}" ] && complete -F _wajig $default wajig'''


wajig = part1

#add the options.
wajig = "%s%s" % (wajig, o_str[0].lstrip())
for i in range(1, len(o_str)):
    wajig = "%s                                 %s" % (wajig, o_str[i])

#add part2
wajig = "%s'%s" % (wajig, part2)

#add the commands.
wajig = "%s%s" % (wajig, c_str[0].lstrip())
for i in range(1, len(c_str)):
    wajig = "%s           %s" % (wajig, c_str[i])

#add the remainder.
wajig = "%s'%s" % (wajig, part3)

#w = open('wajig', 'w')
#print >> w, wajig

print wajig
