pipeline {
  agent none
  options {
    buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '10'))
    disableConcurrentBuilds()
    skipDefaultCheckout(true)
  }
  parameters {
    booleanParam(name: 'LAB_MODE', defaultValue: false, description: 'Usar código montado localmente no laboratório')
    booleanParam(name: 'ENABLE_AZURE_DEPLOY', defaultValue: false, description: 'Exige credenciais Azure configuradas no Jenkins')
    string(name: 'ACR_LOGIN_SERVER', defaultValue: '', description: 'Ex.: carparts.azurecr.io')
    string(name: 'RESOURCE_GROUP', defaultValue: '', description: 'Grupo de recursos Azure')
    string(name: 'STAGING_APP', defaultValue: '', description: 'Container App de homologação')
    string(name: 'PRODUCTION_APP', defaultValue: '', description: 'Container App de produção')
    string(name: 'STAGING_URL', defaultValue: '', description: 'URL HTTPS da homologação')
  }
  environment { IMAGE_NAME = 'carparts-b2b-demo' }
  stages {
    stage('Checkout') {
      agent { label 'linux-docker' }
      options { timeout(time: 10, unit: 'MINUTES') }
      steps {
        script {
          if (params.LAB_MODE) {
            sh 'cp -R /project/src /project/test /project/scripts /project/package.json /project/Dockerfile /project/.dockerignore ./'
            env.SOURCE_COMMIT = sh(script: 'cd /project && git -c safe.directory=/project rev-parse HEAD', returnStdout: true).trim()
          } else {
            checkout scm
            env.SOURCE_COMMIT = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
          }
        }
      }
    }
    stage('Qualidade') {
      agent { label 'linux-docker' }
      options { timeout(time: 15, unit: 'MINUTES') }
      steps { sh 'docker build --target lint -t carparts-lint:${BUILD_NUMBER} .' }
    }
    stage('Testes') {
      agent { label 'linux-docker' }
      options { timeout(time: 15, unit: 'MINUTES') }
      steps {
        sh '''
          set -eu
          docker build --target test -t carparts-test:${BUILD_NUMBER} .
          cid=$(docker create carparts-test:${BUILD_NUMBER})
          mkdir -p reports
          docker cp "$cid:/app/reports/." reports/
          docker rm "$cid"
        '''
      }
      post { always { junit allowEmptyResults: false, testResults: 'reports/junit.xml' } }
    }
    stage('Imagem imutável') {
      agent { label 'linux-docker' }
      options { timeout(time: 15, unit: 'MINUTES') }
      steps {
        sh 'docker build --target production -t carparts-b2b-demo:${BUILD_NUMBER} .'
        sh '''
          mkdir -p evidence
          printf '{"build":"%s","commit":"%s","image":"carparts-b2b-demo:%s","timestamp":"%s"}\n' "$BUILD_NUMBER" "$SOURCE_COMMIT" "$BUILD_NUMBER" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > evidence/build.json
        '''
        archiveArtifacts artifacts: 'evidence/build.json', fingerprint: true
      }
    }
    stage('Publicar no ACR') {
      when { beforeAgent true; allOf { branch 'main'; expression { return params.ENABLE_AZURE_DEPLOY } } }
      agent { label 'linux-docker' }
      options { timeout(time: 15, unit: 'MINUTES') }
      steps {
        withCredentials([usernamePassword(credentialsId: 'azure-sp', usernameVariable: 'AZURE_CLIENT_ID', passwordVariable: 'AZURE_CLIENT_SECRET')]) {
          sh '''
            set +x
            set -eu
            printf '%s' "$AZURE_CLIENT_SECRET" | docker login "$ACR_LOGIN_SERVER" -u "$AZURE_CLIENT_ID" --password-stdin
            docker tag "carparts-b2b-demo:$BUILD_NUMBER" "$ACR_LOGIN_SERVER/$IMAGE_NAME:$BUILD_NUMBER-$SOURCE_COMMIT"
            docker push "$ACR_LOGIN_SERVER/$IMAGE_NAME:$BUILD_NUMBER-$SOURCE_COMMIT"
            docker logout "$ACR_LOGIN_SERVER" >/dev/null
          '''
          script {
            env.IMAGE_REF = sh(script: 'docker image inspect --format "{{index .RepoDigests 0}}" "$ACR_LOGIN_SERVER/$IMAGE_NAME:$BUILD_NUMBER-$SOURCE_COMMIT"', returnStdout: true).trim()
          }
        }
      }
    }
    stage('Homologação Azure') {
      when { beforeAgent true; allOf { branch 'main'; expression { return params.ENABLE_AZURE_DEPLOY } } }
      agent { label 'linux-docker' }
      options { timeout(time: 20, unit: 'MINUTES') }
      steps {
        withCredentials([
          usernamePassword(credentialsId: 'azure-sp', usernameVariable: 'AZURE_CLIENT_ID', passwordVariable: 'AZURE_CLIENT_SECRET'),
          string(credentialsId: 'azure-tenant', variable: 'AZURE_TENANT_ID'),
          string(credentialsId: 'azure-subscription', variable: 'AZURE_SUBSCRIPTION_ID')
        ]) {
          sh '''
            set +x
            set -eu
            docker run --rm -e AZURE_CLIENT_ID -e AZURE_CLIENT_SECRET -e AZURE_TENANT_ID -e AZURE_SUBSCRIPTION_ID -e RESOURCE_GROUP -e STAGING_APP -e IMAGE_REF mcr.microsoft.com/azure-cli:2.77.0 sh -ec '
              az login --service-principal -u "$AZURE_CLIENT_ID" -p "$AZURE_CLIENT_SECRET" --tenant "$AZURE_TENANT_ID" --output none
              az account set --subscription "$AZURE_SUBSCRIPTION_ID"
              az containerapp update --name "$STAGING_APP" --resource-group "$RESOURCE_GROUP" --image "$IMAGE_REF" --output none
            '
            for n in 1 2 3 4 5 6 7 8 9 10; do
              if docker run --rm curlimages/curl:8.11.1 -fsS "$STAGING_URL/health" | grep -q '"status":"ok"'; then exit 0; fi
              sleep 12
            done
            exit 1
          '''
        }
      }
    }
    stage('Aprovação produção') {
      when { beforeInput true; allOf { branch 'main'; expression { return params.ENABLE_AZURE_DEPLOY } } }
      agent { label 'linux-docker' }
      options { timeout(time: 2, unit: 'DAYS') }
      input {
        message 'Promover a mesma imagem validada em homologação para produção?'
        ok 'Aprovar publicação'
        submitter 'admin,release-managers'
        submitterParameter 'APPROVED_BY'
      }
      steps {
        script { env.RELEASE_APPROVER = env.APPROVED_BY }
        echo "Aprovação registrada por ${env.RELEASE_APPROVER}; imagem ${env.IMAGE_REF}"
      }
    }
    stage('Produção Azure') {
      when { beforeAgent true; allOf { branch 'main'; expression { return params.ENABLE_AZURE_DEPLOY } } }
      agent { label 'linux-docker' }
      options { timeout(time: 20, unit: 'MINUTES') }
      steps {
        withCredentials([
          usernamePassword(credentialsId: 'azure-sp', usernameVariable: 'AZURE_CLIENT_ID', passwordVariable: 'AZURE_CLIENT_SECRET'),
          string(credentialsId: 'azure-tenant', variable: 'AZURE_TENANT_ID'),
          string(credentialsId: 'azure-subscription', variable: 'AZURE_SUBSCRIPTION_ID')
        ]) {
          sh '''
            set +x
            set -eu
            docker run --rm -e AZURE_CLIENT_ID -e AZURE_CLIENT_SECRET -e AZURE_TENANT_ID -e AZURE_SUBSCRIPTION_ID -e RESOURCE_GROUP -e PRODUCTION_APP -e IMAGE_REF mcr.microsoft.com/azure-cli:2.77.0 sh -ec '
              az login --service-principal -u "$AZURE_CLIENT_ID" -p "$AZURE_CLIENT_SECRET" --tenant "$AZURE_TENANT_ID" --output none
              az account set --subscription "$AZURE_SUBSCRIPTION_ID"
              az containerapp update --name "$PRODUCTION_APP" --resource-group "$RESOURCE_GROUP" --image "$IMAGE_REF" --output none
            '
          '''
          echo "Produção: commit ${env.SOURCE_COMMIT}; imagem ${env.IMAGE_REF}; aprovador ${env.RELEASE_APPROVER}"
        }
      }
    }
  }
  post {
    success { echo "Build ${env.BUILD_NUMBER} concluído para commit ${env.SOURCE_COMMIT}" }
    failure { echo "Build ${env.BUILD_NUMBER} falhou; consultar testes, log e artefatos" }
    aborted { echo "Build ${env.BUILD_NUMBER} cancelado ou não aprovado" }
  }
}
