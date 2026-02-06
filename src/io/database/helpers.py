import psycopg2.extras as extras


def to_sql_no_update(conn, df, table):
    tuples = []
    for val in df.to_numpy():
        tuples.append(tuple(map(lambda x: None if str(x) == "nan" else x, val)))

    conflict_set = ",".join(list(df.columns))  # column names
    cursor = conn.cursor()
    try:
        query = "INSERT INTO %s(%s) VALUES %%s;" % (table, conflict_set)
        extras.execute_values(cursor, query, tuples)
        conn.commit()
        cursor.close()
        return True
    except Exception as ex:
        cursor.close()
        raise ex
