#!/bin/bash
set -e
psql -v ON_ERROR_STOP=1 --username postgres <<-EOF
    CREATE DATABASE $TGPK_DB;
    DO
    \$do\$
    BEGIN
       IF NOT EXISTS (
          SELECT
          FROM   pg_catalog.pg_roles
          WHERE  rolname = 'my_user') THEN
            CREATE ROLE $TGPK_USER WITH LOGIN PASSWORD '$TGPK_PASS';
       END IF;
    END
    \$do\$;
    ALTER ROLE $TGPK_USER WITH ENCRYPTED PASSWORD '$TGPK_PASS';
    GRANT ALL PRIVILEGES ON DATABASE $TGPK_DB TO $TGPK_USER;
    \c $TGPK_DB;
    CREATE EXTENSION if not exists pg_trgm;
EOF