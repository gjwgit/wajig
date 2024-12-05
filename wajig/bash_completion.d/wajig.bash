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
			       @(addcdrom|add-cdrom|addgroup|add-group|addkey|add-key|addrepo|aptlog|autoalts|autoclean|auto-clean|\
autodownload|autoremove|build|\
builddeps|changelog|clean|commands|contents|dailyupgrade|dependents|describe|describenew|detail|details|\
distupgrade|download|editsources|extract|fixconfigure|fixinstall|fixmissing|force|hold|\
info|init|install|installsuggested|integrity|large|lastupdate|listall|listalternatives|listcache|\
listdaemons|listfiles|listhold|listinstalled|listlog|listnames|listpackages|listscripts|listsection|\
listsections|liststatus|localupgrade|madison|move|new|newdetail|news|nonfree|orphans|passwords|policy|\
purge|purgeorphans|purgeremoved|rbuilddeps|readme|reboot|recdownload|recommended|reconfigure|\
reinstall|reload|remove|removeorphans|repackage|reportbug|repos|restart|rmrepo|rpm2deb|\
rpminstall|safeupgrade|safe-upgrade|search|\
searchapt|show|sizes|snapshot|source|start|status|stop|sysinfo|tasksel|todo|toupgrade|\
tutorial|unhold|unofficial|update|updatealternatives|updatepciids|updateusbids|upgrade|upgradesecurity|\
verify|version|versions|whichpackage) ]];
         then special=${COMP_WORDS[i]}
        fi
    done

    if [[ -n "$special" ]]; then
       case $special in
           install|distupgrade|download|show|changelog|builddeps|dependents|describe|detail|details|policy|recdownload|source)
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

	# 20241204 gjw Add general commands here to have them complete
	# in bash. This is manually updated and so some commands are
	# missing. Also the - versions were not included and are
	# gradually being added, manually as requested in
	# https://github.com/gjwgit/wajig/issues/21. This could surely
	# be automated but for now manually update as I notice they
	# are missing or requested to do so through the issue. The
	# following will list the dashed aliases:
	#
	# grep alias wajig/__init__.py
	#
	# Bound to be a better way but need time to research/review.

        commands=(addcdrom add-cdrom addgroup add-group addkey add-key
		  addrepo aptlog autoalts autoclean auto-clean
		  autodownload auto-download autoremove build
		  builddeps changelog clean commands contents
		  dailyupgrade dependents describe describenew detail
		  details distupgrade dist-upgrade download
		  editsources edit-sources extract fixconfigure
		  fix-configure fixinstall fix-install fixmissing
		  fix-missing force hold info init install
		  installsuggested integrity large lastupdate
		  last-update listall list-all listalternatives
		  list-alternatives listcache list-cache listdaemons
		  list-daemons listfiles list-files listhold list-hold
		  listinstalled listlog listnames listpackages
		  listscripts listsection listsections liststatus
		  localupgrade madison move new newdetail news
		  newupgrades new-upgrades nonfree orphans passwords
		  policy purge purgeorphans purge-orphans purgeremoved
		  purge-removed rbuilddeps readme reboot recdownload
		  recommended reconfigure reinstall reload remove
		  removeorphans repackage reportbug repos restart
		  rmrepo rpm2deb rpminstall safeupgrade safe-upgrade
		  search searchapt show sizes snapshot source start
		  status stop sysinfo tasksel todo toupgrade
		  to-upgrade tutorial unhold unofficial update
		  updatealternatives updatepciids updateusbids
		  upgradable upgrade upgradesecurity verify version
		  versions whichpackage)

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
