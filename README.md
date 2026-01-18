

<p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/logo.png" width="250" height="250">
</p>

# Previsão de churn com análise de sobrevivencia

## Este projeto tem o objetivo de identificar o momento em que ocorrerá o churn dos clientes para subsidiar as ações do time de retenção



# 1. Business Problem.

KKBOX é uma empresa de tecnologia e entretenimento musical originária de Taiwan criada em 2004/2005 em Taipei, Taiwan, sendo conhecida pelo seu serviço de streaming de música digital. KKBOX é uma plataforma de streaming de música legal, oferecendo milhões de faixas via aplicativo e web para smartphones, computadores e aparelhos conectados. A empresa possui mais de 10 milhões de usuários na Ásia e seu modelo de negócio é do tipo Freemium - usuários gratuitos com limitações e assinantes premium com acesso ilimitado. 

O time de Retenção da KKBOX identificou um aumento relevante no churn de clientes e precisa estruturar ações para conter essa tendência. Diante desse cenário, a equipe solicitou o apoio do time de Dados para desenvolver uma solução que permita identificar, com antecedência, quais clientes têm maior risco de churn e quando esse evento provavelmente ocorrerá.

O objetivo é possibilitar a criação de estratégias de retenção proativas, direcionadas aos clientes com maior probabilidade de cancelamento, permitindo que a empresa atue antes da perda de receita. Como os recursos de marketing e atendimento são limitados, a priorização correta dos clientes é essencial para maximizar o impacto das ações e otimizar o retorno sobre o investimento.

Por esse motivo, o time de marketing requisitou ao time de dados uma seleção de clientes elegiveis ao programa, usando técnicas avançadas de manipulação de dados.

# 2. Premissas de negócio.

1. O critério de "churn" é não haver nova assinatura válida de serviço dentro de 30 dias após o término da associação atual.
2. O resultado deverá ser entregue em uma apresentação com as dúvidas de negócio.
3. A solução deverá ser dashboard no streamlit para acompanhamento dos clientes com maior probabildiade de churn.

# 3. Objetivo.

1. Deve ser entregue a lista de clientes com maior probabilidade de churn e qual data provável de churn.
2. A lista de clientes com potencial de churn deverá contem os clientes com maior potencial de risco. Além disso, a lista deverá ser rankeada tendo como critério um balanço entre o valor pago pelo cliente e tempo até o churn sendo prioriazados aqueles com maior valor e tempo mais curto para o churn.

# 4. Análise Teórica do Problema: Churn & Survival Analysis

1. O Problema do Churn
O Churn Rate (Taxa de Rotatividade) mede a taxa de clientes que cancelam uma assinatura ou interrompem a relação comercial com uma empresa. Tradicionalmente, o churn é tratado como um problema de classificação binária (o cliente vai sair ou não?). No entanto, essa abordagem ignora uma variável crítica: o tempo.

Neste projeto, tratamos o churn não apenas como um evento, mas como um processo temporal, permitindo responder não só quem sairá, mas quando isso deve acontecer.

2. O que é Análise de Sobrevivência (Survival Analysis)?
A Análise de Sobrevivência é um conjunto de métodos estatísticos projetados para modelar o tempo até que um evento de interesse ocorra. Tais metodos são muito utilizados na medicina (para medir o tempo até a morte ou cura) e na engenharia (confiabilidade de peças).

- Conceitos Fundamentais:

   **Evento (Event): O Churn (cancelamento).

   ** Tempo (Tenure): O período em que o cliente permanece ativo.

   ** Censura (Censoring): Ocorre quando o evento não aconteceu até o final do período de coleta de dados (o cliente ainda é fiel). Ignorar clientes censurados enviesa o modelo; a Análise de Sobrevivência os utiliza para informar que "pelo menos até o dia X, esse cliente sobreviveu".


3. Pilares Estatísticos e Fórmulas

  A Função de Sobrevivência S(t) 

  Representa a probabilidade de um cliente "sobreviver" (não dar churn) além do tempo (t).

  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/funcao_sobrevivencia.png" width="250">
  </p>

  A Função de Risco (Hazard Function) λ
  
  Representa a taxa instantânea de ocorrência do evento (churn) no tempo (t), dado que o cliente sobreviveu até aquele momento. É o "risco imediato" de perda.

  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/Risco.png" width="250">
  </p>


# 5. Planejamento da solução.

**Step 01. Descrição dos dados:**

  - Checar os tipos de dados e verificar a necessidade de alteração.
  - Checar os NA e realizar e o replace caso necessário.
  - Relizar a descrição estatisticas dos dados númericos e avaliar distorções.

  -- Informações sobre os dados:

  | Feature | Descrição |
