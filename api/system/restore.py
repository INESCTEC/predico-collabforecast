# ruff: noqa

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


def check_if_table_empty(table_name):
    
    with connection.cursor() as cursor:
        query = (f"SELECT CASE WHEN EXISTS (SELECT 1 FROM {table_name}) "
                 f"THEN 1 ELSE 0 END AS table_empty;")
        cursor.execute(query)
        result = cursor.fetchall()

    return bool(result[0][0])


def list_tables():
    # Check which csv files exist in the backup directory:
    backup_dir = os.path.join(settings.BACKUPS_PATH, "csv")
    files_in_dir = os.listdir(backup_dir)
    db_tables = [file.split(".")[0] for file in files_in_dir]
    # Assure that we only restore data for empty tables in DB:
    # -- Check if table is empty:
    for table in db_tables:
        empty = check_if_table_empty(table_name=table)
        if empty:
            print(f"WARNING! DB table '{table}' is not empty. "
                  f"Removing from list of tables to restore from CSV.")
            db_tables.remove(table)

    return db_tables


def restore_tables_from_csv(table_name, files_dir=None):
    if table_name is None:
        db_tables = list_tables()
        for table in db_tables:
            restore_database_table(table_name=table, files_dir=files_dir)
    else:
        restore_database_table(table_name=table_name, files_dir=files_dir)


def restore_database_table(table_name, files_dir=None):
    if files_dir is None:
        backup_dir = os.path.join(settings.BACKUPS_PATH, "csv")
    else:
        backup_dir = os.path.join(settings.BACKUPS_PATH, "csv", files_dir)
        
    backup_filepath = os.path.join(backup_dir, f"{table_name}.csv")
    
    # Check if file exists. If not, raise error:
    if not os.path.exists(backup_filepath):
        raise FileNotFoundError(f"File '{backup_filepath}' not found.")

    command = fr"\COPY {table_name} FROM '{backup_filepath}' WITH CSV HEADER"

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
    
def restore_full_database(file_name):
    backup_dir = os.path.join(settings.BACKUPS_PATH, "dump")
    backup_filepath = os.path.join(backup_dir, file_name)
    
    # Check if file exists. If not, raise error:
    if not os.path.exists(backup_filepath):
        raise FileNotFoundError(f"File '{backup_filepath}' not found.")
    
    # Restore full database from dump file:
    if sys.platform == 'linux':
        run_psql = fr"""
        export PGPASSWORD={DB_PW}; 
        pg_restore -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -d {DB_NAME} -v {backup_filepath};
        """
    else:
        raise NotImplementedError(f"Function not implemented for {sys.platform}")
    
    print("subprocess call:", run_psql)
    subprocess.call(run_psql, shell=True)
    
    return 0
