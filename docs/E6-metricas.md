# E6 · Métricas e plano de melhoria

## Definições e coleta

O histórico Jenkins fornece início, duração, resultado e commit de cada build. `scripts/metrics.py` calcula duração e taxa de êxito a partir de um JSON exportado da API Jenkins. A primeira execução detectou uma opção de plugin ausente; após a correção, as execuções **2–11 foram dez sucessos consecutivos**. Na primeira amostra de 11 builds, houve 10 sucessos (90,9%) e mediana de 5,1 segundos. Consulte `evidence/live/builds.json` para o histórico atualizado; esses builds medem a saúde de CI, não implantações Azure.

Para DORA em produção, acrescente `deployments.csv` com `commit_at_utc`, `deployed_at_utc`, `environment`, `status`, `incident`. **Lead time** é a diferença commit→produção de cada mudança; **frequência** é o número de implantações em produção por semana; **taxa de falha** é o percentual de implantações que exigiram intervenção imediata. Uma simples execução de teste não conta como deploy. A linha de base fornecida no enunciado é 11 dias, sem amostra bruta histórica. Meta: mediana ≤2 dias em oito semanas; publicar pelo menos semanalmente sem elevar falhas.

## Ações em oito semanas

| Prazo | Mudança | Medida de aceitação |
|---|---|---|
| Semanas 1–2 | Automatizar lint, testes e build por PR; tornar `main` protegida | Check verde obrigatório; 10 builds com resultado e duração registrados |
| Semanas 3–4 | Publicar imagem por digest e homologar com smoke test | Cada commit rastreável a uma imagem e revisão de homologação |
| Semanas 5–6 | Gate de aprovação e promoção do mesmo digest | Registro do aprovador em todas as publicações; zero recompilações |
| Semanas 7–8 | Medir DORA, corrigir gargalos e ensaiar rollback | Mediana commit→produção ≤2 dias; taxa de falha acompanhada por incidente |

## Orçamento Azure

Escolha: controller local, ACR Basic, Container Apps em consumo e um ambiente compartilhado. A hipótese inicial é homologação com escala a zero e produção pequena, 0,25 vCPU/0,5 GiB, uma réplica 24 h/dia por 30 dias. A consulta à [API oficial de preços Azure](https://prices.azure.com/api/retail/prices) para Brasil Sul em 30/09/2026 retornou US$ 0,1666/dia para ACR Basic, US$ 0,000024 por vCPU-segundo ativo e US$ 0,000003 por GiB-segundo ativo. Com a franquia de 180.000 vCPU-segundos e 360.000 GiB-segundos mensais disponível, a conta ilustrativa é ACR US$ 5,00 + CPU US$ 11,23 + memória US$ 2,81 = **US$ 19,04/mês**, sem tráfego relevante. Reservando US$ 10 para logs/egress, US$ 5 para armazenamento extra e US$ 30 de contingência, o planejamento fica em **US$ 64,04/mês**, abaixo de US$ 150. A franquia é compartilhada pela assinatura e pode já estar consumida. Valide a oferta real na [calculadora oficial](https://azure.microsoft.com/en-us/pricing/calculator/) antes de provisionar; crie alertas em 50%, 80% e 100%. Custos de rede, logs, pedidos e operações adicionais podem alterar o total.

**Estado da evidência:** os dez builds locais não demonstram lead time real nem frequência de produção. Esses indicadores permanecem pendentes até existir deploy Azure autorizado. Fonte: [cobrança de Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/billing).

