# Carparts · projeto Jenkins CI/CD (Aula 06)

Projeto demonstrativo produzido para a atividade SAP1-DEVOPS, com API Node.js e front-end simples, Jenkins autogerenciado em Docker, configuração JCasC, agent Linux separado, Jenkinsfile declarativo e roteiro Azure/GitHub.

## Estado verificado em 30/09/2026

| Entregável | Material | Evidência |
|---|---|---|
| E1 Arquitetura | `docs/E1-arquitetura.md`, `compose.yaml` | Controller local e agent Linux online; `evidence/live/nodes.json` mostra 0/2 executores |
| E2 Controller | `jenkins/controller/Dockerfile`, `plugins.txt`, `casc.yaml` | Subida real em `evidence/live/controller-startup.log`; plugins diretos fixados por versão; sem acesso anônimo; nó interno com 0 executores |
| E3 Pipeline | `Jenkinsfile`, `Dockerfile`, `src/`, `test/` | Onze builds locais consecutivos bem-sucedidos (#2–#12), quatro testes publicados no build #12, logs e artefato em `evidence/live/` |
| E4 Azure | `azure/provision.sh`, `docs/E4-azure.md`, stages Azure no Jenkinsfile | Build demonstrativo #2 publicou no ACR, testou homologação, registrou aprovação e promoveu o mesmo digest para produção; evidências em `evidence/live/azure-*`; recursos temporários excluídos após o teste |
| E5 Multibranch | `docs/E5-github.md`, `jenkins/multibranch-local.xml`, `infra/nginx-webhook.conf` | `main` e `PR-1` descobertas no GitHub; quatro builds remotos verdes, webhook HMAC com eventos `push`/`pull_request` HTTP 200, check Jenkins verde e proteção de `main` testada; [PR #1](https://github.com/DaviSouza78/carparts-jenkins-aula06/pull/1) aberta para revisão |
| E6 Métricas | `scripts/metrics.py`, `docs/E6-metricas.md` | 12 builds locais: 11 sucessos, mediana 5,1 s; um deploy demonstrativo real com lead time limite de 3 h 20 min 35 s; série DORA de 10 deploys ainda pendente |

A primeira execução local falhou porque a opção `timestamps()` exigia um plugin não instalado. A opção foi removida, e as onze execuções seguintes passaram. Depois, um job demonstrativo separado executou os stages Azure e terminou com sucesso no build #2. Esse job não representa um Multibranch com webhook; veja E5.

## Rodar localmente

Pré-requisito: Docker Desktop com Linux containers e Python 3 para o coletor. Na pasta do projeto, execute no PowerShell:

```powershell
./scripts/start-lab.ps1 -Rebuild
python ./scripts/lab_runs.py --count 10
python ./scripts/metrics.py ./evidence/live/builds.json
```

O script cria `.env` com senha aleatória, inicia Jenkins e Docker-in-Docker, obtém o segredo do agent e o conecta. `.env` e `.runtime/` são ignorados pelo Git. A interface fica em `http://127.0.0.1:8080/` e exige login `admin` com a senha de `.env`. O serviço não é publicado em uma interface externa. Faça backup do volume `jenkins-data` antes de atualizar o controller; teste nova versão LTS e plugins em cópia antes de aplicar no ambiente principal.

Para testar apenas a aplicação:

```powershell
docker build --target test -t carparts-test:local .
docker build --target production -t carparts-b2b-demo:local .
docker run --rm -p 127.0.0.1:3000:3000 carparts-b2b-demo:local
```

`GET http://127.0.0.1:3000/health` retorna `{"status":"ok",...}`. `POST /api/orders` com `{"part":"Filtro","quantity":2}` cria um pedido apenas em memória. É um protótipo de pipeline, sem dados reais do ERP.

## Habilitar Azure e GitHub

Leia `docs/E4-azure.md` e `docs/E5-github.md`. Antes de provisionar, confirme uma assinatura Azure autorizada, orçamento e a oferta de preços. `azure/provision.sh` cria recursos que podem gerar cobrança; revise nomes e permissões antes da execução. Importe o segredo do service principal para o cofre Jenkins e remova o arquivo local; nunca inclua credenciais em commits, parâmetros de build ou logs. A publicação no Jenkinsfile só roda na branch `main` com `ENABLE_AZURE_DEPLOY=true`. O gate de produção exige aprovação identificada e promove o mesmo digest validado em homologação.

O código está no [GitHub público](https://github.com/DaviSouza78/carparts-jenkins-aula06). A proteção de `main` exige PR. O ensaio remoto usou credencial limitada e um túnel HTTPS temporário que expôs apenas `/github-webhook/`; o proxy validou HMAC e o check Jenkins foi exigido com sucesso. Após o ensaio, a exigência do check foi desligada, o webhook desativado e o túnel removido; o token GitHub expira em 01/10/2026 conforme escolha do proprietário. Para operação contínua, substitua o túnel por uma URL da equipe e use uma integração de credencial permanente e controlada. `infra/nginx-webhook.conf` é o modelo de proxy que não expõe a interface Jenkins.

## Evidências e limites

- `evidence/live/builds.json`: histórico da API Jenkins; `console-N.txt`: saída de cada build de laboratório.
- `evidence/live/nodes.json`: executores do controller e agent; `test-report-12.json`: quatro testes, zero falhas; `build-artifact-12.json`: commit e imagem.
- `evidence/live/app-smoke.json`: API iniciada em contêiner e endpoints verificados localmente.
- `evidence/live/azure-deployment-summary.json`, `azure-health-*.json`, `azure-jenkins-build-2.log`: publicação real, aprovação, mesmo digest e smoke tests antes da limpeza.
- `evidence/live/azure-cleanup.json`: verificação da remoção dos recursos e da identidade temporária.
- `evidence/live/multibranch-local-*.log` e `multibranch-local-summary.json`: índice e builds das duas branches locais.
- `evidence/live/azure-prices-chile-2026-09-30.json`: leitura da API oficial de preços na região usada. É referência de planejamento, não fatura.

O material didático mais antigo (`Jenkins.pdf`) explica a automação e a ideia de pipeline, mas mostra fluxos Freestyle e Docker desatualizados. O PDF *Modern Jenkins Pipelines* sustenta pipeline como código, JCasC, controller/agents e integração Azure CLI. Para sintaxe e instalação atuais, confirme nas fontes oficiais: [Jenkins Docker](https://www.jenkins.io/doc/book/installing/docker/), [Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/), [JCasC](https://github.com/jenkinsci/configuration-as-code-plugin), [Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/), [cobrança Azure](https://learn.microsoft.com/en-us/azure/container-apps/billing).
