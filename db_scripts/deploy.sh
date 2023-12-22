#!/usr/bin/env bash

echoerr() {
    echo "$@" 1>&2
}

get_scripts_path() {
    dirname "$0"
}

get_default_version() {
    basename $(ls -d1 $(get_scripts_path)/*/ | tail -n 1)
}

execute_script_in_folder() {
    folder_path=$1
    for file in $folder_path/* ; do
        if [ -d "$file" ]; then
            execute_script_in_folder $file
        elif [[ $file == *.sh ]]; then
            bash $file
        elif [[ $file == *.sql || $file == *.psql ]]; then
            if [[ $LOG_DB_QUERY == "true" ]]; then
                PGPASSWORD="$DB_USER_PASSWORD" \
                    psql \
                    -h $DB_HOST \
                    -p $DB_PORT \
                    -d $DB_NAME \
                    -U $DB_USER \
                    -a -c "$(envsubst < $file)"
            else
                PGPASSWORD="$DB_USER_PASSWORD" \
                    psql \
                    -h $DB_HOST \
                    -p $DB_PORT \
                    -d $DB_NAME \
                    -U $DB_USER \
                    -c "$(envsubst < $file)"
            fi
        fi
    done
}

if [ -z "$VERSION" ]; then
    export VERSION=$(get_default_version)
else
    export VERSION="${VERSION%/}"
fi
if [ -z "$DB_HOST" ]; then
    echoerr "DB_HOST not given!"
    exit 1
fi
if [ -z "$DB_PORT" ]; then
    export DB_PORT=5432
fi
if [ -z "$DB_NAME" ]; then
    export DB_NAME="gctbdb"
fi
if [ -z "$DB_USER" ]; then
    export DB_USER="gctbuser"
fi
if [ -z "$DB_USER_PASSWORD" ]; then
    echoerr "DB_USER_PASSWORD not given!"
    exit 1
fi
if [ -z "$DEPLOY_DDL" ]; then
    export DEPLOY_DDL="true"
fi
if [ -z "$DEPLOY_DML" ]; then
    export DEPLOY_DML="true"
fi
if [ -z "$LOG_DB_QUERY" ]; then
    export LOG_DB_QUERY="false"
fi

if ! [ -d "$(get_scripts_path)/$VERSION" ]; then
    echoerr "Given Version not found!"
    exit 1;
fi

if [[ "$DEPLOY_DDL" == "true" ]]; then
    execute_script_in_folder $(get_scripts_path)/$VERSION/ddl
fi
if [[ "$DEPLOY_DML" == "true" ]]; then
    execute_script_in_folder $(get_scripts_path)/$VERSION/dml
fi
