# =============================================================================
# Construção da ABT
# ABT - Analytical Base Table
# =============================================================================
#
# Sumário
# 
# 1. Importação da bibliotecas
# 2. Criação e iniciação de uma sessão PySpark
# 3. Criação do dataset a partir da leitura do arquivo *.csv
# 4. Análise dos dados
#   4.1. Criação da view temporária
#   4.2. Qualidade dos dados
# 5. Construção da ABT
#   5.1. Criação de novas variáveis
# 6. Salvando a ABT em formato parquet
#
# =============================================================================

# =============================================================================
# 1. Importação de bibliotecas
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType
from pathlib import Path

import os

# =============================================================================
# 2. Criação e iniciação de uma sessão PySpark
# =============================================================================

# Nome da aplicação Spark
APP_NAME = 'ETL - ABT Churn Clientes de Banco'

# Objeto SparkSession com configuração para execução local
spark = SparkSession.builder \
    .appName(APP_NAME) \
    .config('spark.driver.memory', '2g') \
    .config('spark.executor.memory', '2g') \
    .config('spark.master', 'local[*]') \
    .getOrCreate()

# Definindo o nível de log para ERROR para reduzir a verbosidade dos logs
spark.sparkContext.setLogLevel('ERROR')

# Retornando o objeto SparkSession
spark

# =============================================================================
# 3. Criação do dataset a partir da leitura do arquivo *.csv
# =============================================================================

def find_project_root(start: Path, marker: str = 'data'):
    '''
    Localiza dinamicamente a raiz do projeto a partir de um diretório inicial.

    :param start: Path
        Diretório inicial para iniciar a busca (ex: Path.cwd()).
    :param marker: str (default='data')
        Nome da pasta que identifica a raiz do projeto.

    :return: Path
        Caminho da raiz do projeto.
    '''    
    for parent in [start] + list(start.parents):
        if (parent / marker).exists():
            return parent
    raise FileNotFoundError('Raiz do projeto não encontrada.')

# Definindo o caminho para os dados de entrada
BASE_DIR = find_project_root(Path.cwd())
DATA_PATH = BASE_DIR / 'data' / 'raw' / 'Churn_Modelling.csv'

if not DATA_PATH.exists():
    raise FileNotFoundError(f'Arquivo não encontrado: {DATA_PATH}')

# Lê o cabeçalho do arquivo CSV para obter os nomes das colunas
temp_df = spark.read.options(header=True, inferSchema=True).csv(str(DATA_PATH)).limit(1)

# Gerando o schema com base no DataFrame temporário
fields = []
for field in temp_df.schema:
    fields.append(field)
schema = StructType(fields)

# Criando o DataFrame final com o schema definido
df_churn = (
    spark.read
        .option('header', True)
        .option('quote', '"')
        .option('escape', '"')
        .option('multiline', True)
        .option('mode', 'PERMISSIVE')
        .schema(schema)
        .csv(str(DATA_PATH))
)

# Exibir o esquema do DataFrame para verificar os tipos de dados
df_churn.printSchema()

# =============================================================================
# 4. Análise dos dados
# =============================================================================

# -----------------------------------------------------------------------------
# 4.1. Criação da view temporária
# -----------------------------------------------------------------------------

# Criação da view temporária para consultas SQL
df_churn.createOrReplaceTempView('vw_churn_original')

# Exibir as primeiras linhas do DataFrame para verificar os dados
df_churn.show(10, truncate=False)

# -----------------------------------------------------------------------------
# 4.2. Qualidade dos dados
# -----------------------------------------------------------------------------