|----------------|:----------:|
| MSNO | ID de usuário |
| is_churn | Esta é a variável alvo (is_churn = 1, is_churn = 0) |
| payment_method_id | Método de pagamento |
| payment_plan_days | Duração do plano de associação em dias |
| plan_list_price| em Novo Dólar de Taiwan (NTD) |
| actual_amount_paid| Valor pago atualmente |
| is_auto_renew | Renovação automatica |
| transaction_date| Data da transação |
| membership_expire_date| Data de expiração da assinatura |
| is_cance| Se o usuário cancelou ou não a assinatura nesta transação. |
| city | Cidade do usuário |
| bd| Idade |
| gender | Genero |
| registered_via| método de registro |
| registration_init_time| Início na plataforma. Formato %Y%m%d |
| expiration_date | formatar , tomado como um snapshot no qual o member.csv é extraído. Não representa o comportamento real de churn. %Y%m%d |

**Step 02. Filtragem de Variáveis:**
 
  - Filtrar todas as colunas e dados que não irão contribuir para construção do projeto ou que sofre algum restrição de atualização. Não foi identificado a necessidade de realização de filtros.

**Step 02. Mudança de tipos de dados:**
 
  - Foi realizado a alteração dos campos de datas para o formato %Y%m%d.
  

**Step 03. Feature Engineering:**

  - O processo de feature engineering visa a criação de features a partir da combinação de features ou da mudança de formatos. Essas novas features podem ajudar a melhorar o resultado do modelo criando uma maior variabilidade dos dados. Segue o conjunto de features criadas:

    1. Days: Construção de features de tempo (dias) entre a data de inscrição até a data alvo (30 dias após a data de expiração da assinatura). Está feature será utilizada para calcular o tempo até o churn.
 

**Step 04. Exploração dos dados:**

  Nesta etapa foram realizados avaliações sobre a composição de cada grupo das covariaveis em relação a variavel churn.

  O percentual de churn na base gira em torno de 9%.

  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/3_proporcao_de_churn.png" width="250" height="250">
  </p>

 

  Existe uma concentração dos clientes na cidade 1 com 64,3% da base. Entretanto, além do grande volume de churn na cidade 1 que é esperado devido ter o maior volume de clientes, existe um grande volume de churn nas cidades 4 (6,9%), 5(10,0%),13 (11,9%) e 15 (6,1%).

  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/4_churn_city.png" width="800">
  </p>

  
  A maioria dos clientes tem a renovação automática (86,5%). Porém, a distribuição do volume de churn é maior no clientes que não tem renovação automatica (56,7%) o que demonstra a possibilidade de criar ações para adesão da renovação automatica.

  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/5_Auto_renewal.png" width="800">
  </p>


    - Apesar do metodo 33 ser dominante na base ele não repesenta o maior quantidade de churn. Tal posição é ocupada pelo metodo 38 com 38,4% dos churn. Outro metodo representativo é o 36 com participação de 9,8% dos churns.


  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/6_payment_method.png" width="800">
  </p>

   

    - Em relação ao valor pago pelos clientes na plataforma, a maioria está situada entre os intervalos de 0 até 266. Apesar do maior parte do churn acompanhar ficar situada no intervalo de 0 a 266 verificamos um percentual expressivo nos intervalos 400 a 555 com 6%, o intervalo 800 a 933,33 com 9,6% e o intervalo 1733 a 1866,66 com 8,7%.


  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/7_pay.png" width="800">
  </p>

 
**Step 05. Análise da curva de sobrevivência:**

  - A probabilidade de sobrevivência cai para 50% no momento 1539.

  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/8_curva_geral_sobrevivencia.png" width="600">
  </p>

  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/0_mediana_de_sobrevivencia.png" width="300">
  </p>

  Um ponto de destaque é em relação a mediana de churn do metodo de pagamento 25 que é de 38 dias.

  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/0_metodo_pay.png" width="300">
  </p>

 
