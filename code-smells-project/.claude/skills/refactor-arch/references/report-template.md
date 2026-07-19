# Template do Relatório de Auditoria (Fase 2)

O relatório gerado na Fase 2 deve seguir **exatamente** esta estrutura (em Markdown). Substitua os
campos entre `<>`.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do projeto>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<N> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERIDADE>] <Nome do Anti-Pattern>
File: <arquivo>:<linha ou intervalo de linhas>
Description: <o que foi encontrado, de forma específica e verificável>
Impact: <consequência prática — o que quebra, o que fica difícil de manter/testar/proteger>
Recommendation: <ação concreta que será executada na Fase 3>

### [<SEVERIDADE>] <Nome do Anti-Pattern>
File: <arquivo>:<linha ou intervalo de linhas>
Description: ...
Impact: ...
Recommendation: ...

<... um bloco "### [SEVERIDADE] ..." por finding, ordenados CRITICAL → HIGH → MEDIUM → LOW ...>

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Regras de preenchimento

- **Files/lines of code**: conte apenas arquivos de código-fonte da aplicação (ver
  `project-analysis.md`, seção 6).
- **File**: sempre arquivo + linha(s) exata(s). Nunca "em algum lugar do models.py" — aponte a
  linha inicial (e final, se for um bloco) exata.
- **Description**: uma ou duas frases, técnica e específica. Evite generalidades ("código
  desorganizado") — diga o que exatamente está errado ("query monta SQL concatenando `id` recebido
  do path param diretamente na string").
- **Impact**: conecte o problema a uma consequência real (segurança, manutenção, teste,
  performance, corretude).
- **Recommendation**: deve ser executável — a Fase 3 vai literalmente aplicar essa recomendação
  usando o padrão correspondente do `refactoring-playbook.md`.
- **Ordenação**: sempre CRITICAL → HIGH → MEDIUM → LOW. Dentro da mesma severidade, ordene pela
  ordem em que aparecem no código (top-down, por arquivo).
- O relatório salvo em `reports/audit-<projeto>.md` deve ser idêntico ao impresso no terminal
  (sem o prompt de confirmação final, que é apenas interação de CLI).
