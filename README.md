# apigw-compose

## Pre-requsites

1. Knowledge and usage of API Gateway.
1. Docker and docker compose knowledge.

At least 16 GB of memory is required for 3 node manager (2 AMN), 3 gateway, 3 Cassandra test.

This software has been tested with:
1. Linux: Ubuntu 16.04
2. Docker: Refer to apigw-compose/apigw_containers_info.txt
3. Docker Compose: Refer to apigw-compose/apigw_containers_info.txt
4. Python: 2.7.12

## Overview

Using apigw-compose involves the following steps:

1. Build the static docker images that are required for your desired API Gateway topology.
2. Build the topology images from these static images.
3. Deploy and test.

## Running the pre-built Demo Images with API Gateway Manager and API Manager
* Download and extract APIGateway_7.5.3_Demo_DockerImage_linux-x86-64_BN<XYZ>.tar.gz to current directory
* Provide a license file in current directory, e.g. called mylicense.lic
* ```docker load < ./cassandra_centos-latest.tar.gz```
* ```docker load < ./gwlatest-1node_node1_centos-latest.tar.gz```
* ```export APIGW_LICENSE="$(cat ./mylicense.lic | gzip | base64)"```
* ```docker-compose up```
* API Gateway Manager and API Manager are accessible via the default ports. These ports are also mapped to the Docker host, so ```https://<docker-host-name>:8090``` and ```https://<docker-host-name>:8075``` can be used respectively

## Building static images

Static images are built rarely.
From these images you can create many different kinds of API Gateway topology images.

```
./build.py --installer <API GATEWAY install file> --license <API Gateway License file> --clean
```

Example:
```
./build.py --installer ~/dependencies/APIGateway_7.5.3_Install_linux-x86-64_BN201606301.run --license lic.lic --clean
```

We also provide the option to build API Gateway images from CentOS and RedHat Enterprise Linux 7 as a base OS. This can be achieved by supplying the --baseos parameter to the build.py script shown below, CentOS being the default OS should none be provided.

```
./build.py --installer <API GATEWAY install file> --license <API Gateway License file> --baseos <Base OS Family> --clean
```

Example:
```
./build.py --installer ~/dependencies/APIGateway_7.5.3_Install_linux-x86-64_BN201606301.run --license lic.lic --baseos redhat --clean
```

The following images are added to local Docker registry:
```
REPOSITORY                         TAG                         IMAGE ID            CREATED             SIZE
gwlatest-1node_node1_redhat        latest                      e8a8cce2fda8        16 seconds ago      1.45 GB
apigw_linux64_redhat               latest                      6e5df467493e        3 minutes ago       3.08 GB
cassandra_redhat                   latest                      0f2bc85350ea        6 minutes ago       512 MB
gwredhat                           latest                      c49e25206321        8 minutes ago       193 MB
registry.access.redhat.com/rhel7   latest                      a2d9f633eaab        4 weeks ago         193 MB
```

## Building topology images

```
./compose.py --config <JSON FILE definiting the topology>
```

Example:
```
./compose.py --config sample-compose-config/gwlatest-1nodeha-apimgr.json
```

Note:
* If the --baseos parameter was supplied to build.py then it must also be supplied to the compose.py script as shown below:
* If the --image option is not provided then the default image name used will be gwlatest_<baseos>, where <baseos> is the value of the --baseos parameter.

Example:
```
./compose.py --config sample-compose-config/gwlatest-1nodeha-apimgr.json --baseos redhat
```


Listed are the JSON topology files currently available in sample-compose-config
```
gwlatest-1node-apimgr.json:     1 api mgr + 1 admin node manager + 3 cassandra
gwlatest-2nodeha-apimgr.json    2 api mgr + 1 admin node manager + 1 node manager + 3 cassandra
gwlatest-3nodeha-apimgr.json    3 api mgr + 2 admin node manager + 1 node manager + 3 cassandra
```

The following images are added to local Docker registry (example for 3 node):
```
REPOSITORY                      TAG                 IMAGE ID            CREATED             SIZE
gwlatest-3nodeha-apimgr_node3   latest              fd20cb907be3        17 minutes ago      3.244 GB
gwlatest-3nodeha-apimgr_node2   latest              0c459c85df53        17 minutes ago      3.244 GB
gwlatest-3nodeha-apimgr_node1   latest              942792951b89        17 minutes ago      3.257 GB
```

A docker-compose YAML file is written to compose-generated/servers/<config_name>/docker-compose.yml

## Deploy and test images

You can run these images locally.
Or you can copy the images and docker-compose.yml to your docker compatible system.
Run docker-compose up to launch containers from the runtime images.

Example:
```
docker-compose -f compose-generated/servers/gwlatest-2nodeha-apimgr/docker-compose.yml up -d
```