**Step 06. Análise do impacto da covariaveis sobre o aumento do risco:**

  - Utilizamos o algoritmo Cox PH para verificar quais covariaveis mais influenciam no aumento do risco de churn e qual a intensidade. Um ponto de observação é que o Cox PH é um algoritmo estatístico que busca verificar ralações lineares.


  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/9_Table_Cox_PH.png" width="750">
  </p>


  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/12_impacto.png" width="700">
  </p>


  Na tabela do Cox, as principais colunas são o coef, exp(coef) e p. O coef sinalizar o tipo de impacto sobre o churn sendo que valores positivos aumentam o risco de churn e valores negativos reduzem o risco. O exp(coef) mostra a intensidade do impacto sendo valores maiores que 1 aumentam o risco (HR 1.20 significa que o risco é 20% maior para cada unidade da variável) e valores menores que 1 reduzem o risco de churn (HR de 0.80 significa que o risco é 20% menor). O valor de p-valor demonstra se o coeficiente tem significancia estatística e impacta o churn sendo que o valor da variavel tem que ser <0.05. O valor do C-index demonstra a perfomance do modelo sendo que valores menores que 0.5 representa um modelo ruim, valores entre 0.7 a 0.8 representam um modelo com boa capacidade preditiva e valores maiores que 0.8 demonstra um modelo com capacidade excelente.

  As features payment_method, is_auto_renew e actual_paid tem um impacto negativo e reduzem o risco de churn. O modelo apresenta um performance adequada com 0.78. A única variavel que não tem significancia estatística é a plan_list_price.

  Após a análise do impacto das variáveis é necessário realizar o teste de residuos Schoenfeld. Tal teste é importante para validar a proporcionalidade dos Riscos (Proportional Hazards Assumption). A premissa PH considera que as variáveis são constantes ao longo de todo o tempo.

  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/10_Teste_sch.png" width="600">
  </p>


  Com exceção das covariáveis payments_pan_days e a plan_list_price todas as outras violaram a premissa PH.

  A violação da premissa sugere que o impacto desses fatores no Churn não é estático. Por exemplo, o payment_method tem um peso diferente no risco de cancelamento nos primeiros meses de contrato em comparação com clientes antigos. Isso demonstra que o comportamento de churn na base de dados é dinâmico e evolui ao longo do ciclo de vida do cliente. Embora a premissa de PH não tenha sido estritamente atendida, o Modelo de Cox ainda é útil como uma ferramenta de inferência geral, fornecendo a direção do impacto (se aumenta ou diminui o risco) de cada variável.

**Step 07. Análise do impacto da covariaveis sobre o tempo de sobrevivência (AFT):**

Foi utilizado o algoritmo Weibull Aft para avaliar quais variaveis impactam na aceleração do churn e qual a intensidade dessa influência. Semelhante ao Cox, o Weibull Aft é um modelo focado na leitura de relações lineares.

  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/13_tabela_aft.png" width="750">
  </p>

Esta é a coluna mais importante. Ela indica a relação com o logaritmo do tempo.
  * Coeficiente Positivo ($> 0$): Significa que a variável aumenta o tempo de sobrevivência. O cliente demora mais para cancelar (o que é bom para o negócio).
  * Coeficiente Negativo ($< 0$): Significa que a variável diminui o tempo de sobrevivência. O cancelamento acontece mais rápido (o que é ruim).
  * Se exp(coef) = 1,20: A variável aumenta a duração em 20%.
  * Se exp(coef) = 0,80: A variável reduz a duração para 80% do original (ou seja, o cancelamento acontece 20% mais rápido).

* Nota 1: As covariáveis payments_pan_days, plan_list_price e registered_via aceleram o tempo de cancelamento. As demais o retardam.
* Nota 2: A covariável com maior impacto em atrasar o cancelamento é is_auto_renew com 3.11.
* Nota 3: Todas as covariáveis mostraram significância estatística.

**Step 07. Teste dos modelos parametricos:**

Inicialmente foram realizados testes apra avaliar os modelos parametricos e selecionar um modelo base que servirá de referência como valor mínimo de performance.


  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/15_modelos_parametricos.png" width="400">
  </p>


Entre as distribuições paramétricas avaliadas, o modelo Weibull apresentou o melhor ajuste aos dados de tempo até churn, superando substancialmente os modelos Log-normal e Log-logistic segundo os critérios de log-verossimilhança (maior / menos negativo melhor), AIC(menor melhor) e BIC (menor melhor).

**Step 08. Hyperparameter Fine-Tunning e teste dos modelos:**
    
Nesta etapa foi realizar o teste com os modelos e ajuste dos parametros com os modelos Weibull aft, XGBoost aft e XGBoost Cox. A principal metrica de avaliação foi a c_index. O XGboost Cox também foi treinado visando a realização da primeira etapa de ranqueamento por meio do score gerado pelo modelo.

**Step 09. Teste-validação:**

   -  Para o processo de teste-validação foi escolhido o modelo XGBoost (aft e cox). O XGBoost COx será utilizado para raquear os clientes por meio do score de risco e em seguida será verificado os dias de sobrevivência com o XGBoost aft.

  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/Teste_validacao.png" width="250">
  </p>


