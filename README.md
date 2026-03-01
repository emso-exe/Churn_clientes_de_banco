# 🔎 Análise e classificação de Churn de clientes de banco 😒

Projeto de Análise Exploratória de Dados (EDA) e Machine Learning para identificação de clientes com potencial de encerrar suas contas em uma instituição bancária.
O conjunto de dados está disponível publicamente na plataforma [Kaggle](https://www.kaggle.com/datasets/shrutimechlearn/churn-modelling).

## 🚨 Contexto do problema

A retenção de clientes é um dos principais desafios estratégicos no setor bancário. A saída de clientes (churn) impacta diretamente:

- Receita recorrente;
- Custos de aquisição de novos clientes;
- Imagem da marca;
- Competitividade no mercado.

Com base em dados históricos de clientes que permaneceram ou encerraram suas contas, este projeto propõe o desenvolvimento de um modelo preditivo capaz de identificar clientes com maior probabilidade de evasão.
Essa abordagem permite que a instituição atue de forma preventiva, adotando estratégias direcionadas de retenção.

## 💼 Demanda do negócio

- Realizar análise exploratória dos dados para identificar padrões associados ao churn.
- Mapear variáveis com maior influência na saída de clientes.
- Desenvolver um modelo preditivo para classificação de churn.
- Avaliar o modelo considerando o desbalanceamento entre classes.
- Gerar insights que possam apoiar estratégias de retenção.

## 📊 Abordagem Analítica

O projeto segue uma estrutura baseada no framework CRISP-DM, contemplando:

1. Compreensão do negócio
2. Compreensão dos dados
3. Preparação dos dados
4. Modelagem
5. Avaliação
6. Interpretação de resultados
  
## 📓 Dicionário de dados

| Variável            | Descrição                                                |
| ------------------- | -------------------------------------------------------- |
| **RowNumber**       | Identificador sequencial da linha                        |
| **CustomerId**      | Identificador único do cliente                           |
| **Surname**         | Sobrenome do cliente                                     |
| **CreditScore**     | Pontuação de crédito                                     |
| **Geography**       | País de residência                                       |
| **Gender**          | Gênero do cliente                                        |
| **Age**             | Idade                                                    |
| **Tenure**          | Tempo (em anos) como cliente do banco                    |
| **Balance**         | Saldo bancário                                           |
| **NumOfProducts**   | Quantidade de produtos contratados                       |
| **HasCrCard**       | Indica se possui cartão de crédito (1 = Sim, 0 = Não)    |
| **IsActiveMember**  | Indica se é cliente ativo                                |
| **EstimatedSalary** | Salário estimado                                         |
| **Exited**          | Variável alvo (1 = Cliente saiu, 0 = Cliente permaneceu) |

## 💻 Tecnologias

- Python
    - Biblioteca GC
    - Biblioteca Pandas
    - Biblioteca Matplotlib
    - Biblioteca Seaborn
    - Biblioteca Numpy
    - Biblioteca Warnings
    - Biblioteca Tabulate
    - Biblioteca SciKit-learn
    - Biblioteca Imbalanced-learn
    - Biblioteca Pyspark
    - Biblioteca Pathlib

import os    

## 💳 Créditos

- [Estênio Mariano](https://github.com/emso-exe)

## 🔖 Licença

Licença MIT (MIT). Por favor leia o [arquivo da licença](LICENSE.md) para mais informações.