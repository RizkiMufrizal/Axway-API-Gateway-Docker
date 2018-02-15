# Standalone cassandra node
FROM registry.access.redhat.com/rhel7:latest

MAINTAINER support@axway.com

ENV CASSANDRA_VERSION=2.2.8
ENV CASSANDRA_HOME=/opt/cassandra
ENV PATH $CASSANDRA_HOME/bin:$PATH
ENV JAVA_HOME /usr/java/jre1.8.0_131
ENV PATH $PATH:$JAVA_HOME/bin

RUN cd /usr && \
    mkdir -p java && \
    cd java && \    
    curl -L -b "oraclelicense=a" http://download.oracle.com/otn-pub/java/jdk/8u131-b11/d54c1d3a095b4ff2b6607d096fa80163/jre-8u131-linux-x64.tar.gz -o jre-8u131-b11-linux-x64.tar.gz &&\
    tar -zxf jre-8u131-b11-linux-x64.tar.gz && \
    rm jre*.tar.gz
    
RUN curl http://archive.apache.org/dist/cassandra/$CASSANDRA_VERSION/apache-cassandra-$CASSANDRA_VERSION-bin.tar.gz -o /tmp/cassandra.tgz &&\        
    mkdir $CASSANDRA_HOME &&\
    tar zxf /tmp/cassandra.tgz -C $CASSANDRA_HOME --strip-components=1 &&\
    rm /tmp/cassandra.tgz &&\
    sed -i 's|start_rpc:|#start_rpc:|' $CASSANDRA_HOME/conf/cassandra.yaml &&\
    sed -i 's|rpc_port:|#rpc_port:|' $CASSANDRA_HOME/conf/cassandra.yaml

WORKDIR $CASSANDRA_HOME/bin
VOLUME $CASSANDRA_HOME/data

ADD cassandra-launch.sh $CASSANDRA_HOME/bin/
RUN chmod u+x $CASSANDRA_HOME/bin/cassandra-launch.sh

CMD ["/opt/cassandra/bin/cassandra-launch.sh"]

# 7000: intra-node communication
# 7001: TLS intra-node communication
# 7199: JMX
# 9042: CQL

EXPOSE 7000 7001 7199 9042
