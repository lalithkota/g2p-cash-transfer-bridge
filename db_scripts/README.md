## Database Initialization Scripts

### PostgreSQL

- Create a new role/user called "gctbuser" and create a new database called "gctbdb",
  with "gctbuser" as the owner.
  No need to run this step if Postgres was installed through openg2p's deployment script.
  ```sql
  CREATE ROLE gctbuser WITH LOGIN NOSUPERUSER	CREATEDB CREATEROLE INHERIT REPLICATION CONNECTION LIMIT -1 PASSWORD 'xxxxxx';
  CREATE DATABASE gctbdb WITH OWNER = gctbuser CONNECTION LIMIT = -1;
  ```
- Then run
  ```sh
  DB_HOST="openg2p.sandbox.net" \
  DB_USER_PASSWORD="xxxxxx" \
    ./deploy.sh
  ```
  - The following optional Env vars can also be passed:
    - `VERSION="1.0.0"` Do not set this if you want latest version.
    - `DB_PORT="5432"` Default is 5432.
    - `DB_NAME="mydb"` Default is gctbdb.
    - `DB_USER="myuser"` Default is gctbuser.
    - `DEPLOY_DDL="false"` Default is true. If false, will not run DDL scripts.
    - `DEPLOY_DML="false"` Default is true. If false, will not run DML scripts.
    - `LOG_DB_QUERY="true"` Default is false. Logs all Db queries.
