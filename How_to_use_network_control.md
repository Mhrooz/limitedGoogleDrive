# How to use the network control part

The network topology used in this project:

![network topology](topo.svg)

## How to use

Follow these steps to use this repository:

1. Log in to the server and upload the codes.

   ```bash
    user@localhost:~$ scp -r ./limitedGoogleDrive rnp@gruppeXX:
   ```

2. Copy the folder to `router4` for compilation.

   ```bash
   rnp@gruppeXX:~$ scp -r ./limitedGoogleDrive router4:~/
   ```

3. Compile the code on `router4`.

   ```bash
   rnp@gruppeXX:~$ ssh router4 "mkdir build"
   rnp@gruppeXX:~$ ssh router4 "p4c-bm2-ss --p4v 16 --p4runtime-files build/packetinout_directcounter.p4info.txt -o build/packetinout_directcounter.json ~/assignment/packetinout_directcounter.p4"
    rnp@gruppeXX:~$ ssh router4 "cp -r ~/build ~/assignment/build"
   ```

4. Transfer the compiled files from `router4` to the switches:

   ```bash
   rnp@Gruppe05:~$ scp -r router4:~/build ./
   rnp@Gruppe05:~$ scp -r ./build s1:
   rnp@Gruppe05:~$ scp -r ./build s2:
   rnp@Gruppe05:~$ scp -r ./build s3:
   ```

5. Start the P4 switch on each of the switches (`s1`, `s2`, `s3`) with the compiled code:

   1. If you run the code for the first time, please run `mkdir pcaps` on switch machines

   ```bash
   root@s1:~$ sudo simple_switch_grpc -i 1@eth1 -i 2@eth2 -i 3@eth3 --pcap pcaps --nanolog ipc:///tmp/s1-log.ipc --device-id 1 build/packetinout_directcounter.json --log-console --thrift-port 9090 -- --grpc-server-addr 0.0.0.0:50051 --cpu-port 255
   ```

   ```bash
   root@s2:~$ sudo simple_switch_grpc -i 1@eth1 -i 2@eth2 -i 3@eth3 --pcap pcaps --nanolog ipc:///tmp/s1-log.ipc --device-id 2 build/packetinout_directcounter.json --log-console --thrift-port 9090 -- --grpc-server-addr 0.0.0.0:50051 --cpu-port 255
   ```

   ```bash
   root@s3:~$ sudo simple_switch_grpc -i 1@eth1 -i 2@eth2 -i 3@eth3 --pcap pcaps --nanolog ipc:///tmp/s1-log.ipc --device-id 3 build/packetinout_directcounter.json --log-console --thrift-port 9090 -- --grpc-server-addr 0.0.0.0:50051 --cpu-port 255
   ```

6. Execute the controller program from `router4`:

   ```bash
   root@router4:~$ cp -r build ./limitedGoogleDrive/
   root@router4:~$ cd limitedGoogleDrive
   root@router4:~$ python3 main.py
   ```

## Test Policy

If everything works well, now you can use `iperf3` to generate traffic volume between `pc1` and `pc2`.

### Normal(allow) case

First we start a iperf3 server on `pc2`.

```bash
root@pc2:~$ iperf3 -s
```

Then we sent traffic from `pc1` in 100 Kbps bandwidth:

```bash
root@pc1:~$ iperf3 -c 192.168.1.2 --bandwidth 100K -t 120
```

Now you can observe on `pc1`:

```bash
Connecting to host 192.168.1.2, port 5201
[  5] local 192.168.1.1 port 57795 connected to 192.168.1.2 port 5201
[ ID] Interval           Transfer     Bitrate         Total Datagrams
[  5]   0.00-1.00   sec  12.7 KBytes   104 Kbits/sec  9
[  5]   1.00-2.00   sec  12.7 KBytes   104 Kbits/sec  9
[  5]   2.00-3.00   sec  11.3 KBytes  92.7 Kbits/sec  8
[  5]   3.00-4.00   sec  12.7 KBytes   104 Kbits/sec  9
[  5]   4.00-5.00   sec  12.7 KBytes   104 Kbits/sec  9
[  5]   5.00-6.00   sec  11.3 KBytes  92.7 Kbits/sec  8
....
```

On `pc2`:

```bash
-----------------------------------------------------------
Server listening on 5201
-----------------------------------------------------------
Accepted connection from 192.168.1.1, port 35014
[  5] local 192.168.1.2 port 5201 connected to 192.168.1.1 port 57795
[ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
[  5]   0.00-1.00   sec  11.3 KBytes  92.7 Kbits/sec  5.667 ms  0/8 (0%)
[  5]   1.00-2.00   sec  12.7 KBytes   104 Kbits/sec  7.144 ms  0/9 (0%)
[  5]   2.00-3.00   sec  11.3 KBytes  92.6 Kbits/sec  7.646 ms  0/8 (0%)
[  5]   3.00-4.00   sec  12.7 KBytes   104 Kbits/sec  8.915 ms  0/9 (0%)
[  5]   4.00-5.00   sec  12.7 KBytes   104 Kbits/sec  16.591 ms  0/9 (0%)
[  5]   5.00-6.00   sec  11.3 KBytes  92.7 Kbits/sec  18.878 ms  0/8 (0%)
.....
```

### Deny case

First we add the policy rule to the controller:

```bash
root@router4:~$ curl -X POST -H "Content-Type: application/json" -d '{"src_ip": "192.168.1.1", "dst_ip": "192.16.1.2", "dst_port": "5201", "action": "deny"}' http://localhost:8080/policies
```

Sent traffic from `pc1` in 200 Kbps bandwidth:

```bash
root@pc1:~$ iperf3 -c 192.168.1.2 --bandwidth 200K -t 120
```

```bash
Connecting to host 192.168.1.2, port 5201
[  5] local 192.168.1.1 port 54898 connected to 192.168.1.2 port 5201
[ ID] Interval           Transfer     Bitrate         Total Datagrams
[  5]   0.00-1.00   sec  0.00 Bytes  0.00 bits/sec
[  5]   1.00-2.00   sec  0.00 Bytes  0.00 bits/sec
[  5]   2.00-3.00   sec  0.00 Bytes  0.00 bits/sec
[  5]   3.00-4.00   sec  0.00 Bytes  0.00 bits/sec
....
```



## Bandwidth Control

If you generate traffic volumn to 1M:

```bash
root@pc1:~# iperf3 -c 192.168.1.2 -t 100 -b 1M -u
Connecting to host 192.168.1.2, port 5201
[  5] local 192.168.1.1 port 41856 connected to 192.168.1.2 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd  
[  5]   0.00-1.00   sec  76.4 KBytes   625 Kbits/sec   15   2.83 KBytes
[  5]   1.00-2.00   sec  0.00 Bytes  0.00 bits/sec   14   2.83 KBytes
[  5]   2.00-3.00   sec   124 KBytes  1.02 Mbits/sec   27   2.83 KBytes 
[  5]   3.00-4.00   sec   124 KBytes  1.02 Mbits/sec   34   2.83 KBytes
[  5]   4.00-5.00   sec  93.3 KBytes   764 Kbits/sec   30   2.83 KBytes   
...

```

On `pc2`, you can observe the output is like:

```
-----------------------------------------------------------
Server listening on 5201
-----------------------------------------------------------
Accepted connection from 192.168.1.1, port 35028
[  5] local 192.168.1.2 port 5201 connected to 192.168.1.1 port 41856
[ ID] Interval           Transfer     Bitrate 
[  5]   0.00-4.12   sec   256 KBytes   509 Kbits/sec
[  5]   4.12-6.29   sec   256 KBytes   964 Kbits/sec  
[  5]   6.29-8.36   sec   256 KBytes  1.02 Mbits/sec 
[  5]   8.36-10.31  sec   256 KBytes  1.07 Mbits/sec 
```

Let's try to limit the bandwidth to 500K:

```bash
root@router4:~$ curl -X POST -H "Content-Type: application/json" -d '{"src_ip": "172.16.1.1", "dst_ip": "172.16.1.2", "rates": [[62500, 10000], [62500, 10000]], "dst_port": "5201"}' http://localhost:8080/bandwidth
```

And generate traffics:

```bash
root@pc1:~# iperf3 -c 192.168.1.2 -t 100 -b 1M -u
Connecting to host 192.168.1.2, port 5201
[  5] local 192.168.1.1 port 41856 connected to 192.168.1.2 port 5201
[ ID]   Interval         Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00 sec   102 KBytes   833 Kbits/sec   13    2.83 KBytes
[  5]   1.00-2.00 sec   0.00 Bytes   0.00 bits/sec   12    2.83 KBytes
[  5]   2.00-3.00 sec   0.00 Bytes   0.00 bits/sec   12    2.83 KBytes
[  5]   3.00-4.00 sec   0.00 Bytes   0.00 bits/sec   10    2.83 KBytes
[  5]   4.00-5.00 sec   31.1 KBytes  255 Kbits/sec   8     2.83 KBytes
[  5]   5.00-6.00 sec   0.00 Bytes   0.00 bits/sec   10    2.83 KBytes
[  5]   6.00-7.00 sec   31.1 KBytes  255 Kbits/sec   10    2.83 KBytes
[  5]   7.00-8.00 sec   31.1 KBytes  255 Kbits/sec   11    2.83 KBytes
[  5]   8.00-9.00 sec   0.00 Bytes   0.00 bits/sec   10    2.83 KBytes
```

Now on server side:

```bash
-----------------------------------------------------------
Server listening on 5201
-----------------------------------------------------------
Accepted connection from 192.168.1.1, port 35028
[  5] local 192.168.1.2 port 5201 connected to 192.168.1.1 port 41856
[ ID]   Interval            Transfer     Bitrate
[  5]   0.00-15.16 sec      256 KBytes   138 Kbits/sec
[  5]   15.16-29.45 sec     256 KBytes   147 Kbits/sec
[  5]   29.45-39.43 sec     256 KBytes   210 Kbits/sec
[  5]   39.43-49.43 sec     109 KBytes   89.0 Kbits/sec
[  5]   49.43-61.32 sec     256 KBytes   176 Kbits/sec
[  5]   61.32-73.25 sec     256 KBytes   176 Kbits/sec
[  5]   73.25-84.99 sec     256 KBytes   179 Kbits/sec
[  5]   84.99-97.08 sec     256 KBytes   173 Kbits/sec
[  5]   97.08-108.00 sec    256 KBytes   192 Kbits/sec
```



