cmdline:
	chmod +x ${PWD}/src/pounce.py
	mkdir -p ${HOME}/bin
	if test -f ${HOME}/bin/pounce; then rm ${HOME}/bin/pounce; fi
	ln -s ${PWD}/src/pounce.py ${HOME}/bin/pounce	
	export PATH="${PATH}:${HOME}/bin"
	echo 'export PATH="$$PATH:$$HOME/bin"' >> ${HOME}/.profile
