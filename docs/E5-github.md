# E5 · Multibranch, webhook e proteção de `main`

1. Publique este projeto em um repositório GitHub privado da equipe. Crie um GitHub App para o Jenkins com acesso somente a esse repositório e permissões mínimas de conteúdo/PR/status; armazene a credencial no cofre Jenkins. Evite token pessoal amplo.
2. Crie um item **Multibranch Pipeline** no Jenkins, fonte **GitHub**, proprietário/repositório, descoberta de branches e pull requests, `Jenkinsfile` na raiz. Confirme que o índice cria jobs para `main`, branch de recurso e PR.
3. Configure no GitHub um webhook `https://<domínio-da-equipe>/github-webhook/`, eventos *push* e *pull request*, tipo JSON e segredo HMAC. O exemplo `infra/nginx-webhook.conf` publica somente esse endpoint e encaminha ao Jenkins interno; a interface/API seguem acessíveis apenas por VPN/proxy autenticado. Configure a validação do segredo no plugin GitHub e confirme uma entrega de teste; não publique a porta 8080 diretamente.
4. No ruleset ou proteção da branch `main`, exija PR, um aprovador independente e o check do pipeline verde antes do merge. Bloqueie push direto e descarte aprovações antigas após novos commits. Execute um PR de exemplo e anexe print dos checks e da execução Multibranch.

**Estado da evidência:** configuração documentada; não há repositório GitHub da Carparts nem URL pública fornecidos nesta sessão, portanto webhook e check remoto não foram acionados. Fontes: [Jenkins Multibranch](https://www.jenkins.io/doc/book/pipeline/multibranch/), [GitHub webhooks](https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks), [regras de proteção](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).

