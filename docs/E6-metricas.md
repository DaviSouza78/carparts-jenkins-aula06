# E6 · Métricas e plano de melhoria

## Definições e coleta

O histórico Jenkins fornece início, duração, resultado e commit de cada build. `scripts/metrics.py` calcula duração e taxa de êxito a partir de um JSON exportado da API Jenkins. A primeira execução detectou uma opção de plugin ausente; após a correção, as execuções **2–12 foram onze sucessos consecutivos**. A amostra final de 12 builds locais teve 11 sucessos (91,7%) e mediana de 5,1 segundos. Consulte `evidence/live/builds.json`; esses builds medem a saúde de CI, não implantações Azure.

Para DORA em produção, acrescente `deployments.csv` com `commit_at_utc`, `deployed_at_utc`, `environment`, `status`, `incident`. **Lead time** é a diferença commit→produção de cada mudança; **frequência** é o número de implantações em produção por semana; **taxa de falha** é o percentual de implantações que exigiram intervenção imediata. Houve **uma publicação demonstrativa real** no Azure, no build `carparts-azure-demo #2`: commit de 30/09/2026 22:11:23 UTC, build concluído em 01/10/2026 01:31:58 UTC. Usando o fim do build como limite superior do deploy, o lead time da demonstração foi **até 3 h 20 min 35 s**. O resultado foi sucesso, sem incidente registrado. Uma amostra de um deploy não estima frequência sustentada nem taxa de falha confiável; as dez execuções exigidas para esses indicadores ainda faltam. A linha de base fornecida no enunciado é 11 dias, sem amostra bruta histórica. Meta: mediana ≤2 dias em oito semanas; publicar pelo menos semanalmente sem elevar falhas.

## Ações em oito semanas

| Prazo | Mudança | Medida de aceitação |
|---|---|---|
| Semanas 1–2 | Automatizar lint, testes e build por PR; tornar `main` protegida | Check verde obrigatório; 10 builds com resultado e duração registrados |
| Semanas 3–4 | Publicar imagem por digest e homologar com smoke test | Cada commit rastreável a uma imagem e revisão de homologação |
| Semanas 5–6 | Gate de aprovação e promoção do mesmo digest | Registro do aprovador em todas as publicações; zero recompilações |
| Semanas 7–8 | Medir DORA, corrigir gargalos e ensaiar rollback | Mediana commit→produção ≤2 dias; taxa de falha acompanhada por incidente |

## Orçamento Azure

Escolha: controller local, ACR Basic, Container Apps em consumo e um ambiente compartilhado. A assinatura estudantil permitiu **Chile Central**; o ensaio usou homologação e produção com escala a zero. Para planejar um mês de operação, adoto a hipótese conservadora de produção com uma réplica ativa 24 h/dia por 30 dias (0,25 vCPU/0,5 GiB), homologação com carga desprezível. A consulta à [API oficial de preços Azure](https://prices.azure.com/api/retail/prices) para Chile Central em 30/09/2026 retornou US$ 0,1666/dia para ACR Basic, US$ 0,000034 por vCPU-segundo ativo e US$ 0,000004 por GiB-segundo ativo; a resposta está em `evidence/live/azure-prices-chile-2026-09-30.json`. Considerando a franquia mensal de 180.000 vCPU-segundos e 360.000 GiB-segundos, a estimativa é ACR US$ 5,00 + CPU US$ 15,91 + memória US$ 3,74 = **US$ 24,65/mês**. Com US$ 10 para logs/egress, US$ 5 para armazenamento extra e US$ 30 de contingência, o planejamento é **US$ 69,65/mês**, abaixo do limite didático de US$ 150. A franquia é compartilhada pela assinatura e pode já estar consumida; preços, câmbio, tráfego e recursos adicionais podem alterar o total. Valide a oferta real na [calculadora oficial](https://azure.microsoft.com/en-us/pricing/calculator/) e configure alertas de custo.

**Estado da evidência:** 12 builds locais de CI e uma publicação demonstrativa real na Azure. Os dados não constituem dez implantações em produção nem permitem uma taxa de falha DORA representativa. Fonte: [cobrança de Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/billing).

