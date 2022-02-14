#!/bin/bash
MONTH=$(date +%m)
YEAR=$(date +%Y)
TIMESTAMP=$(date '+%Y%m%d%H%M%S')
BACKUPDIR=${BASEDIR}/${YEAR}/${MONTH}

# backup globals
PGPASSWORD=${POSTGRES_PASSWORD} pg_dumpall -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U ${POSTGRES_USER} --globals-only -f ${BASEDIR}/globals.sql

# each database
for DB in ${DBLIST}; do
  echo "Database: $DB"
  DMPPATH=${BACKUPDIR}/${DB}
  DMPFILE=${DMPPATH}/${DUMPPREFIX}_${DB}_${TIMESTAMP}.dmp
  mkdir -p ${DMPPATH}
  PGPASSWORD=${POSTGRES_PASSWORD} pg_dump -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U ${POSTGRES_USER} -Fc -d ${DB} > ${DMPFILE}
  echo "File: $DMPFILE"
done

# cleanup
if [ "${REMOVE_BEFORE:-}" ]; then
  TIME_MINUTES=$((REMOVE_BEFORE * 24 * 60))
  echo "Removing following backups older than ${REMOVE_BEFORE} days"
  find ${BASEDIR}/* -type f -mmin +${TIME_MINUTES} -delete
fi
