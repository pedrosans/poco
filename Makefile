mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(patsubst %/,%,$(dir $(mkfile_path)))
VERSION=0.4.7
WORKSPACE=$(current_dir)
SETUP_SCRIPT=${WORKSPACE}/setup.py

.SILENT:
manual:
	sed "s/VERSION/${VERSION}/" pocoy.1 > pocoy.1~
	groff -mman pocoy.1~ -T utf8 | col -bx > pocoy.1.txt
	gzip -c pocoy.1~ > pocoy.1.gz
	rm pocoy.1~
install: manual
	python3 -W 'ignore' ${SETUP_SCRIPT} install --record ${WORKSPACE}/installed_files.txt 1>/dev/null
uninstall:
	cat ${WORKSPACE}/installed_files.txt | xargs rm -rf ; rm -f ${WORKSPACE}/installed_files.txt
sources: manual
	python3 ${SETUP_SCRIPT} --command-packages=stdeb.command sdist_dsc --forced-upstream-version ${VERSION} 1>/dev/null
publish:
	debsign -pgpg2 ${WORKSPACE}/deb_dist/pocoy_${VERSION}-1_source.changes && echo "Signed"
	cd ${WORKSPACE}/deb_dist && dput ppa:pedrosans/rios pocoy_${VERSION}-1_source.changes && echo "Published"
clean:
	[ ! -f $(WORKSPACE)/installed_files.txt ] || rm -f  $(WORKSPACE)/installed_files.txt
	[ ! -f ${WORKSPACE}/pocoy.1.gz ]          || rm -f  ${WORKSPACE}/pocoy.1.gz
	[ ! -f ${WORKSPACE}/tags ]                || rm     ${WORKSPACE}/tags
	[ ! -f ${WORKSPACE}/pocoy-*.tar.gz ]      || rm     ${WORKSPACE}/pocoy-*.tar.gz
	[ ! -f ${WORKSPACE}/MANIFEST ]            || rm     ${WORKSPACE}/MANIFEST
	[ ! -d ${WORKSPACE}/build ]               || rm -rf ${WORKSPACE}/build
	[ ! -d ${WORKSPACE}/deb_dist ]            || rm -r  ${WORKSPACE}/deb_dist
	[ ! -d ${WORKSPACE}/dist ]                || rm -r  ${WORKSPACE}/dist
