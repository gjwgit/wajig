_have grep-status && {
_comp_dpkg_installed_packages()
{
    grep-status -P -e "^$1" -a -FStatus 'install ok installed' -n -s Package
}
} || {
_comp_dpkg_installed_packages()
{
    command grep -A 1 "Package: $1" /var/lib/dpkg/status | \
        command grep -B 1 -Ee "ok installed|half-installed|unpacked| \
            half-configured" \
            -Ee "^Essential: yes" | \
        command grep "Package: $1" | cut -d\  -f2
}
}

_have grep-status && {
_comp_dpkg_hold_packages()
{
    grep-status -P -e "^$1" -a -FStatus 'hold' -n -s Package
}
} || {
_comp_dpkg_hold_packages()
{
    command grep -B 2 'hold' /var/lib/dpkg/status | \
        command grep "Package: $1" | cut -d\  -f2
}
}

_have wajig &&
_wajig()
{
    local cur dashoptions prev special i

    COMPREPLY=()
    _get_comp_words_by_ref cur prev

    dashoptions='-h --help -V --version'

    for (( i=0; i < ${#COMP_WORDS[@]}-1; i++ )); do
        if [[ ${COMP_WORDS[i]} == \
         @(addcdrom|addrepo|aptlog|autoalts|autoclean|autodownload|autoremove|build|\
builddeps|changelog|clean|commands|contents|dailyupgrade|dependents|describe|describenew|\
distupgrade|download|editsources|extract|fixconfigure|fixinstall|fixmissing|force|hold|\
info|init|install|installsuggested|integrity|large|lastupdate|listall|listalternatives|listcache|\
listdaemons|listfiles|listhold|listinstalled|listlog|listnames|listpackages|listscripts|listsection|\
listsections|liststatus|localupgrade|madison|move|new|newdetail|news|nonfree|orphans|passwords|policy|\
purge|purgeorphans|purgeremoved|rbuilddeps|readme|reboot|recdownload|recommended|reconfigure|\
reinstall|reload|remove|removeorphans|repackage|reportbug|repos|restart|rmrepo|rpm2deb|rpminstall|search|\
searchapt|show|sizes|snapshot|source|start|status|stop|sysinfo|tasksel|todo|toupgrade|\
tutorial|unhold|unofficial|update|updatealternatives|updatepciids|updateusbids|upgrade|upgradesecurity|\
verify|version|versions|whichpackage) ]];
         then special=${COMP_WORDS[i]}
        fi
    done

    if [[ -n "$special" ]]; then
       case $special in
           install|distupgrade|download|show|changelog|builddeps|dependents|describe|details|policy|recdownload|source)
               COMPREPLY=( $( apt-cache pkgnames $cur 2> /dev/null ) )
               if [[ "$special" == "install" ]]; then
                   _filedir
               fi
               return 0
               ;;
           purge|remove|reinstall|listinstalled|hold|news|readme|recommended|reconfigure|repackage|todo|verify)
               COMPREPLY=( $( _comp_dpkg_installed_packages "$cur" ) )
               return 0
               ;;
           reload|*start|status|stop)
               _services "$cur"
               return 0
               ;;
           unhold)
               COMPREPLY=( $( _comp_dpkg_hold_packages "$cur" ) )
               return 0
               ;;
           contents|extract|info|rpm2deb|rpminstall)
               _filedir
               ;;
       esac
    fi

    case $prev in
        # don't complete anything if these options are found
        autoclean|clean|search|upgrade|update)
            return 0
            ;;
        -S)
            _filedir
            return 0
            ;;
    esac

    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $( compgen -W "$dashoptions" -- "$cur" ) )
    elif [[ -z "$special" ]]; then
        commands=(addcdrom addrepo aptlog autoalts autoclean autodownload autoremove build builddeps
                  changelog clean commands contents dailyupgrade dependents describe
                  describenew distupgrade download editsources extract fixconfigure fixinstall
                  fixmissing force hold info init install installsuggested integrity large lastupdate
                  listall listalternatives listcache listdaemons listfiles listhold listinstalled
                  listlog listnames listpackages listscripts listsection listsections liststatus
                  localupgrade madison move new newdetail news nonfree orphans passwords policy purge purgeorphans
                  purgeremoved rbuilddeps readme reboot recdownload recommended reconfigure reinstall
                  reload remove removeorphans repackage reportbug repos restart rmrepo rpm2deb rpminstall search
                  searchapt show sizes snapshot source start status stop sysinfo tasksel
                  todo toupgrade tutorial unhold unofficial update updatealternatives updatepciids
                  updateusbids upgrade upgradesecurity verify version versions whichpackage)

        local option oldNoCaseMatch=$(shopt -p nocasematch)
        shopt -s nocasematch
        COMPREPLY=( $( for command in "${commands[@]}"; do
                [[ ${command:0:${#cur}} == "$cur" ]] && printf '%s\n' $command
                done ) )
        eval "$oldNoCaseMatch" 2> /dev/null
    fi

    return 0
}
complete -F _wajig wajig

# Local variables:
# mode: shell-script
# End:
