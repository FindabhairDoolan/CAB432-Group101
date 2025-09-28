Assignment 2 - Cloud Services Exercises - Response to Criteria
================================================

Instructions
------------------------------------------------
- Keep this file named A2_response_to_criteria.md, do not change the name
- Upload this file along with your code in the root directory of your project
- Upload this file in the current Markdown format (.md extension)
- Do not delete or rearrange sections.  If you did not attempt a criterion, leave it blank
- Text inside [ ] like [eg. S3 ] are examples and should be removed


Overview
------------------------------------------------

- **Name:** Findabhair Doolan
- **Student number:** n11957557
- **Partner name (if applicable):** Alex O'Donnell
- **Application name:** VideoRestApi
- **Two line description:** We implemented an app that transcodes videos, and allows uploading and downloading of said videos.
- **EC2 instance name or ID:**i-0c72802fa261bbc81

------------------------------------------------

### Core - First data persistence service

- **AWS service name:**  S3
- **What data is being stored?:** Video Files
- **Why is this service suited to this data?:** The video files are best suited for this server due to the size limits.
- **Why is are the other services used not suitable for this data?:** Same reason as above, this allows data storage with size limits that allow what we need
- **Bucket/instance/table name:** n11957557-video-bucket
- **Video timestamp:**00:09
- **Relevant files:** controller.py, model.py
    -

### Core - Second data persistence service

- **AWS service name:**  DynamoDB
- **What data is being stored?:** The metadata for the video files in the first table, and a list of tasks to complete in the tasks files. 
- **Why is this service suited to this data?:** Small scale, and we can use the PK and SK to retrieve all the data we need really quickly.
- **Why is are the other services used not suitable for this data?:** they do not provide the functionality we need for the metadata, and while SQL would provide the functionality, it is overkill for this project. 
- **Bucket/instance/table name:** "n11957557-videos" and "n11957557-tasks"
- **Video timestamp:**00:49
- **Relevant files:** controller.py, model.py
    -

### Third data service

- **AWS service name:**  [eg. RDS]
- **What data is being stored?:** [eg video metadata]
- **Why is this service suited to this data?:** [eg. ]
- **Why is are the other services used not suitable for this data?:** [eg. Advanced video search requires complex querries which are not available on S3 and inefficient on DynamoDB]
- **Bucket/instance/table name:**
- **Video timestamp:**
- **Relevant files:**
    -

### S3 Pre-signed URLs

- **S3 Bucket names:** n11957557-video-bucket
- **Video timestamp:**02:28
- **Relevant files:** models.py
    -

### In-memory cache

- **ElastiCache instance name:**
- **What data is being cached?:** [eg. Thumbnails from YouTube videos obatined from external API]
- **Why is this data likely to be accessed frequently?:** [ eg. Thumbnails from popular YouTube videos are likely to be shown to multiple users ]
- **Video timestamp:**
- **Relevant files:**
    -

### Core - Statelessness

- **What data is stored within your application that is not stored in cloud data services?:** Video files that have been transcoded but not put in the S3 bucket yet.
- **Why is this data not considered persistent state?:** They can be retranscoded from the original file if necessary. 
- **How does your application ensure data consistency if the app suddenly stops?:** The tasks table acts as a journel to resume interuppted tasks upon restart of the program.
- **Relevant files:** recovery.py
    -

### Graceful handling of persistent connections

- **Type of persistent connection and use:** [eg. server-side-events for progress reporting]
- **Method for handling lost connections:** [eg. client responds to lost connection by reconnecting and indicating loss of connection to user until connection is re-established ]
- **Relevant files:**
    -


### Core - Authentication with Cognito

- **User pool name:**Group101-A2
- **How are authentication tokens handled by the client?:** Server response to logging in contains the IDToken used for authorising a user
- **Video timestamp:**04:33
- **Relevant files:**
    -auth.py
    -configure.py

### Cognito multi-factor authentication

- **What factors are used for authentication:** [eg. password, SMS code]
- **Video timestamp:**
- **Relevant files:**
    -

### Cognito federated identities

- **Identity providers used:**
- **Video timestamp:**
- **Relevant files:**
    -

### Cognito groups

- **How are groups used to set permissions?:** Admin group users can view tasks and videos uploaded/started by any user while normal users just view their own
- **Video timestamp:**05:12
- **Relevant files:**
    -auth.py
    -transcoder/models.py
    -transcoder/controllers.py

### Core - DNS with Route53

- **Subdomain**:group101.cab432.com
- **Video timestamp:**06:11

### Parameter store

- **Parameter names:** /Group101/CLIENT_ID, /Group101/DDB_TABLE_FILES, /Group101/DDB_TABLE_TASKS, /Group101/S3_BUCKET, /Group101/USER_POOL_ID
- **Video timestamp:**06:36
- **Relevant files:**
    -configure.py
    -auth.py
    -transcoder/models.py
    -transcoder/controllers.py

### Secrets manager

- **Secrets names:** group101-cognitosecret
- **Video timestamp:**07:15
- **Relevant files:**
    -configure.py
    -auth.py

### Infrastructure as code

- **Technology used:**
- **Services deployed:**
- **Video timestamp:**
- **Relevant files:**
    -

### Other (with prior approval only)

- **Description:**
- **Video timestamp:**
- **Relevant files:**
    -

### Other (with prior permission only)

- **Description:**
- **Video timestamp:**
- **Relevant files:**
    -
