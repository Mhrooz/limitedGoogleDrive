# RESTful APIs

[toc]

## Policy - Endpoints

Policy rule means the "allow" or "deny" the connection between two IPs as well as the destination's port.

### 1. Add a policy rule

- HTTP Method: `POST`

- URL Path: `/policies`

- Request Body:

  - `src_ip`: Source IP.
  - `dst_ip`: Destination IP.
  - `dst_port`: Destination's Port.
  - `action`: key must be `allow` or `deny`.

- example

  - Request: 
    `curl -X POST -H  "Content-Type: application/json" -d '{"src_ip": "172.16.1.1", "dst_ip":"172.16.1.2", "dst_port": "5201", "action": "allow"}' http://localhost:8080/policies`

  - Response:

    ```json
    {                                                                       
      "action": "allow",                                                     
      "dst_ip": "172.16.1.2", 
      "dst_port": "5201",
      "id": 0,
      "src_ip": "172.16.1.1"
    }  
    ```

- Status Codes

  - `201 Created`: The policy rule was added successfully.
  - `400 Bad Request`: Invalid input data.
  - `409 Rule exists`: Rule already exists.

### 2. Find a policy rule

- HTTP Method: `GET`

- URL Path: `/policies`

- Example

  - Request: 
    `curl -X GET http://localhost:8080/policies`

  - Response:

    ```json
    [ 
      {
        "action": "allow", 
        "dst_ip": "172.16.1.2",
        "dst_port": "5201",
        "id": 0,
        "src_ip": "172.16.1.1"
      }，
      {
        "action": "allow", 
        "dst_ip": "172.16.1.2",
        "dst_port": "5202",
        "id": 0,
        "src_ip": "172.16.1.1"
      } ，
    ]   
    ```

- Status Codes

  - `200`: Return the entries.

### 3. Update a policy rule

- HTTP Method: `PUT`

- URL Path: `/policies`

- Request Body:

  - `src_ip`: Source IP.
  - `dst_ip`: Destination IP.
  - `dst_port`: Destination's Port.
  - `action`: key must be `allow` or `deny`.

- Example

  - Request: 
    `curl -X PUT -H  "Content-Type: application/json" -d '{"src_ip": "172.16.1.1", "dst_ip":"172.16.1.2", "dst_port": "5201", "action": "allow"}' http://localhost:8080/policies`

  - Response:

    ```json
    {                                                                       
      "action": "allow",                                                     
      "dst_ip": "172.16.1.2", 
      "dst_port": "5201",
      "id": 0,
      "src_ip": "172.16.1.1"
    }  
    ```

- Status Codes

  - `201 Updated`: The policy rule updated successfully.
  - `400 Bad Request`: Invalid input data.

### 4. Delete a policy rule

- HTTP Method: `DELETE`

- URL Path: `/policies/{id}`

- Example

  - Request: 
    ` curl -X DELETE http://localhost:8080/policies/1`

  - Response:

    ```json
    {                                                                       
    	"message": "policies deleted" 
    }  
    ```

- Status Codes

  - `201 Deleted`: The policy rule was deleted successfully.
  - `404 Not found`: Invalid input data.

## Bandwidth Control - Endpoints

Policy rule means the "allow" or "deny" the connection between two IPs as well as the destination's port.

### 1. Add a bandwidth control rule

- HTTP Method: `POST`

- URL Path: `/bandwidth`

- Request Body:

  - `src_ip`: Source IP.
  - `dst_ip`: Destination IP.
  - `rates`: A list included two lists
    - `[[CIR bytes, Cburst bytes], [PIR bytes, Pburst bytes]]`
  - `dst_port`: Destination's Port.

- Example

  - Request: 
    ` curl -X POST -H  "Content-Type: application/json" -d '{"src_ip": "172.16.1.1", "dst_ip":"172.16.1.2", "rates": [[100000, 10000], [100000, 10000]],  "dst_port": "5201"}' http://localhost:8080/bandwidth `

  - Response:

    ```json
    { 
      "dst_ip": "172.16.1.2", 
      "dst_port": "5201", 
      "path": [
        "s1", 
        "s2" 
      ], 
      "rates": [ 
        [
          100000, 
          10000 
        ], 
        [
          100000,
          10000
        ] 
      ],
      "src_ip": "172.16.1.1"
    }   
    ```

- Status Codes

  - `201 Created`: The bandwidth-control rule was added successfully.
  - `400 Bad Request`: Invalid input data.
  - `409 Rule exists`: Rule already exists.

### 2. Find a bandwidth control rule

- HTTP Method: `GET`

- URL Path: `/bandwidth`

- example

  - Request: 
    `curl -X GET http://localhost:8080/bandwidth`

  - Response:

    ```json
    [
      {
        "dst_ip": "172.16.1.2", 
        "dst_port": "5201",
        "id": 0, 
        "path": [
          "s1",
          "s2"
        ], 
        "rates": [ 
          [ 
            100000,
            10000 
          ], 
          [ 
            100000, 
            10000 
          ]
        ], 
        "src_ip": "172.16.1.1" 
      }, 
      { 
        "dst_ip": "172.16.1.2",
        "dst_port": "5202",
        "id": 1, 
        "path": [
          "s1",
          "s2"
        ], 
        "rates": [ 
          [ 
            100000,
            10000 
          ], 
          [ 
            100000, 
            10000 
          ]
        ], 
        "src_ip": "172.16.1.1" 
      }
    ]
    ```

- Status Codes

  - `200`: Return the entries.

### 3. Update a bandwidth-control rule

- HTTP Method: `PUT`

- URL Path: `/policies`

- Request Body:

  - `src_ip`: Source IP.
  - `dst_ip`: Destination IP.
  - `rates`: A list included two lists
    - `[[CIR bytes, Cburst bytes], [PIR bytes, Pburst bytes]]`
  - `dst_port`: Destination's Port.

- example

  - Request: 
    `curl -X PUT -H  "Content-Type: application/json" -d '{"src_ip": "172.16.1.1", "dst_ip":"172.16.1.2", "rates": [[150000, 10000], [150000, 10000]],  "dst_port": "5201"}' http://localhost:8080/bandwidth`

  - Response:

    ```json
    { 
      "dst_ip": "172.16.1.2", 
      "dst_port": "5201", 
      "path": [
        "s1", 
        "s2" 
      ], 
      "rates": [ 
        [
          150000, 
          10000 
        ], 
        [
          150000,
          10000
        ] 
      ],
      "src_ip": "172.16.1.1"
    }   
    ```

- Status Codes

  - `201 Updated`: The bandwidth rule updated successfully.
  - `400 Bad Request`: Invalid input data.

### 4. Delete a bandwidth-control rule

- HTTP Method: `DELETE`

- URL Path: `/policies/{id}`

- example

  - Request: 
    ` curl -X DELETE http://localhost:8080/bandwidth/1`

  - Response:

    ```json
    {                                                                       
    	"message": "policies deleted" 
    }  
    ```

- Status Codes

  - `201 Deleted`: The bandwidth rule was deleted successfully.
  - `404 Not found`: Invalid input data.
