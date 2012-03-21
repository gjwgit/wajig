#!/bin/sh
# adapted from optcomplete (http://hg.furius.ca/public/optcomplete/)

_wajig()
{
    COMPREPLY=( $( \
	COMP_LINE=$COMP_LINE  COMP_POINT=$COMP_POINT \
	COMP_WORDS="${COMP_WORDS[*]}"  COMP_CWORD=$COMP_CWORD \
	ARGPARSE_AUTO_COMPLETE=1 $1 ) )
}

complete -F _wajig wajig
