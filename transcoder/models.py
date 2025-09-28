from aws import dynamo, TABLE_FILES, TABLE_TASKS, QUT_USERNAME

#videos
def create_video_metadata(file_id: str, filename: str, s3_key: str, size: int, uploaded_by: str, created_at: str):
    dynamo.put_item(
        TableName=TABLE_FILES,
        Item={
            "qut-username": {"S": QUT_USERNAME},   #fixed pk cause unit rule
            "fileId": {"S": file_id},              
            "uploaded_by": {"S": uploaded_by},     #app level user
            "filename": {"S": filename},
            "s3Key": {"S": s3_key},
            "size": {"N": str(size)},
            "createdAt": {"S": created_at}
        }
    )
    return {
        "id": file_id,
        "filename": filename,
        "s3Key": s3_key,
        "size": size,
        "uploaded_by": uploaded_by,
        "created_at": created_at
    }
#lists all videos under the QUT PK
def get_all_videos(limit=10, offset=0, sort_by="created_at", order="desc", uploaded_by=None):
    resp = dynamo.query(
        TableName=TABLE_FILES,
        KeyConditionExpression="#pk = :pk AND begins_with(#sk, :pref)",
        ExpressionAttributeNames={"#pk": "qut-username", "#sk": "fileId"},
        ExpressionAttributeValues={":pk": {"S": QUT_USERNAME}, ":pref": {"S": "FILE#"}},
        ScanIndexForward=(order.lower() == "asc"),
        Limit=limit + offset
    )
    items = resp.get("Items", [])
    # Optional app-user filtering
    if uploaded_by:
        items = [it for it in items if it.get("uploaded_by", {}).get("S") == uploaded_by]

    items = items[offset:offset+limit]
    out = []
    for it in items:
        out.append({
            "id": it["fileId"]["S"],
            "filename": it["filename"]["S"],
            "s3Key": it["s3Key"]["S"],
            "size": int(it["size"]["N"]),
            "uploaded_by": it["uploaded_by"]["S"],
            "created_at": it["createdAt"]["S"]
        })
    return out
#Gets video by id
def get_video_by_id(file_id: str, uploaded_by: str):
    resp = dynamo.query(
        TableName=TABLE_FILES,
        KeyConditionExpression="qut-username = :qut AND uploaded_by = :user",
        FilterExpression="fileId = :fid",
        ExpressionAttributeValues={
            ":qut": {"S": QUT_USERNAME},
            ":user": {"S": uploaded_by},
            ":fid": {"S": file_id}
        }
    )
    items = resp.get("Items", [])
    if not items:
        return None

    it = items[0]
    return {
        "id": it["fileId"]["S"],
        "filename": it["filename"]["S"],
        "s3Key": it["s3Key"]["S"],
        "size": int(it["size"]["N"]),
        "uploaded_by": it["uploaded_by"]["S"],
        "created_at": it["createdAt"]["S"]
    }

#task table(the joruenyl)
def create_task_record(uploaded_by: str, file_id: str, preset: str, created_at: str):
    from aws import new_task_id
    task_id = new_task_id()
    dynamo.put_item(
        TableName=TABLE_TASKS,
        Item={
            "qut-username": {"S": QUT_USERNAME},  
            "taskId": {"S": task_id},            
            "uploaded_by": {"S": uploaded_by},    
            "fileId": {"S": file_id},
            "preset": {"S": preset},
            "status": {"S": "queued"},
            "createdAt": {"S": created_at}
        }
    )
    return {"id": task_id}

#update task status
def update_task_status(uploaded_by: str, task_id: str, status: str, output_key=None, error=None, started_at=None, finished_at=None):
    expr_parts = ["#s = :s"]
    names = {"#s": "status"}
    vals = {":s": {"S": status}}

    if output_key is not None:
        expr_parts.append("outputKey = :o"); vals[":o"] = {"S": output_key}
    if error is not None:
        expr_parts.append("error = :e"); vals[":e"] = {"S": str(error)}
    if started_at is not None:
        expr_parts.append("startedAt = :sa"); vals[":sa"] = {"S": started_at}
    if finished_at is not None:
        expr_parts.append("finishedAt = :fa"); vals[":fa"] = {"S": finished_at}

    dynamo.update_item(
        TableName=TABLE_TASKS,
        Key={"qut-username": {"S": QUT_USERNAME}, "taskId": {"S": task_id}},
        UpdateExpression="SET " + ", ".join(expr_parts),
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=vals
    )

