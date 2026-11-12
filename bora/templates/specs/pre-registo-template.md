# Pré-registo-lite: <título da mudança>

- **Data:** <AAAA-MM-DD>
- **Autor:** <quem propõe>
- **Estado:** proposto | em curso | veredicto emitido

> Pré-registo-lite: 5 secções, um ficheiro, sem burocracia. A régua (secção 3) é assinada
> **ANTES** de tocar no código. O veredicto (secção 5) preenche-se DEPOIS, **no mesmo ficheiro**.

## 1. Motivação medida (com referências)

<porque é que isto precisa de mudar — números medidos com data, links para medições em
`medicoes.jsonl`, logs, profiles. Sem motivação medida não há pré-registo.>

## 2. A mudança + o que fica byte-idêntico

- **Muda:** <o que se altera, com ficheiros/funções>
- **Fica byte-idêntico:** <o que NÃO pode mudar — ficheiros, comportamentos, APIs. Esta lista é o escudo contra scope creep.>

## 3. Régua passa/falha (assinada ANTES) + critérios de kill

- **Régua:** <métrica objectiva e limiar: "passa se X ≥ Y", "falha se …">
- **Assinada em:** <data/hora em que a régua foi fixada — antes da implementação>
- **Kill (reverter sem discussão) se:** <condições de abandono: regressão >N%, complexidade +M ficheiros, prazo estourado, …>

## 4. Previsões

1. <previsão concreta e falsificável, com probabilidade se fizer sentido>
2. <previsão>

## 5. Veredicto (preenchido DEPOIS, neste ficheiro)

- **Resultado medido:** <números, com data>
- **Régua:** passou | falhou
- **Previsões:** <acertadas/falhadas, uma a uma>
- **Decisão:** fica | revertido | iterar
- **Registado em `medicoes.jsonl`:** id <n>
