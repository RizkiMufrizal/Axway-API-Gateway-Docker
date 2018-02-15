#!/bin/bash

function prepareConfFiles(){

	local L_RPC_ADDRESS=${RPC_ADDRESS:=$HOSTNAME}
	local L_NATIVE_TRANSPORT_PORT=${NATIVE_TRANSPORT_PORT:=9042}
	local L_SEEDS=${SEEDS:=$HOSTNAME}
	local L_LISTEN_ADDRESS=${LISTEN_ADDRESS:=$HOSTNAME}

	echo "----------------------------------"
	echo "| Launching Cassandra on `pwd`"
	echo "| rpc_address: $L_RPC_ADDRESS"
	echo "| native_transport_port: $L_NATIVE_TRANSPORT_PORT"
	echo "| seeds: $L_SEEDS"
	echo "| listen_address: $L_LISTEN_ADDRESS"
	echo "----------------------------------"

	sed -r -i "s/rpc_address: localhost/rpc_address: $L_RPC_ADDRESS/g" $CASSANDRA_HOME/conf/cassandra.yaml
	sed -r -i "s/native_transport_port: 9042/native_transport_port: $L_NATIVE_TRANSPORT_PORT/g" $CASSANDRA_HOME/conf/cassandra.yaml
	sed -r -i "s/seeds: \"127.0.0.1\"/seeds: $L_SEEDS/g" $CASSANDRA_HOME/conf/cassandra.yaml
	sed -r -i "s/listen_address: localhost/listen_address: $L_LISTEN_ADDRESS/g" $CASSANDRA_HOME/conf/cassandra.yaml
}

function backoff(){
        if [ -z $START_BACKOFF_SECS ]; then
          START_BACKOFF_SECS=0
        fi
        echo "Node start backoff is $START_BACKOFF_SECS seconds"
        sleep $START_BACKOFF_SECS
}

backoff
prepareConfFiles
$CASSANDRA_HOME/bin/cassandra -f
