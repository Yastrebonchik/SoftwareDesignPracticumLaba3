FROM maven:3.9.11-eclipse-temurin-21-alpine@sha256:922927df2c662cdd47ddb116443d6bec4696cfae3de1a0ddac8fcc7b87ce61ae AS builder
WORKDIR /build
COPY app/pom.xml .
RUN mvn -B -ntp dependency:go-offline
COPY app/src ./src
RUN mvn -B -ntp package

FROM ubuntu:24.04@sha256:2198e4c65076e9cb0b3d695219df667c0e3b0072da64ca3c2648aca17dcecaf5
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ansible-core openssh-client ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /ansible
COPY --from=builder /build/target/app.jar /artifacts/app.jar
COPY ansible/ /ansible/
COPY docker/master/entrypoint.sh /usr/local/bin/master-entrypoint
RUN chmod 755 /usr/local/bin/master-entrypoint
ENTRYPOINT ["/usr/local/bin/master-entrypoint"]
CMD ["sleep", "infinity"]
