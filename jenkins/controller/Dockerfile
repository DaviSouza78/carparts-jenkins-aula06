FROM jenkins/jenkins:2.568.3-jdk21
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"
ENV CASC_JENKINS_CONFIG=/jenkins-config/casc.yaml
COPY casc.yaml /jenkins-config/casc.yaml