def run_data_quality_checks(
    df,
    df_name: str | None = None,
    not_null_columns: list[str] | None = None,
    numeric_rules: dict[str, str] | None = None,
    date_rules: dict[str, str] | None = None,
    fail_on_error: bool = False
):
    '''
    Executa verificações de qualidade de dados em um DataFrame Spark.

    Realiza checagens de:
    - Volumetria (total de registros e colunas)
    - Colunas que não devem conter valores nulos
    - Regras aplicadas a colunas numéricas
    - Consistência cronológica entre colunas de data

    :param df: pyspark.sql.DataFrame
        DataFrame Spark a ser validado.
    :param df_name: str (default=None)
        Nome descritivo do DataFrame para exibição nos logs.
    :param not_null_columns: list[str] (default=None)
        Lista de colunas que não podem conter valores nulos.
    :param numeric_rules: dict[str, str] (default=None)
        Dicionário com regras para colunas numéricas.
    :param date_rules: dict[str, str] (default=None)
        Dicionário com pares de colunas de data para validação
        de consistência cronológica.
    :param fail_on_error: bool (default=False)
        Se True, interrompe a execução ao encontrar a primeira
        violação de regra, lançando exceção.

    :return: None
        Apenas imprime o resultado das validações no console.
    '''     
    total_records = df.count()
    df_label = df_name if df_name else 'DataFrame'

    # -------------------------------------------------------
    # VOLUMETRIA
    # -------------------------------------------------------
    print(f'\n🔷 Volumetria do \033[3m{df_label}\033[0m:\n')
    print(f'Total de registros: {total_records}')
    print(f'Total de colunas:   {len(df.columns)}')

    # -------------------------------------------------------
    # REGRAS PARA COLUNAS NÃO NULAS
    # -------------------------------------------------------
    if not_null_columns:
        print(f'\n🔷 Checagem de colunas que não devem conter valores nulos:\n')  
        exprs = [
            F.sum(F.when(F.col(c).isNull(), 1).otherwise(0)).alias(c)
            for c in not_null_columns
        ]
        result = df.agg(*exprs).collect()[0]
        violations = 0
        for c in not_null_columns:
            null_count = result[c]
            if null_count > 0:
                print(f'  ❌ Coluna "{c}": {null_count} nulos encontrados!')
                violations += 1
                if fail_on_error:
                    raise ValueError(f'Regra violada: "{c}" não pode ser nula.')
        if violations == 0:
            print('  🟢 Nenhuma violação de nulidade encontrada.')  

    # -------------------------------------------------------
    # REGRAS PARA COLUNAS NUMÉRICAS
    # -------------------------------------------------------
    if numeric_rules:
        print(f'\n🔷 Checagem de regras para colunas numéricas:\n')
        exprs = [
            F.sum(F.when(F.expr(f'{c} {rule}'), 1).otherwise(0)).alias(f'{c}_rule_{i}')
            for i, (c, rule) in enumerate(numeric_rules.items())
        ]
        result = df.agg(*exprs).collect()[0]
        violations = 0
        for i, (c, rule) in enumerate(numeric_rules.items()):
            invalid_count = result[f'{c}_rule_{i}']
            if invalid_count > 0:
                print(f'  ❌ Coluna "{c}": {invalid_count} registros violam a regra "{rule}"')
                violations += 1
                if fail_on_error:
                    raise ValueError(f'Regra numérica violada em "{c}": {rule}')
        if violations == 0:
            print(f'  🟢 Todas as regras numéricas foram atendidas.')

    # -------------------------------------------------------
    # REGRAS PARA COLUNAS DE DATA
    # -------------------------------------------------------
    if date_rules:
        print(f'\n🔷 Checagem de regras para colunas de data:\n')
        exprs = [
            F.sum(F.when(F.col(end_date) < F.col(start_date), 1).otherwise(0)).alias(f"date_check_{i}")
            for i, (end_date, start_date) in enumerate(date_rules.items())
        ]
        result = df.agg(*exprs).collect()[0]
        violations = 0
        for i, (end_date, start_date) in enumerate(date_rules.items()):
            invalid_count = result[f'date_check_{i}']
            if invalid_count > 0:
                print(f'  ❌ Inconsistência: "{end_date}" é menor que "{start_date}" em {invalid_count} casos.')
                violations += 1
                if fail_on_error:
                    raise ValueError(f'Violação de cronologia entre {end_date} e {start_date}')
        if violations == 0:
            print(f'  🟢 Consistência de datas validada.')

    print(f'\n✅ Data quality checks concluídos para o \033[3m{df_label}\033[0m.\n')

# Executando as checagens de qualidade de dados
run_data_quality_checks(
    df_churn,
    df_name='Churn Modelling',
    not_null_columns=['RowNumber', 'CustomerId', 'Surname'],
    numeric_rules={
        'CreditScore': '<= 0',
        'Age': '<= 0',
        'Tenure': '< 0',
        'Balance': '< 0',
        'NumOfProducts': '< 0',
        'EstimatedSalary': '<= 0'
    },
)

# =============================================================================
# 5. Construção da ABT
# =============================================================================

# -----------------------------------------------------------------------------
# 5.1. Criação de novas variáveis
# -----------------------------------------------------------------------------

# Criando uma nova view com os dados limpos e ordenados por CustomerId
spark.sql('''
CREATE OR REPLACE TEMP VIEW vw_churn AS
SELECT
    CustomerId,
    Surname,
    CreditScore,
    Geography,
    Gender,
    Age,
    Tenure,
    Balance,
    NumOfProducts,
    HasCrCard,
    IsActiveMember,
    EstimatedSalary,
    Exited
FROM vw_churn_original
ORDER BY CustomerId ASC
''')

spark.table('vw_churn').show(10, truncate=False)

