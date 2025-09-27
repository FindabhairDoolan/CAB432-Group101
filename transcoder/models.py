from db.db import get_connection

#videos
def create_video_metadata(filename, storage_path, size, uploaded_by):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO files (filename, storage_path, size, uploaded_by) VALUES (%s, %s, %s, %s)",
        (filename, storage_path, size, uploaded_by)
    )
    conn.commit()
    file_id = cur.lastrowid
    conn.close()
    return {
        "id": file_id,
        "filename": filename,
        "storage_path": storage_path,
        "size": size,
        "uploaded_by": uploaded_by
    }

def get_all_videos(limit=10, offset=0, sort_by="created_at", order="desc", uploaded_by=None):
    allowed_sorts = {"id", "filename", "size", "created_at"}
    if sort_by not in allowed_sorts:
        sort_by = "created_at"
    if order.lower() not in {"asc", "desc"}:
        order = "desc"

    conn = get_connection()
    cur = conn.cursor()

    if uploaded_by:
        cur.execute(
            f"SELECT * FROM files WHERE uploaded_by=%s ORDER BY {sort_by} {order.upper()} LIMIT %s OFFSET %s",
            (uploaded_by, limit, offset)
        )
    else:
        cur.execute(
            f"SELECT * FROM files ORDER BY {sort_by} {order.upper()} LIMIT %s OFFSET %s",
            (limit, offset)
        )

    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    conn.close()
    return [dict(zip(cols, r)) for r in rows]

def get_video_by_id(file_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM files WHERE id = %s", (file_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    cols = [d[0] for d in cur.description]
    conn.close()
    return dict(zip(cols, row))

#tasks
def create_task_record(file_id, preset):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (file_id, preset, status) VALUES (%s, %s, %s)",
        (file_id, preset, "queued")
    )
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return {"id": task_id}

def update_task_status(task_id, status, output_path=None, error=None, started_at=None, finished_at=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE tasks
        SET status=%s, output_path=%s, error=%s, started_at=%s, finished_at=%s
        WHERE id=%s
    """, (status, output_path, error, started_at, finished_at, task_id))
    conn.commit()
    conn.close()

def get_task_by_id(task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    cols = [d[0] for d in cur.description]
    conn.close()
    return dict(zip(cols, row))

def get_tasks(status=None, limit=10, offset=0, sort_by="id", order="desc", username=None):
    allowed_sorts = {"id", "file_id", "preset", "status", "started_at", "finished_at"}
    if sort_by not in allowed_sorts:
        sort_by = "id"
    if order.lower() not in {"asc", "desc"}:
        order = "desc"

    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT t.* FROM tasks t"
    params = []

    if username:
        query += " JOIN files f ON t.file_id = f.id WHERE f.uploaded_by=%s"
        params.append(username)
        if status:
            query += " AND t.status=%s"
            params.append(status)
    elif status:
        query += " WHERE t.status=%s"
        params.append(status)

    query += f" ORDER BY {sort_by} {order.upper()} LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    conn.close()
    return [dict(zip(cols, r)) for r in rows]
