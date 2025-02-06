# Limited Google Drive

---

## **Part 1: What We Want to Do**
This project aims to build a terminal-based network and file management system using **P4**, **BMv2**, **WebDAV**, and **RESTful APIs**. The system will allow users to interact with a **NAS** while dynamically controlling their **network bandwidth** and **file access permissions**.

### **1. User Roles and Permissions**
We have four user roles with the following permissions:

| User Role        | Permissions                                                                                          |
|------------------|------------------------------------------------------------------------------------------------------|
| **Unregistered**  | Cannot access any files or network resources.                                                       |
| **Registered**    | Can upload, download, delete, and move their own files via WebDAV, but under a limited bandwidth.   |
| **VIP**           | Can upload, download, delete, and move their own files via WebDAV without bandwidth limitations.    |
| **Administrator** | Full access to all files (change ownership, set access policies) and control network bandwidth.     |

---

### **2. Features**
- **File Management via WebDAV:** Handle file uploads, downloads, deletions, and directory navigation.
- **User Authentication:** Secure login and token-based authentication using JWT.
- **Bandwidth Management:** Dynamically control user bandwidth through P4 logic.
- **Access Control:** Administrators can define per-user access to WebDAV resources.
- **Network Monitoring:** Track and log user network activity for analysis.

---

## **Part 2: How We Do That**

---

### **1. System Architecture**
- **WebDAV Server:** Acts as the central file management service (e.g., Apache WebDAV, Nextcloud).
- **RESTful API 1:** Network REST API for managing bandwidth and file access control.
- **P4 Runtime:** Manages network flows and enforces bandwidth policies using BMv2.
- **Terminal-Based CLI Script:** Provides users with command-line interaction for file and network operations.

```
+-----------------------------------------+
|            Terminal CLI (client.sh)     |
+-----------------------------------------+
                |
                v
+-----------------------------------------+
|             Network REST API            |
+-----------------------------------------+
                |
                v
+----------------------------+    +----------------------+
|   P4 Switch (BMv2 Model)   |    |      WebDAV Server   |
+----------------------------+    +----------------------+
```

---

### **2. Implementation Steps**

#### **Step 1: WebDAV Integration for File Management**
**Goal:** Allow users to interact with files through the WebDAV protocol using the terminal CLI script.

- **File Operations:** Instead of direct RESTful endpoints for files, use a WebDAV server for:
  - Uploading files
  - Downloading files
  - Deleting files
  - Moving/renaming files
  - Listing directory contents

- **CLI Interaction with WebDAV:**
  - Use `curl` or specialized tools like `cadaver` to interact with the WebDAV server.
  - Implement commands for file interactions in the `client.sh` script.

**CLI Script Example for WebDAV Operations:**
```bash
# Upload file using curl to WebDAV server
curl -T ./myfile.txt http://webdav-server.local/remote.php/dav/files/user1/

# Download file
curl -O http://webdav-server.local/remote.php/dav/files/user1/myfile.txt

# Delete file
curl -X DELETE http://webdav-server.local/remote.php/dav/files/user1/myfile.txt

# Move/Rename file
curl -X MOVE -H "Destination: http://webdav-server.local/remote.php/dav/files/user1/newname.txt" \
http://webdav-server.local/remote.php/dav/files/user1/myfile.txt
```

---

#### **Step 2: Authentication System**
**Goal:** Implement secure login using JWT tokens, and authenticate users against both WebDAV and the Network REST API.

- **Process:**
  - User logs in through the terminal script (`client.sh`).
  - Upon successful login, a JWT is issued and saved locally (`~/.client_auth_token`).
  - WebDAV requests include the token for authentication.

**File Operations with Authentication:**
```bash
curl -T ./myfile.txt \
    -H "Authorization: Bearer $(cat ~/.client_auth_token)" \
    http://webdav-server.local/remote.php/dav/files/user1/
```

---

#### **Step 3: Network REST API for Bandwidth and Access Control**
**Goal:** Dynamically control network access and bandwidth using P4 and RESTful APIs.

| Endpoint               | Method | Description                      |
|-----------------------|--------|----------------------------------|
| `/network/set_bandwidth` | POST   | Set bandwidth limits for users   |
| `/network/check_bandwidth` | GET | Check current bandwidth usage    |
| `/network/set_access_policy` | POST | Define WebDAV access restrictions |

**How It Works:**
- **Bandwidth Limits:** Use `P4Runtime` to configure flow tables on BMv2.
- **Access Policies:** Block unauthorized requests to WebDAV using IP-based access control.
  
Example Request to Set Bandwidth:
```json
POST /network/set_bandwidth
{
    "user_ip": "192.168.1.100",
    "bandwidth_limit": "10Mbps"
}
```

---

#### **Step 4: P4 Logic for Bandwidth Enforcement**
**Goal:** Use counters to monitor traffic and dynamically enforce bandwidth limits.

**P4 Example for BMv2:**
```p4
// Define counter for tracking traffic
counter user_traffic_counter {
    type: bytes;
}

// Bandwidth control table
table bandwidth_control {
    key = { hdr.ipv4.srcAddr : lpm; }
    actions = { set_limit; drop; }
}

action set_limit() {
    user_traffic_counter.count();
    // Check bandwidth limits via control plane
}
```

---

#### **Step 5: Terminal-Based CLI Script**
**Goal:** Provide a simple command-line interface for users to interact with the system.

**Updated Commands with WebDAV:**
```bash
# Login
./client.sh login --username <username> --password <password>

# Upload a file to WebDAV
./client.sh upload --file <path_to_file>

# Download a file from WebDAV
./client.sh download --file <remote_file_path>

# Delete a file
./client.sh delete --file <remote_file_path>

# List directory contents
./client.sh list_files

# Set bandwidth limit (admin only)
./client.sh admin set_bandwidth --user <username> --limit 10Mbps
```