Wait for services in containers to start.
Example:
```
ps -ef | grep vshell
root     19048 18558 11 15:36 ?        00:00:18 Node Manager on node1 (Node Manager Group) (7.5.3) (vshell)
root     19081 18627 12 15:36 ?        00:00:19 Node Manager on node2 (Node Manager Group) (7.5.3) (vshell)
root     19159 18558 23 15:37 ?        00:00:27 PortalInstance-1 (PortalGroup-1) (7.5.3) (vshell)
root     19193 18627 23 15:37 ?        00:00:27 PortalInstance-2 (PortalGroup-1) (7.5.3) (vshell)
```

### Expose ports
You can edit the docker-compose yaml file ... e.g. to expose ports:
```
version: '2'
services:

    node1:
        image: gwlatest-2nodeha-apimgr_node1
        hostname: node1
        privileged: true
        ports:
            - "8075:8075"
            - "8090:8090"
            - "8080:8080"

    node2:
        image: gwlatest-2nodeha-apimgr_node2
        links:
            - node1:node1
        hostname: node2
        privileged: true
   ...
```

### Persistent volumes

We need to create docker volumes for configuration and data persistence.
This is required for Node Manager, Gateway and Cassandra on each node.
The examples below show how to do this for the 3 node use case.

```
cd apigw-compose/src/util
# Create volumes for node1, node2, and node3
./volume.py --create --nodeName node1
./volume.py --create --nodeName node2
./volume.py --create --nodeName node3

# Create volumes for the Cassandra cluster
docker volume create --name cassandra-s1_DATA
docker volume create --name cassandra-s1_LOGS
docker volume create --name cassandra-s2_DATA
docker volume create --name cassandra-s2_LOGS
docker volume create --name cassandra-m_DATA
docker volume create --name cassandra-m_LOGS
```

This will create the following volumes
```
docker volume ls
DRIVER              VOLUME NAME
local               cassandra-m_DATA
local               cassandra-m_LOGS
local               cassandra-s1_DATA
local               cassandra-s1_LOGS
local               cassandra-s2_DATA
local               cassandra-s2_LOGS
local               node1_CONF_DATA
local               node1_EVENTS_DATA
local               node1_GROUP_DATA
local               node1_LOGS_DATA
local               node1_TRACE_DATA
local               node1_USER_DATA
local               node2_CONF_DATA
local               node2_EVENTS_DATA
local               node2_GROUP_DATA
local               node2_LOGS_DATA
local               node2_TRACE_DATA
local               node2_USER_DATA
local               node3_CONF_DATA
local               node3_EVENTS_DATA
local               node3_GROUP_DATA
local               node3_LOGS_DATA
local               node3_TRACE_DATA
local               node3_USER_DATA
```

note: if you wish to remove these volumes:
```
./volume.py --delete --nodeName node1
./volume.py --delete --nodeName node2
./volume.py --delete --nodeName node3
docker volume rm cassandra-s1_DATA
docker volume rm cassandra-s1_LOGS
docker volume rm cassandra-s2_DATA
docker volume rm cassandra-s2_LOGS
docker volume rm cassandra-m_DATA
docker volume rm cassandra-m_LOGS
```

Then, enable the volumes in the generated docker-compose yaml file. Example:

