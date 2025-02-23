# RESTful APIs Documentation

These APIs are designed to control **TCP** traffic.

---

## Policy Endpoints

Policy rules determine whether to **allow** or **deny** connections between two IP addresses and a specific destination port.

---

### **1. Add a Policy Rule**

Add a new policy rule to allow or deny traffic.

- **HTTP Method**: `POST`
- **URL Path**: `/policies`
- **Request Body**:
  - `src_ip` (string): Source IP address.
  - `dst_ip` (string): Destination IP address.
  - `dst_port` (string): Destination port.
  - `action` (string): Must be either `allow` or `deny`.

#### **Example**

- **Request**:

  ```bash
  curl -X POST -H "Content-Type: application/json" -d '{"src_ip": "172.16.1.1", "dst_ip": "172.16.1.2", "dst_port": "5201", "action": "allow"}' http://localhost:8080/policies
  ```

- **Response**:

  ```json
  {
    "action": "allow",
    "dst_ip": "172.16.1.2",
    "dst_port": "5201",
    "id": 0,
    "src_ip": "172.16.1.1"
  }
  ```

- **Status Codes**:

  - `201 Created`: Policy rule added successfully.
  - `400 Bad Request`: Invalid input data.
  - `409 Conflict`: Rule already exists.

---

### **2. Retrieve Policy Rules**

Fetch all existing policy rules.

- **HTTP Method**: `GET`
- **URL Path**: `/policies`

#### **Example**

- **Request**:

  ```bash
  curl -X GET http://localhost:8080/policies
  ```

- **Response**:

  ```json
  [
    {
      "action": "allow",
      "dst_ip": "172.16.1.2",
      "dst_port": "5201",
      "id": 0,
      "src_ip": "172.16.1.1"
    },
    {
      "action": "allow",
      "dst_ip": "172.16.1.2",
      "dst_port": "5202",
      "id": 1,
      "src_ip": "172.16.1.1"
    }
  ]
  ```

- **Status Codes**:

  - `200 OK`: Returns the list of policy rules.

---

### **3. Update a Policy Rule**

Modify an existing policy rule.

- **HTTP Method**: `PUT`
- **URL Path**: `/policies`
- **Request Body**:
  - `src_ip` (string): Source IP address.
  - `dst_ip` (string): Destination IP address.
  - `dst_port` (string): Destination port.
  - `action` (string): Must be either `allow` or `deny`.

#### **Example**

- **Request**:

  ```bash
  curl -X PUT -H "Content-Type: application/json" -d '{"src_ip": "172.16.1.1", "dst_ip": "172.16.1.2", "dst_port": "5201", "action": "allow"}' http://localhost:8080/policies
  ```

- **Response**:

  ```json
  {
    "action": "allow",
    "dst_ip": "172.16.1.2",
    "dst_port": "5201",
    "id": 0,
    "src_ip": "172.16.1.1"
  }
  ```

- **Status Codes**:

  - `201 Updated`: Policy rule updated successfully.
  - `400 Bad Request`: Invalid input data.

---

### **4. Delete a Policy Rule**

Remove a policy rule by its ID.

- **HTTP Method**: `DELETE`
- **URL Path**: `/policies/{id}`

#### **Example**

- **Request**:

  ```bash
  curl -X DELETE http://localhost:8080/policies/1
  ```

- **Response**:

  ```json
  {
    "message": "Policy deleted"
  }
  ```

- **Status Codes**:

  - `201 Deleted`: Policy rule deleted successfully.
  - `404 Not Found`: Rule does not exist.

---

## Bandwidth Control Endpoints

These endpoints manage bandwidth control rules using **P4 meter**. They regulate traffic bandwidth between two IP addresses and a specific destination port.

Bandwidth is controlled using four parameters:

- **CIR (Committed Information Rate)**: Guaranteed minimum bandwidth.
- **Cburst (Committed Burst Size)**: Maximum allowed burst above CIR.
- **PIR (Peak Information Rate)**: Maximum allowed bandwidth.
- **Pburst (Peak Burst Size)**: Maximum allowed burst above PIR.

