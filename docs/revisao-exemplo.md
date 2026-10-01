# Revisão de exemplo · E5

Este pull request de demonstração valida a revisão de branch, os testes e o check Jenkins antes de integrar na main. A revisão deve conferir sintaxe do Jenkinsfile, permissões das credenciais e promoção do mesmo digest de homologação para produção.

O Jenkins GitHub Multibranch descobriu main e PR-1. Os builds main #1 e PR-1 #2 terminaram SUCCESS; o GitHub mostrou o check `continuous-integration/jenkins/pr-merge` verde. Um webhook HTTPS temporário, restrito a `/github-webhook/` e validado por HMAC, entregou eventos ping e pull_request com resposta HTTP 200. Este commit exercita também os eventos push e pull_request.synchronize. A revisão independente segue pendente.