```
version: '2'
services:

    node1:
        image: gwlatest-3nodeha-apimgr_node1
        links:
        - cassandra-m
        - cassandra-s1
        - cassandra-s2
        volumes:
        #  Configuring volume for Node Manager conf (modified using API Gateway Manager web application)
        -  node1_CONF_DATA:/opt/Axway/apigateway/conf
        #  Configuring volume for Node Manager trace (modified using API Gateway Manager web application)
        -  node1_TRACE_DATA:/opt/Axway/apigateway/trace
        #  Configuring volume for Node Manager logs (includes Domain and Transaction logs modified using API Gateway Manager web application)
        -  node1_LOGS_DATA:/opt/Axway/apigateway/logs
        #  Configuring volume for Node Manager events (modified using API Gateway Manager web application)
        -  node1_EVENTS_DATA:/opt/Axway/apigateway/events
        #  Configuring volume for API Gateway Group Configuration, data, logging and trace.
        -  node1_GROUP_DATA:/opt/Axway/apigateway/groups
        #  Configuring volume for API Gateway user data eg. ActiveMQ, File-based filters, Ehcache etc
        -  node1_USER_DATA:/custom_path/to/userdata/
        hostname: node1
        environment:
        - START_BACKOFF_SECS=180 # starts after Cassandra cluster and 30s after previous instance
        - CASSANDRA_HOSTS=cassandra-m,cassandra-s1,cassandra-s2
        privileged: true


    node2:
        image: gwlatest-3nodeha-apimgr_node2
        links:
        - cassandra-m
        - cassandra-s1
        - cassandra-s2
        volumes:
        #  Configuring volume for Node Manager conf (modified using API Gateway Manager web application)
        -  node2_CONF_DATA:/opt/Axway/apigateway/conf
        #  Configuring volume for Node Manager trace (modified using API Gateway Manager web application)
        -  node2_TRACE_DATA:/opt/Axway/apigateway/trace
        #  Configuring volume for Node Manager logs (includes Domain and Transaction logs modified using API Gateway Manager web application)
        -  node2_LOGS_DATA:/opt/Axway/apigateway/logs
        #  Configuring volume for Node Manager events (modified using API Gateway Manager web application)
        -  node2_EVENTS_DATA:/opt/Axway/apigateway/events
        #  Configuring volume for API Gateway Group Configuration, data, logging and trace.
        -  node2_GROUP_DATA:/opt/Axway/apigateway/groups
        #  Configuring volume for API Gateway user data eg. ActiveMQ, File-based filters, Ehcache etc
        -  node2_USER_DATA:/custom_path/to/userdata/
        hostname: node2
        environment:
        - START_BACKOFF_SECS=210 # starts after Cassandra cluster and 30s after previous instance
        - CASSANDRA_HOSTS=cassandra-m,cassandra-s1,cassandra-s2
        privileged: true


    node3:
        image: gwlatest-3nodeha-apimgr_node3
        links:
        - cassandra-m
        - cassandra-s1
        - cassandra-s2
        volumes:
        #  Configuring volume for Node Manager conf (modified using API Gateway Manager web application)
        -  node3_CONF_DATA:/opt/Axway/apigateway/conf
        #  Configuring volume for Node Manager trace (modified using API Gateway Manager web application)
        -  node3_TRACE_DATA:/opt/Axway/apigateway/trace
        #  Configuring volume for Node Manager logs (includes Domain and Transaction logs modified using API Gateway Manager web application)
        -  node3_LOGS_DATA:/opt/Axway/apigateway/logs
        #  Configuring volume for Node Manager events (modified using API Gateway Manager web application)
        -  node3_EVENTS_DATA:/opt/Axway/apigateway/events
        #  Configuring volume for API Gateway Group Configuration, data, logging and trace.
        -  node3_GROUP_DATA:/opt/Axway/apigateway/groups
        #  Configuring volume for API Gateway user data eg. ActiveMQ, File-based filters, Ehcache etc
        -  node3_USER_DATA:/custom_path/to/userdata/
        hostname: node3
        environment:
        - START_BACKOFF_SECS=240 # starts after Cassandra cluster and 30s after previous instance
        - CASSANDRA_HOSTS=cassandra-m,cassandra-s1,cassandra-s2
        privileged: true


    cassandra-m:
        image: cassandra
        environment:
        - START_BACKOFF_SECS=0 # prevents race between nodes joining the cluster
        - SEEDS=cassandra-m
        - MAX_HEAP_SIZE=1G
        - HEAP_NEWSIZE=400m
        volumes:
        #  Cassandra data volume
        -  cassandra-m_DATA:/opt/cassandra/data
        #  Cassandra logs volume
        -  cassandra-m_LOGS:/opt/cassandra/logs
        image: cassandra
        hostname: cassandra-m
        restart: on-failure:2


    cassandra-s1:
        image: cassandra
        environment:
        - START_BACKOFF_SECS=60 # prevents race between nodes joining the cluster
        - SEEDS=cassandra-m
        - MAX_HEAP_SIZE=1G
        - HEAP_NEWSIZE=400m
        volumes:
        #  Cassandra data volume
        -  cassandra-s1_DATA:/opt/cassandra/data
        #  Cassandra logs volume
        -  cassandra-s1_LOGS:/opt/cassandra/logs
        image: cassandra
        hostname: cassandra-s1
        restart: on-failure:2


    cassandra-s2:
        image: cassandra
        environment:
        - START_BACKOFF_SECS=120 # prevents race between nodes joining the cluster
        - SEEDS=cassandra-m
        - MAX_HEAP_SIZE=1G
        - HEAP_NEWSIZE=400m
        volumes:
        #  Cassandra data volume
        -  cassandra-s2_DATA:/opt/cassandra/data
        #  Cassandra logs volume
        -  cassandra-s2_LOGS:/opt/cassandra/logs
        image: cassandra
        hostname: cassandra-s2
        restart: on-failure:2

volumes:
   node1_CONF_DATA:
       external: true
   node1_TRACE_DATA:
       external: true
   node1_LOGS_DATA:
       external: true
   node1_EVENTS_DATA:
       external: true
   node1_GROUP_DATA:
       external: true
   node1_USER_DATA:
       external: true
   node2_CONF_DATA:
       external: true
   node2_TRACE_DATA:
       external: true
   node2_LOGS_DATA:
       external: true
   node2_EVENTS_DATA:
       external: true
   node2_GROUP_DATA:
       external: true
   node2_USER_DATA:
       external: true
   node3_CONF_DATA:
       external: true
   node3_TRACE_DATA:
       external: true
   node3_LOGS_DATA:
       external: true
   node3_EVENTS_DATA:
       external: true
   node3_GROUP_DATA:
       external: true
   node3_USER_DATA:
       external: true
   cassandra-m_DATA:
       external: true
   cassandra-m_LOGS:
       external: true
   cassandra-s1_DATA:
       external: true
   cassandra-s1_LOGS:
       external: true
   cassandra-s2_DATA:
       external: true
   cassandra-s2_LOGS:
       external: true
```