**Note**: During testing with `iperf3`, the actual bandwidth was observed to be approximately half of the configured value.

---

### **1. Add a Bandwidth Control Rule**

Add a new bandwidth control rule.

- **HTTP Method**: `POST`
- **URL Path**: `/bandwidth`
- **Request Body**:
  - `src_ip` (string): Source IP address.
  - `dst_ip` (string): Destination IP address.
  - `rates` (list): A list containing two lists:
    - `[[CIR (bytes), Cburst (bytes)], [PIR (bytes), Pburst (bytes)]]`
  - `dst_port` (string): Destination port.

#### **Example**

- **Request**:

  ```bash
  curl -X POST -H "Content-Type: application/json" -d '{"src_ip": "172.16.1.1", "dst_ip": "172.16.1.2", "rates": [[100000, 10000], [100000, 10000]], "dst_port": "5201"}' http://localhost:8080/bandwidth
  ```

- **Response**:

  ```json
  {
    "dst_ip": "172.16.1.2",
    "dst_port": "5201",
    "path": ["s1", "s2"],
    "rates": [[100000, 10000], [100000, 10000]],
    "src_ip": "172.16.1.1"
  }
  ```

- **Status Codes**:

  - `201 Created`: Bandwidth control rule added successfully.
  - `400 Bad Request`: Invalid input data.
  - `409 Conflict`: Rule already exists.

---

### **2. Retrieve Bandwidth Control Rules**

Fetch all existing bandwidth control rules.

- **HTTP Method**: `GET`
- **URL Path**: `/bandwidth`

#### **Example**

- **Request**:

  ```bash
  curl -X GET http://localhost:8080/bandwidth
  ```

- **Response**:

  ```json
  [
    {
      "dst_ip": "172.16.1.2",
      "dst_port": "5201",
      "id": 0,
      "path": ["s1", "s2"],
      "rates": [[100000, 10000], [100000, 10000]],
      "src_ip": "172.16.1.1"
    },
    {
      "dst_ip": "172.16.1.2",
      "dst_port": "5202",
      "id": 1,
      "path": ["s1", "s2"],
      "rates": [[100000, 10000], [100000, 10000]],
      "src_ip": "172.16.1.1"
    }
  ]
  ```

- **Status Codes**:

  - `200 OK`: Returns the list of bandwidth control rules.

---

### **3. Update a Bandwidth Control Rule**

Modify an existing bandwidth control rule. If the rule does not exist, it will be created.

- **HTTP Method**: `PUT`
- **URL Path**: `/bandwidth`
- **Request Body**:
  - `src_ip` (string): Source IP address.
  - `dst_ip` (string): Destination IP address.
  - `rates` (list): A list containing two lists:
    - `[[CIR (bytes), Cburst (bytes)], [PIR (bytes), Pburst (bytes)]]`
  - `dst_port` (string): Destination port.

#### **Example**

- **Request**:

  ```bash
  curl -X PUT -H "Content-Type: application/json" -d '{"src_ip": "172.16.1.1", "dst_ip": "172.16.1.2", "rates": [[150000, 10000], [150000, 10000]], "dst_port": "5201"}' http://localhost:8080/bandwidth
  ```

- **Response**:

  ```json
  {
    "dst_ip": "172.16.1.2",
    "dst_port": "5201",
    "path": ["s1", "s2"],
    "rates": [[150000, 10000], [150000, 10000]],
    "src_ip": "172.16.1.1"
  }
  ```

- **Status Codes**:

  - `201 Updated`: Bandwidth control rule updated successfully.
  - `400 Bad Request`: Invalid input data.

---

### **4. Delete a Bandwidth Control Rule**

Remove a bandwidth control rule by its ID.

- **HTTP Method**: `DELETE`
- **URL Path**: `/bandwidth/{id}`

#### **Example**

- **Request**:

  ```bash
  curl -X DELETE http://localhost:8080/bandwidth/1
  ```

- **Response**:

  ```json
  {
    "message": "Bandwidth rule deleted"
  }
  ```

- **Status Codes**:

  - `201 Deleted`: Bandwidth control rule deleted successfully.
  - `404 Not Found`: Rule does not exist.


