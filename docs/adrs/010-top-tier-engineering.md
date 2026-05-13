# ADR-010: O Top 0,01% — LLMOps, Agentes e Resiliência Extrema

## Status: Aceito
## Data: 2026-05-12

## Contexto

A maioria das empresas para na Clean Architecture, e os projetos de IA param no RAG (Retrieval-Augmented Generation) básico via LangChain. Para operar no topo absoluto (top 0,01%), onde OpenAI, Netflix e defesa cibernética operam, o sistema precisa antecipar falhas estruturais, otimizar custos de IA por token e executar fluxos autônomos com segurança criptográfica.

## Decisão

1. **Semantic Caching (Otimização Extrema de Custos):** Chamadas a LLMs (GPT-4, Claude 3) são lentas e caras. Implementamos Caching Semântico (via Redis ou pgvector). Se a intenção da pergunta do usuário for >95% similar a uma pergunta armazenada, retornamos do cache. Latência cai de 2500ms para 15ms. O custo marginal vai a zero.
2. **LLMOps e Telemetria de Alucinação (Langfuse / LangSmith):** OpenTelemetry não entende "alucinação". Toda chamada a LLM gera um trace em ferramentas de LLMOps capturando: tokens exatos usados, custo dinâmico em USD, versão do prompt e o RAG Triad (Context Relevance, Groundedness, Answer Relevance). O deploy é abortado se o índice de alucinação (Groundedness) cair.
3. **Orquestração de Agentes Determinísticos (Temporal.io / LangGraph):** Agentes autônomos (ReAct, Plan-and-Execute) são intrinsecamente não-determinísticos. Falhas no meio de um chain deixam o sistema inconsistente. Usamos orquestradores de estado durável. Se um Agente falhar no meio de uma compra de R$ 50 mil, a execução "pausa" e retoma do exato milissegundo em que travou.
4. **Chaos Engineering Constante:** Resiliência teórica é inútil. Injetamos falhas aleatórias no ambiente de staging (Chaos Mesh/Gremlin) — simulamos quedas na rede da AWS, latência artificial de 5s no PostgreSQL, ou timeout na OpenAI. Se os Circuit Breakers e Fallbacks não abrirem perfeitamente, o PR é reprovado na esteira CI.
5. **Supply Chain Security (SLSA Nível 3+ e SBOM):** Nenhuma imagem Docker vai para produção sem um SBOM (Software Bill of Materials) analisado contra CVEs zero-day e uma assinatura criptográfica (Cosign). Impede que um package NPM comprometido roube chaves da AWS. Segurança de grau militar.

## Consequências

- **Margem de lucro blindada:** Ao escalar produtos B2C baseados em IA, o Semantic Cache impede a famosa "falência por sucesso" onde a conta da OpenAI destrói a receita.
- **Auditoria de Compliance (Legal):** A telemetria de prompts permite auditoria exata. Se a IA recomendar algo ilegal, o time jurídico tem o "replay" do fluxo exato de pensamento que o agente tomou.
- **Paz de Espírito:** Um sistema testado com Chaos Engineering contínuo cura a si mesmo. O time de engenharia não é acordado às 3h da manhã.
