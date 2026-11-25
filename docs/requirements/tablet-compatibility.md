# Matriz de compatibilidade de mesas digitalizadoras e canetas

**Versão:** 0.1
**Data:** 2026-11-25
**Status:** Rascunho para aprovação
**Dono:** Product Owner

Documento vivo que sustenta o requisito [RNF-03.7](requirements-catalog.csv): o Rabisco deve funcionar com as mesas digitalizadoras e canetas das principais marcas.

## 1. O que "todas as mesas" significa
Não existe como testar todos os modelos. O compromisso é este:
1. **Suportar as APIs de entrada de cada sistema operacional**, e não um modelo específico. A mesa fala com o driver e o driver fala com o sistema; quem usa a API certa funciona com qualquer mesa cujo driver a implemente.
2. **Manter esta matriz** com os modelos realmente testados, o que funciona e o que não.
3. **Tratar como defeito** (issue `defect`) qualquer mesa de marca relevante que funcione em outro programa mas não no Rabisco.

## 2. APIs de entrada por sistema
| Sistema | API a suportar | Pressão, inclinação e rotação | Observação |
|---|---|---|---|
| Windows | Windows Ink (`WM_POINTER`) | Sim, quando o driver as expõe | Padrão atual dos drivers Wacom, Huion, XP-Pen e Gaomon |
| Windows (drivers antigos) | WinTab | Sim | Alguns drivers só entregam pressão completa por WinTab; avaliar no spike (b) |
| macOS | Eventos de tablet do `NSEvent` | Sim | Mesas conectadas por driver do fabricante |
| Linux | libinput / evdev (X11 e Wayland) | Depende do driver | Melhor esforço no R1 (RNF-03.1) |
| iPadOS | Apple Pencil (`UITouch`, coalescência e previsão) | Sim | R4 |
| Android | `MotionEvent` com `TOOL_TYPE_STYLUS` | Sim, conforme o aparelho | R4 |

## 3. O que se verifica em cada mesa
Teste manual, cada item com "ok", "parcial" ou "não":
1. **Pressão** responde de forma contínua, sem degraus visíveis (curva monotônica).
2. **Inclinação** (quando a mesa tem).
3. **Rotação da caneta** (quando a mesa tem).
4. **Borracha** na ponta traseira da caneta (quando existe).
5. **Botões da caneta** reconhecidos.
6. **Pairar** (a caneta sobre a superfície move o cursor sem tocar).
7. **Resolução e taxa de amostragem**: traços rápidos e curvos sem pontas serrilhadas.
8. **Latência** da entrada até a tela, no cenário do RNF-01.3.
9. **Mais de um monitor e escala de tela** (mesas com e sem tela).

## 4. Níveis de suporte
| Nível | Significado |
|---|---|
| **Verificado** | Todos os itens aplicáveis da seção 3 em "ok", testado por alguém da equipe |
| **Parcial** | Funciona, com limitação descrita na coluna de notas |
| **Não funciona** | Há defeito aberto (link da issue) |
| **Não testado** | Citado por usuários ou pela equipe, ainda sem teste |

## 5. Matriz
Cada pessoa da equipe acrescenta o próprio equipamento. Não registre número de série nem dado pessoal (o repositório é público).

| Marca e modelo | Tipo | Sistema e versão | Driver e versão | API usada | Nível | Notas e issue | Quem testou | Data |
|---|---|---|---|---|---|---|---|---|
| a preencher | a preencher | Windows 11 (10.0.26200) | a preencher | a definir no spike (b) | Não testado | Mesa da autora do projeto; marca, modelo e driver ainda não informados | maria-brito15 | 2026-11-25 |

## 6. Como manter
- Novo teste: acrescente uma linha ou atualize a existente, no mesmo PR, com a data.
- Mudança de driver ou de sistema que quebre algo: atualize o nível e abra a issue.
- Mudou a lista de APIs suportadas (seção 2)? Isso é decisão técnica: registre na ADR ou na spec do motor de entrada.
