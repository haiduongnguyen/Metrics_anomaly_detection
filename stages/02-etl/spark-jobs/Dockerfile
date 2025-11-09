FROM python:3.11-slim

# Install Java (required for PySpark)
RUN apt-get update && \
    apt-get install -y openjdk-21-jre-headless curl procps && \
    rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Install PySpark
RUN pip install --no-cache-dir pyspark==3.5.0

# Install AWS SDK for Hadoop (S3 support)
RUN mkdir -p /opt/spark/jars && \
    curl -o /opt/spark/jars/hadoop-aws-3.3.4.jar https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    curl -o /opt/spark/jars/aws-java-sdk-bundle-1.12.262.jar https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar

# Copy Spark job scripts
WORKDIR /app/spark-jobs
COPY *.py ./

# Make scripts executable
RUN chmod +x *.py

# Keep container running
CMD ["tail", "-f", "/dev/null"]
