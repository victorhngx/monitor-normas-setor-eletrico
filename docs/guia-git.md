# Guia de Git/GitHub (em construção)

Glossário em linguagem simples. Ampliar conforme os conceitos aparecem no projeto.

| Termo | O que é | Analogia |
|---|---|---|
| Repositório (repo) | Pasta do projeto com todo o histórico de mudanças | Pasta com "controle de versões" embutido |
| Commit | Um "salvamento" com descrição do que mudou | Versão de um documento com comentário |
| Branch | Linha de trabalho paralela, sem mexer no principal | Cópia de rascunho |
| main | Branch principal, a versão "oficial" | Documento aprovado |
| Issue | Registro de uma tarefa, ideia ou problema | Chamado / ticket |
| Pull Request (PR) | Pedido para levar as mudanças de um branch para o main, com revisão e checks | Pedido de aprovação de minuta |
| Merge | Juntar o branch aprovado ao main | Incorporar a minuta aprovada |
| Push | Enviar os commits do computador para o GitHub | Sincronizar com a nuvem |
| Pull | Trazer para o computador o que mudou no GitHub | Baixar a versão mais recente |
| Clone | Cópia do repo no seu computador | Baixar a pasta sincronizada |
| Checks / CI | Verificações automáticas rodadas em cada PR (testes, privacidade) | Revisão automática antes da assinatura |
| GitHub Actions | Robô do GitHub que executa tarefas (checks, monitoramento diário) | Rotina agendada |
| GitHub Pages | Site simples publicado a partir do repo | Página da ferramenta |
| .gitignore | Lista de arquivos que o Git deve ignorar (nunca enviar) | Lista de "não arquivar" |
| GitHub Desktop | Programa visual para ver/sincronizar o repo no computador | — |

## Fluxo de trabalho do projeto
Issue → branch → commits → push → PR → checks passam → merge no main.
