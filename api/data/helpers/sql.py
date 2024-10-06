# ruff: noqa: UP031
import psycopg2.extras as extras


def to_sql_update(conn, df, table, constraint_columns):
    tuples = []
    for val in df.to_numpy():
        tuples.append(tuple(map(lambda x: None if str(x) == "nan" else x, val)))  # noqa

    conflict_set = ','.join(list(df.columns))  # column names
    excluded_set = ','.join('EXCLUDED.' + str(e) for e in df.columns)
    try:
        query = "INSERT INTO %s(%s) VALUES %%s;" % (table, conflict_set)
        cursor = conn.cursor()
        extras.execute_values(cursor, query, tuples)
        conn.commit()
        cursor.close()
        return ''
    except Exception:
        constraint_columns = ','.join(constraint_columns)
        query = "INSERT INTO %s(%s) VALUES %%s " \
                "ON CONFLICT (%s) " \
                "DO UPDATE SET (%s)=(%s);" % (table, conflict_set,
                                              constraint_columns,
                                              conflict_set, excluded_set)
        cursor = conn.cursor()
        extras.execute_values(cursor, query, tuples)
        conn.commit()
        cursor.close()
        return "One or more database records were updated."
