#!/usr/bin/env python
# -*- python -*-

"""Program to generate bash_completion function for wajig.

It runs 'wajig -v command' and analyzes the output to generate the script.
To use the output, place the generated file in /etc/bash_completion.d.
To test it, source it in your .bashrc.

initial author: Author Don Rozenberg
changes by Graham Williams and Tshepang Lekhonkhobe
"""

import os
import re
import pprint
import subprocess

pp = pprint.PrettyPrinter()

option_patt = r'^(-[a-z]*)\|(--[a-z]*)'
option_patt_r = re.compile(option_patt)

command_patt = r'^([a-z-]*)'
command_patt_r = re.compile(command_patt)

o_str = ['']
o_i = 0

c_str = ['']
c_i = 0

# Run wajig command
cmd = "python src/wajig.py -v commands"
with subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout as f:
    for l in f:
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

part1 = '''\
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
            COMPREPLY=($( compgen -W \'
            '''

part3 = ''' -- $cur ) )
        fi
}
complete -F _wajig $default wajig
'''


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
wajig = "%s'%s\n" % (wajig, part3)

with open("wajig.completion", "w") as f:
    f.write(wajig)
