#!/bin/bash
# Rudimentary deployment script..
# 
# The following must be done on the server ahead of deployment:
# 1) The following packages must be installed:
#    apt-get install libjpeg-dev python-dev
# 2) You must have created a user for storing files and running gunicorn, 
#    and the directory ${HOSTDIR} must be writable by that user.
# 3) init system must be configured to start gunicorn worker on startup/incoming
#    connection, and to restart worker on crash.
#    The init system should set the environment variable PM_CONFIG pointing
#    to the production configuration file.
# 4) Web server should be configured to forward requests to gunicorn.

LOGIN=${1}
HOSTDIR=${2}

do_reinstall_py=n
do_reinstall_js=n
do_file_scan=n
do_reinitialize_db=n

[[ -t 0 ]] && read -p $'\e[1;32m Do you want to purge and reinstall python packages? (y/N)\e[0m ' do_reinstall_py
[[ -t 0 ]] && read -p $'\e[1;32m Do you want to purge and reinstall bower dependencies? (y/N)\e[0m ' do_reinstall_js
[[ -t 0 ]] && read -p $'\e[1;32m Do you want to drop all db tables and reinitialize? (y/N)\e[0m ' do_reinitialize_db 
[[ -t 0 ]] && read -p $'\e[1;32m Do you want to perform a library scan? (y/N)\e[0m ' do_file_scan

add_files=""
if [[ $do_reinstall_py =~ ^(y|Y)$ ]]; then 
	if [ -z ${VIRTUAL_ENV+x} ]; then
		echo "Virtualenv is not set.."
		exit 0
	fi
	pip freeze > deployment_requirements.pip
	add_files=" deployment_requirements.pip"
fi

# TODO: switch to git-archive
ssh $LOGIN "find ${HOSTDIR}/pm | grep py$ | xargs rm"
ssh $LOGIN "find ${HOSTDIR}/pm | grep pyc$ | xargs rm"
tar -cj -f - pm manage.py ${add_files} | ssh $LOGIN tar -xj -f - -C $HOSTDIR

if [[ $do_reinstall_py =~ ^(y|Y)$ ]]; then 
	echo "Reinitializing python environment"
	ssh ${LOGIN} rm -rf ${HOSTDIR}/env
	ssh ${LOGIN} mkdir ${HOSTDIR}/env
	ssh ${LOGIN} virtualenv -p /usr/bin/python3 ${HOSTDIR}/env
	ssh ${LOGIN} ${HOSTDIR}/env/bin/pip install -r ${HOSTDIR}/deployment_requirements.pip
	rm deployment_requirements.pip
fi

if [[ $do_reinitialize_db =~ ^(y|Y)$ ]]; then 
	echo "Reinitializing database"
	# for now we assume the production config file is ${HOSTDIR}/config.cfg
	ssh ${LOGIN} PM_CONFIG=${HOSTDIR}/config.cfg ${HOSTDIR}/env/bin/python ${HOSTDIR}/manage.py resetdb
fi

if [[ $do_file_scan =~ ^(y|Y)$ ]]; then 
	echo "Performing file scan"
	# for now we assume the production config file is ${HOSTDIR}/config.cfg
	# TODO: doesn't really seem to work, perhaps the connection gets cut for some reason..
	#       really should just schedule some process, started by systemd or something
	ssh ${LOGIN} PM_CONFIG=${HOSTDIR}/config.cfg ${HOSTDIR}/env/bin/python ${HOSTDIR}/manage.py scan
fi

#if [[ $do_file_scan =~ ^(y|Y)$ ]]; then 
#  ssh ${LOGIN} bower ${HOSTDIR}/env/bin/python ${HOSTDIR}/scan.py
#fi


## kill worker processes
ssh ${LOGIN} killall gunicorn
