## Descrição

Descreva claramente o que este PR resolve. Inclua contexto, o problema e como a solução arquitetural foi implementada.

## Relacionado a

- Issue: # (se aplicável)
- ADR: # (se aplicável)

## Tipo de mudança

- [ ] 🐛 Bug fix (mudança non-breaking que corrige um problema)
- [ ] ✨ Nova feature (mudança non-breaking que adiciona valor)
- [ ] 💥 Breaking change (fix ou feature que quebra retrocompatibilidade)
- [ ] 📝 Documentação (atualização de ADRs, arquitetura ou README)
- [ ] 🚀 Performance (melhoria de p95, otimização de queries, etc)

## Checklist Czanix (Top 0.01%)

- [ ] **Result Pattern:** O código não usa exceções (`try/catch/throw`) para fluxo de negócio.
- [ ] **Clean Architecture:** As regras de domínio não possuem dependências de infraestrutura, banco ou frameworks.
- [ ] **Banco de Dados:** Quaisquer novas entidades possuem `deleted_at` (soft delete) e constraints no banco (não só no código).
- [ ] **Performance:** Novas queries possuem índices filtrados cobrindo os campos de busca.
- [ ] **Testes:** Foram adicionados testes cobrindo o caminho feliz e os erros de domínio.
- [ ] **Linter & CI:** O código passa em todas as validações automáticas do pipeline.

## Evidências

*(Se houver impacto visual, adicione screenshots. Se for backend, adicione log de sucesso do k6 ou Jaeger).*