**Step 10. Modelo final:**

  O algoritmo Cox será utilizado para realizar o ranqueamento da base (risk_score) e o aft será usado para calcular o período do churn. Nesta etapa serão construídas as colunas:

  - risk_score: Crição do score de risco realizado pelo XGBoost Cox. Ele representa o risco de churn.
  - risk_percentile: Representa a criação dos percentis com base na coluna risck_score.
  - risk_group: Representa a estratificação dos percentis em classes e servirá como referencia de atuação para o time de retenção. Para realizar o calculo dos tempos de churn foi selecionado somente os grupos Alto, Muito alto e critico que representa 10,56% da base.

  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/Grupo_de_risk.png" width="300">
  </p>


  - expected_days_to_churn: É o tempo até o churn calculado pelo modelo aft.
  - expected_churn_date: Representa a data prevista para o churn.
  - priority_score: Prioridade de risco que é criada por meio da divisão do valor pago pelo cliente e tempo até o churn. Essa feature será utilizada como referencia de ação priorizando aqueles com maior score ( maior valor pago e mais próximo de churn)

   
**Step 11. Simulação de redução de perda :**

Nesta etapa, foi criado a tabela simulando a perda evitada caso a equipe de marketing consiga reter o número estimado em cada faixa. A coluna Cenário (Redução Churn %) representa o percentual de redução de churn e a coluna clientes atendidos representa o número de retenções para cada cenário. A coluna Valor Recuperado representa a perda evitada mensal e as colunas Rec_em_[i]_meses representam a a projeção do valor recuperado para cada período de meses.

  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/Tabela_perda_evitada.png" width="750">
  </p>


Obs.: Esta imagem representa a projeção de ganho considerando somente os grupos critico e muito alto.

**Step 12. Interpretação da features :**

Para este projeto, utilizamos o SHAP (SHapley Additive exPlanations) para garantir transparência e explicabilidade aos resultados do modelo de Churn. Enquanto modelos tradicionais nos dão uma visão geral da base, o SHAP nos permite entender a contribuição individual de cada variável para a projeção dos dias de sobrevivência.

  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/feature_importanece_bar.png" width="750">
  </p>

A herarquia das features na coordenda y representa o grau de importância sendo o registred_via a mais importante e a city a menos importante. Os valores apresentados na barras informam a contribuição para a estimação do aft.


**Step 13. Top 3 Data Insights:**

H1: Os clientes sem renovação automatica são mais propensos a ter churn

Verdade: Os clientes que não possuem renovação automatica representam cerca 56,7% dos churns. Esse insight possibilidade de criar ações direcionadas a adoção da renovação automatica pelos clientes, tal como desconto na mensalidade por um determinado período.


H2: Por representar a maior parte dos clientes, o metodo de pagamento 41 tem maior concentração de churn.

Falso: A concentração de churn está no metodo 38 (38,4%). Outros metodos com quantidade de churn expressiva são a 36 (9,8%) e a 40 (7,1%). O metodo 41 representa 24,6% da base.



H3: Nenhuma cidade chega a ter probilidade de 50% antes de 500 dias.

Falso: As cidades 25, 17, 20 e 8 term queda de 50% da probilidade de sobrevivencia, ou seja, chega a probilidade de 50% antes de 500 dias. Um ponto de atenção são as cidades 25 e 17 que chegam em 50% com, respectivamente, 38 e 118 dias. Tal informação destaca a necessidade de se realizar um estudo mais aprofundado sobre o habito de consumo dos usuários dessas regiões.


**Step 12. Entrega do dashboard no Streamlit:**

Segue o link dashboard com os clientes com potencial de churn no streamlit:


Link:

  <p align="center">
  <img src="https://raw.githubusercontent.com/Andre10DS/churn_analise_sobrevivencia/main/img/streamlit_b.gif" width="800">
  </p>


# 4. Conclusão

Neste projeto, foi desenvolvido um sistema completo de Análise de Sobrevivência para previsão de churn, cujo objetivo central foi estimar não apenas se um cliente irá churnar, mas quando esse evento tende a ocorrer, permitindo uma atuação proativa do negócio.

Para isso, foi adotada uma abordagem baseada em modelos de tempo até o evento (time-to-event), superando as limitações dos modelos tradicionais de classificação binária, que ignoram tanto a dimensão temporal quanto o problema de censura (clientes que ainda não churnaram no momento da observação).

Dois modelos de estado da arte foram utilizados:

  - XGBoost com função de risco proporcional (Cox)

  - XGBoost com modelo de tempo acelerado (AFT – Accelerated Failure Time)

Esses modelos permitiram capturar relações não lineares, interações complexas e efeitos heterogêneos entre as covariáveis, algo que modelos clássicos como Cox PH linear não conseguem representar adequadamente.



# 5. Próximo passos

  - Criar uma conexão com o CRM ou com base de dados da equipe de marketing para sinalizar as ações que estão sendo realizadas para cada cliente evitando a concentração de esforços em um mesmo cliente, mensurar o custo das ações e verificar quais ações estão gerando retorno.
  - Acrescentar um modelo previo de classficição para apontar aqueles que tem maior chance de churn e depois envia-los para os modelos Cox e aft.