#get task by id
def get_task_by_id(uploaded_by: str, task_id: str):
    resp = dynamo.get_item(
        TableName=TABLE_TASKS,
        Key={"qut-username": {"S": QUT_USERNAME}, "taskId": {"S": task_id}}
    )
    it = resp.get("Item")
    if not it:
        return None
    if it.get("uploaded_by", {}).get("S") != uploaded_by:
        return None

    return {
        "id": it["taskId"]["S"],
        "file_id": it["fileId"]["S"],
        "preset": it["preset"]["S"],
        "status": it["status"]["S"],
        "created_at": it.get("createdAt", {}).get("S"),
        "started_at": it.get("startedAt", {}).get("S"),
        "finished_at": it.get("finishedAt", {}).get("S"),
        "error": it.get("error", {}).get("S"),
        "output_key": it.get("outputKey", {}).get("S")
    }

def get_tasks(uploaded_by: str, status=None, limit=10, offset=0, sort_by="id", order="desc"):
    resp = dynamo.query(
        TableName=TABLE_TASKS,
        KeyConditionExpression="#pk = :pk AND begins_with(#sk, :pref)",
        ExpressionAttributeNames={"#pk": "qut-username", "#sk": "taskId"},
        ExpressionAttributeValues={":pk": {"S": QUT_USERNAME}, ":pref": {"S": "TASK#"}},
        ScanIndexForward=(order.lower() == "asc"),
        Limit=limit + offset
    )
    items = resp.get("Items", [])

    #filter to the app user
    items = [it for it in items if it.get("uploaded_by", {}).get("S") == uploaded_by]
    #filter by status
    if status:
        items = [it for it in items if it.get("status", {}).get("S") == status]

    items = items[offset:offset+limit]
    out = []
    for it in items:
        out.append({
            "id": it["taskId"]["S"],
            "file_id": it["fileId"]["S"],
            "preset": it["preset"]["S"],
            "status": it["status"]["S"],
            "created_at": it.get("createdAt", {}).get("S"),
            "started_at": it.get("startedAt", {}).get("S"),
            "finished_at": it.get("finishedAt", {}).get("S"),
            "error": it.get("error", {}).get("S"),
            "output_key": it.get("outputKey", {}).get("S")
        })
    return out

#finds file - helper for startup check
def get_video_by_id_any(file_id: str):
    resp = dynamo.get_item(
        TableName=TABLE_FILES,
        Key={"qut-username": {"S": QUT_USERNAME}, "fileId": {"S": file_id}}
    )
    it = resp.get("Item")
    if not it:
        return None
    return {
        "id": it["fileId"]["S"],
        "filename": it["filename"]["S"],
        "s3Key": it["s3Key"]["S"],
        "size": int(it["size"]["N"]),
        "uploaded_by": it["uploaded_by"]["S"],
        "created_at": it["createdAt"]["S"]
    }

#get tasks by status - helper for startup check
def get_tasks_by_statuses(statuses: set[str], limit: int = 200):
    resp = dynamo.scan(
        TableName=TABLE_TASKS,
        FilterExpression="task_status IN (:s1, :s2)",
        ExpressionAttributeValues={
        ":s1": {"S": "queued"},
        ":s2": {"S": "running"}
        }
    )
    items = resp.get("Items", [])
    out = []
    for it in items:
        st = it.get("status", {}).get("S")
        if st in statuses:
            out.append({
                "id": it["taskId"]["S"],
                "file_id": it["fileId"]["S"],
                "preset": it["preset"]["S"],
                "status": st,
                "uploaded_by": it["uploaded_by"]["S"],
                "created_at": it.get("createdAt", {}).get("S"),
                "started_at": it.get("startedAt", {}).get("S"),
                "finished_at": it.get("finishedAt", {}).get("S"),
                "error": it.get("error", {}).get("S"),
                "output_key": it.get("outputKey", {}).get("S")
            })
    return out


