# Painel Eleições 2026

Painel interativo dos resultados do 1º turno das Eleições 2026 (04/10/2026). Ele foi construído a partir das planilhas do Portal de Dados Abertos do TSE, normalizadas até a 3ª Forma Normal.

## Como abrir

Baixe `dashboard_eleicoes_2026.html` e abra com duplo clique em qualquer navegador atual. Os dados vão embutidos no arquivo, então não é preciso instalar nada nem estar conectado à internet.

## O que tem no painel

| Aba | Conteúdo |
|---|---|
| Resultados | Cargo, abrangência (Brasil → UF → município), indicadores de comparecimento, brancos e nulos, ranking de candidatos com a chapa, mais votado por UF |
| Candidaturas | As 20.989 candidaturas com filtros, gráficos e exportação em CSV |
| Consulta | Acesso às 10 tabelas do modelo 3FN e a visões com JOIN, com o SQL equivalente de cada consulta |
| Normalização & DER | Etapas 0FN → 1FN → 2FN → 3FN com os registros do enunciado e o Diagrama Entidade-Relacionamento |
| Como foi feito | Documentação completa do processo: fontes, ETL, validações, arquitetura, design e testes |

## Modelo relacional (3FN)

`REGIAO`, `UF`, `MUNICIPIO`, `CARGO`, `ELEICAO`, `PARTIDO`, `CANDIDATURA`, `COMPOSICAO_CHAPA`, `VOTACAO_CANDIDATO`, `RESULTADO_MUNICIPIO_CARGO`

## Estrutura

```
dashboard_eleicoes_2026.html   painel final (arquivo único)
scripts/
  etl.py          planilhas do TSE → tabelas 3FN (dados.json), com validações
  build.py        embute dados.json no template e gera o HTML
  template.html   código do painel (HTML, CSS e JavaScript)
  dados.json      banco normalizado gerado pelo ETL
```

## Como gerar o painel de novo

Requer Python 3, sem bibliotecas externas.

```bash
cd scripts
python -I etl.py detalhe_votacao.csv lista_candidatos_2026.csv pasta_json_votos dados.json
python -I build.py template.html dados.json ../dashboard_eleicoes_2026.html
```

## Fontes

- `detalhe_votacao.csv` e `lista_candidatos_2026.csv`: Portal de Dados Abertos do TSE
- Votos por candidato: arquivos JSON públicos de resultados do TSE, por UF

Painel independente, sem vínculo institucional com o TSE.
