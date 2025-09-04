#!/usr/bin/env bash
set -e
STAMP=$(date +%F_%H-%M)
docker exec -it proplus_mongo bash -lc "mongodump --db proplus --out /data/db/backup_${STAMP}"
docker cp proplus_mongo:/data/db/backup_${STAMP} ./backups/
echo "✅ Backup saved to ./backups/backup_${STAMP}"