# Consulta SQL com transformações e análises adicionais
spark.sql('''
SELECT
      CustomerId,
      CASE 
            WHEN Age < 30 THEN 'Young'
            WHEN Age BETWEEN 30 AND 50 THEN 'Adult'
            ELSE 'Senior'
      END AS age_bucket,
      CASE 
            WHEN Tenure <= 3 THEN 'New customer'
            WHEN Tenure BETWEEN 4 AND 7 THEN 'Mid tenure'
            ELSE 'long_term'
      END AS tenure_bucket,
      CASE 
            WHEN EstimatedSalary > 0 
            THEN Balance / EstimatedSalary
      END AS balance_to_salary_ratio,
      NumOfProducts / CASE WHEN Tenure > 0 THEN Tenure END AS products_per_tenure,
      CASE WHEN CreditScore >= 721 THEN 1 ELSE 0 END AS is_high_credit_score,
      CASE 
            WHEN Age > 60 AND Tenure < 2 THEN 1 ELSE 0
      END AS is_senior_new_customer,
      AVG(EstimatedSalary) OVER(PARTITION BY Geography) AS avg_salary_by_geography,
      COUNT(*) OVER(PARTITION BY Geography) AS customer_count_by_geography,
      CASE WHEN balance = 0 THEN 1 ELSE 0 END AS is_zero_balance,  
      CASE WHEN NumOfProducts > 1 
          THEN 1 ELSE 0 END AS is_multi_product_customer,
      CASE WHEN IsActiveMember == 1 AND HasCrCard == 1 
          THEN 1 ELSE 0 END AS is_active_with_card
FROM vw_churn
''').show(10, truncate=False)

# Criando uma nova view com as transformações e análises adicionais
spark.sql('''
CREATE OR REPLACE TEMP VIEW vw_churn_enriched AS
SELECT
      CustomerId,
      CreditScore,
      Geography,
      Gender,
      Age,
      Tenure,
      Balance,
      NumOfProducts,
      HasCrCard,
      IsActiveMember,
      EstimatedSalary,
          
      CASE 
            WHEN Age < 30 THEN 'Young'
            WHEN Age BETWEEN 30 AND 50 THEN 'Adult'
            ELSE 'Senior'
      END AS age_bucket,
      CASE 
            WHEN Tenure <= 3 THEN 'New customer'
            WHEN Tenure BETWEEN 4 AND 7 THEN 'Mid tenure'
            ELSE 'long_term'
      END AS tenure_bucket,
      CASE 
            WHEN EstimatedSalary > 0 
            THEN Balance / EstimatedSalary
      END AS balance_to_salary_ratio,
      NumOfProducts / CASE WHEN Tenure > 0 THEN Tenure END AS products_per_tenure,
      CASE WHEN CreditScore >= 721 THEN 1 ELSE 0 END AS is_high_credit_score,
      CASE 
            WHEN Age > 60 AND Tenure < 2 THEN 1 ELSE 0
      END AS is_senior_new_customer,
      AVG(EstimatedSalary) OVER(PARTITION BY Geography) AS avg_salary_by_geography,
      COUNT(*) OVER(PARTITION BY Geography) AS customer_count_by_geography,
      CASE WHEN balance = 0 THEN 1 ELSE 0 END AS is_zero_balance,  
      CASE WHEN NumOfProducts > 1 
          THEN 1 ELSE 0 END AS is_multi_product_customer,
      CASE WHEN IsActiveMember == 1 AND HasCrCard == 1 
          THEN 1 ELSE 0 END AS is_active_with_card,
          
      Exited,
            
      CURRENT_DATE() AS processing_date
FROM vw_churn
ORDER BY CustomerId ASC
''')

spark.table('vw_churn_enriched').show(10, truncate=False)

# -----------------------------------------------------------------------------
# 5.2. Qualidade dos dados
# -----------------------------------------------------------------------------

# Carregar a tabela enriquecida em um DataFrame
abt_churn = spark.table('vw_churn_enriched')

# Executando as checagens de qualidade de dados
run_data_quality_checks(
    abt_churn,
    df_name='ABT Churn Modelling',
    not_null_columns=['CustomerId'],
    numeric_rules={
        'CreditScore': '<= 0',
        'Age': '<= 0',
        'Tenure': '< 0',
        'Balance': '< 0',
        'NumOfProducts': '< 0',
        'EstimatedSalary': '<= 0',
    },
)

# =============================================================================
# 6. Salvando a ABT em formato parquet
# =============================================================================

# Definindo o caminho onde os dados processados serão salvos
BASE_DIR = find_project_root(Path.cwd())
DATA_PATH = BASE_DIR / 'data' / 'processed' 

# Verifica se o diretório ABT já existe
if os.path.exists(DATA_PATH):

    # Exportar para Parquet
    abt_churn.write \
        .mode('overwrite') \
        .partitionBy('processing_date') \
        .option('compression', 'snappy') \
        .parquet(str(DATA_PATH))
    
    # Valida a quantidade de linhas lidas do Parquet
    read_abt_churn = spark.read.parquet(str(DATA_PATH))
    print(f'\nA ABT parquet tem {read_abt_churn.count()} linhas.')
else:
    print(f'\nOcorreu um erro: o diretório "{DATA_PATH}" não existe!')
