#!/bin/bash
MONTH=$(date +%m)
YEAR=$(date +%Y)
TIMESTAMP=$(date '+%Y%m%d%H%M%S')
BACKUPDIR=${BASEDIR}/beta/${YEAR}/${MONTH}

# backup globals
PGPASSWORD=${POSTGRES_BETA_PASSWORD} pg_dumpall -h ${POSTGRES_BETA_HOST} -p ${POSTGRES_BETA_PORT} -U ${POSTGRES_BETA_USER} --globals-only -f ${BASEDIR}/beta/globals-beta.sql

# each database
for DB in ${DBLIST_BETA}; do
  echo "Database: $DB"
  DMPPATH=${BACKUPDIR}/${DB}
  DMPFILE=${DMPPATH}/${DUMPPREFIX}_${DB}_${TIMESTAMP}.dmp
  mkdir -p ${DMPPATH}
  PGPASSWORD=${POSTGRES_BETA_PASSWORD} pg_dump -h ${POSTGRES_BETA_HOST} -p ${POSTGRES_BETA_PORT} -U ${POSTGRES_BETA_USER} -Fc -d ${DB} > ${DMPFILE}
  echo "File: $DMPFILE"
done

# cleanup
if [ "${REMOVE_BEFORE:-}" ]; then
  TIME_MINUTES=$((REMOVE_BEFORE * 24 * 60))
  echo "Removing following backups older than ${REMOVE_BEFORE} days"
  find ${BASEDIR}/beta/* -type f -mmin +${TIME_MINUTES} -delete
fi