*Note:* In the volumes section of the docker-compose.yaml seen above, the user data container path '/custom_path/to/userdata' should be updated as desired. It is recommended that all user data be stored in a centralised location for convenience.

#### A few examples explaining how user data can be persisted:

a. Filters in Policy Studio specifying user-defined directories:
1. If your policy uses a file-based filter eg. File Download filter (or File Upload, Save to File etc) that allows a user-defined directory, such as '/home/user/Downloads' inside the container.
2. Create a volume for the user data (eg GatewayNODE2_userdata) on the host.
3. Get the full path of the volume created on the host
    ```
    $ docker volume inspect --name GatewayNODE1_userdata
    /var/lib/docker/volumes/GatewayNODE2_userdata/_data
    ```
4. Update the line to the docker-compose.yaml as shown below:
    ```
    volumes:
      #  Configuring volume for API Gateway user data eg. ActiveMQ, File-based filters, Ehcache etc
      - /var/lib/docker/volumes/GatewayNODE1_userdata/_data:/home/user/Downloads
    ```
b. Using Directory Scanner (Environment Configuration > Listeners > API Gateway (right-click)):
    The Directory Scanner allows specifying multiple directory locations on disk ie. Input, Processing and Response directories. There are two ways by which this data can be persisted:

* Create a directory inside the container eg. /home/userdata/DirectoryScanner and set it as the directory path for all and update the entry in the YAML as:
    ```
    - /var/lib/docker/volumes/GatewayNODE1_userdata/_data:/home/userdata/DirectoryScanner
    ```
* Create a nested directory inside the container
 eg.
    ```
    /home/userdata/DirectoryScanner/Input
    /home/userdata/DirectoryScanner/Processing
    /home/userdata/DirectoryScanner/Response
    ```
    The corresponding yaml entry will be:
    ```
    - /var/lib/docker/volumes/GatewayNODE1_userdata/_data:/home/userdata/DirectoryScanner
    ```
 * Create multiple volumes with a one-one mapping with container paths:
    The corresponding yaml entries will be:
    ```
    - /var/lib/docker/volumes/GatewayNODE1_userdata1/_data:/home/userdata/DirectoryScanner/Input
    - /var/lib/docker/volumes/GatewayNODE1_userdata2/_data:/home/userdata/DirectoryScanner/Processing
    - /var/lib/docker/volumes/GatewayNODE1_userdata3/_data:/home/userdata/DirectoryScanner/Response
    ```

Finally, bring up the system:

Example:
```
docker-compose -f compose-generated/servers/gwlatest-2nodeha-apimgr/docker-compose.yml up -d
```

Wait for services in containers to start.
Example:
```
ps -ef | grep vshell
root     19048 18558 11 15:36 ?        00:00:18 Node Manager on node1 (Node Manager Group) (7.5.3) (vshell)
root     19081 18627 12 15:36 ?        00:00:19 Node Manager on node2 (Node Manager Group) (7.5.3) (vshell)
root     19159 18558 23 15:37 ?        00:00:27 PortalInstance-1 (PortalGroup-1) (7.5.3) (vshell)
root     19193 18627 23 15:37 ?        00:00:27 PortalInstance-2 (PortalGroup-1) (7.5.3) (vshell)
```


##### Some tests that can be done to check if the system is running:

1. Healthcheck:
    ```
    curl http://localhost:8080/healthcheck
    <status>ok</status>        
    ```

2. API Manager:
    ```
    Goto: https://localhost:8075/home
    ```

## Notes - Cassandra Heap
In file opt/cassandra/conf/cassandra-env.sh, heap sizes have been modified to
the following:
```
MAX_HEAP_SIZE=1G
HEAP_NEWSIZE=200M
```
Previous values were:
```
MAX_HEAP_SIZE=4G
HEAP_NEWSIZE=800M
```
