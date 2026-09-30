FROM docker:27-cli AS dockercli
FROM jenkins/inbound-agent:jdk21
USER root
COPY --from=dockercli /usr/local/bin/docker /usr/local/bin/docker
USER jenkins
