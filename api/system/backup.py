import os
import sys
import subprocess

from django.conf import settings
from django.db import connection

# DB settings:
DB_NAME = settings.DATABASES["default"]["NAME"]
DB_USER = settings.DATABASES["default"]["USER"]
DB_PW = settings.DATABASES["default"]["PASSWORD"]
DB_HOST = settings.DATABASES["default"]["HOST"]
DB_PORT = settings.DATABASES["default"]["PORT"]


def list_tables():
    query = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public';
    """
    # Connect to DB:
    with connection.cursor() as cursor:
        cursor.execute(query)
        db_tables = cursor.fetchall()
    db_tables = [table[0] for table in db_tables]
    return db_tables


def backup_tables_to_csv(table_name):
    if table_name is None:
        db_tables = list_tables()
        for table in db_tables:
            backup_database_table(table_name=table)
    else:
        backup_database_table(table_name=table_name)


def backup_database_table(table_name):
    backup_dir = os.path.join(settings.BACKUPS_PATH, "csv")
    backup_filepath = os.path.join(backup_dir, f"{table_name}.csv")
    os.makedirs(backup_dir, exist_ok=True)

    command = f"\COPY (SELECT * FROM {table_name}) TO '{backup_filepath}' WITH CSV HEADER"

    if sys.platform == 'linux':
        run_psql = fr"""
        export PGPASSWORD={DB_PW}; 
        psql -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -d {DB_NAME} -c "{command}";
        """
    else:
        raise NotImplementedError(f"Function not implemented for {sys.platform}")

    print("subprocess call:", run_psql)
    subprocess.call(run_psql, shell=True)

    return 0


def backup_full_database(file_name):
    backup_dir = os.path.join(settings.BACKUPS_PATH, "dump")
    os.makedirs(backup_dir, exist_ok=True)
    backup_filepath = os.path.join(backup_dir, file_name)
    
    if sys.platform == 'linux':
        run_psql = fr"""
        export PGPASSWORD={DB_PW}; 
        pg_dump -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -Fc -x {DB_NAME} > {backup_filepath}
        """
    else:
        raise NotImplementedError(f"Function not implemented for {sys.platform}")

    print("subprocess call:", run_psql)
    subprocess.call(run_psql, shell=True)

    return 0


def backup_and_archive_logs():
    raise NotImplementedError("Not implemented yet")

