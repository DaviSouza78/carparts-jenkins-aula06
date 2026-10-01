# E1 · Arquitetura Carparts

```mermaid
flowchart LR
  DEV[4 desenvolvedores\n2 Windows 11 + WSL 2\n2 Ubuntu 24.04] -->|push / PR| GH[GitHub público]
  GH -->|HTTPS 443 /github-webhook/\nHMAC e proxy apenas para webhook| PROXY[Proxy reverso na rede local]
  PROXY -->|HTTP 8080 interno| CTRL[Jenkins LTS 2.568.3\ncontroller em Docker on-premises\n0 executores, JENKINS_HOME em volume]
  CTRL -->|WebSocket HTTPS interno\nsem porta inbound 50000| LINUX[Agent linux-docker\nUbuntu/container, 2 executores\nDocker TLS 2376 em rede interna]
  CTRL -.->|futuro: build .NET| WIN[Agent windows-dotnet\nWindows 11, 1 executor\nsem acesso ao JENKINS_HOME]
  LINUX -->|push por digest HTTPS 443| ACR[Azure Container Registry Basic]
  LINUX -->|Azure CLI HTTPS 443| HML[Container App homologação]
  LINUX -->|após input registrado\nmesmo digest| PRD[Container App produção]
  ACR -->|AcrPull com identidade gerenciada| HML
  ACR -->|AcrPull com identidade gerenciada| PRD
```

**Decisão.** O controller fica no ambiente local porque a diretoria exige Jenkins autogerenciado e dados do ERP on-premises. A porta 8080 está publicada somente em `127.0.0.1` no laboratório; em uso de equipe, o acesso à interface deve ocorrer por VPN/proxy HTTPS com autenticação. O endpoint de webhook precisa de proxy que exponha somente `/github-webhook/` e valide o segredo HMAC. O nó interno tem zero executores; builds ficam no agent Linux. O agent Windows fica reservado para um módulo .NET futuro e não é necessário para a API Node.js demonstrativa.

| Cenário | Vantagem | Risco e custo |
|---|---|---|
| Controller local em Docker (escolhido) | ERP e histórico permanecem locais; sem VM de Jenkins na nuvem; recriação por Dockerfile, plugins e JCasC | Exige backup do volume, atualizações e VPN/proxy seguros; eletricidade e operação locais não entram no teto Azure |
| Controller em VM Azure | Acesso e backup centralizados | Aumenta custo recorrente, exige túnel para ERP e eleva superfície de rede |
| Controller em AKS | Agents elásticos para muitos times | Complexidade e custo de cluster incompatíveis com quatro desenvolvedores e US$ 150/mês |

**Capacidade.** Um agent Linux com dois executores permite duas tarefas simultâneas. Para builds com Docker, aumentar paralelismo só após medir CPU/memória. Agent e daemon Docker compartilham uma rede Docker privada; a API do daemon usa TLS em 2376 e não é publicada no host. O segredo do agent fica fora do Git. O volume `jenkins-data` precisa de backup criptografado e retenção; a política do Jenkins descarta builds antigos.

**Evidência:** `compose.yaml`, `jenkins/controller/casc.yaml`, `evidence/live/` com logs e consulta da API de nós após execução. Fonte: [Jenkins Docker](https://www.jenkins.io/doc/book/installing/docker/), [JCasC](https://github.com/jenkinsci/configuration-as-code-plugin).

