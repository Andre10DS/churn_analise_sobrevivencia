import streamlit as st
import pandas as pd
import numpy as np
import pickle
import shap
import os
import sys
import xgboost           as xgb
import matplotlib.pyplot as plt
import base64
from pathlib import Path
from datetime                       import datetime, timedelta
from lifelines                      import KaplanMeierFitter
from utils.simulator                import simular_reversao



st.set_page_config(page_title="Dashboard de Retenção - Churn Survival", layout="wide",initial_sidebar_state="expanded")


@st.cache_resource

def load_models():
    # Carregue seus modelos .pkl aqui
    with open('models/model_xgb.pkl', 'rb') as f:
        model_cox = pickle.load(f)
    with open('models/model_xgb_aft.pkl', 'rb') as f:
        model_aft = pickle.load(f)
    return model_cox, model_aft

def load_processing():
    
    with open('models/scaler_pay.pkl', 'rb') as f:
        scaler_pay = pickle.load(f)
    with open('models/scaler_ac.pkl', 'rb') as f:
        scaler_ac = pickle.load(f)
    with open('models/mm_reg.pkl', 'rb') as f:
        mm_reg = pickle.load(f)
    with open('models/encoder_freq.pkl', 'rb') as f:
        encoder_freq = pickle.load(f)

    return scaler_pay, scaler_ac, mm_reg, encoder_freq

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def processing_data():

    df_train = pd.read_parquet("data/train_v2.parquet")
    df_members = pd.read_parquet("data/members_v3.parquet")
    df_transactions = pd.read_parquet("data/transactions.parquet")

    scaler_pay, scaler_ac, mm_reg, encoder_freq = load_processing()



    df_transactions_2 = df_transactions.groupby("msno").agg(payment_method = ("payment_method_id","max"),
                                    payments_pan_days = ("payment_plan_days","max"),
                                    plan_list_price = ("plan_list_price","max"),
                                    is_auto_renew = ("is_auto_renew","max"),
                                    actual_paid = ("actual_amount_paid","max"),
                                    expiration_assinatura = ("membership_expire_date","max")
                                    ).reset_index()

    df_members["date_ini"] = pd.to_datetime(df_members["registration_init_time"], format='%Y%m%d')
    df_transactions_2["date_fim"] = pd.to_datetime(df_transactions_2["expiration_assinatura"], format='%Y%m%d')

    df_members = df_members.drop(columns=["registration_init_time"])
    df_transactions_2 = df_transactions_2.drop(columns=["expiration_assinatura"])

    df_raw = pd.merge(df_train,df_members, on="msno",how="left")
    df_raw = pd.merge(df_raw,df_transactions_2, on="msno",how="left")
    df_raw["year"] = df_raw["date_ini"].dt.year

    df_raw = df_raw.drop(columns=["gender","bd"])

    df_raw = df_raw.dropna()


    df_raw["days"] = df_raw.apply(lambda x: (x["date_fim"]-x["date_ini"]).days if pd.notnull(x["date_fim"]) else pd.to_datetime('today').normalize()-x["date_ini"], axis = 1)

    df_raw["days"] = df_raw["days"].astype("int64")


    df_raw = df_raw[df_raw["year"]>=2013]

    df = df_raw[df_raw["days"]>0]

    df = df.drop(columns="plan_list_price")

    df['actual_paid'] = scaler_ac.transform(df[['actual_paid']])

    df['registered_via'] = mm_reg.transform(df[['registered_via']])
    df['payments_pan_days'] = scaler_pay.transform(df[['payments_pan_days']])

    df=encoder_freq.transform(df)

    return df



def apply_models(df):
   
    model_cox, model_aft = load_models()
    

    features = ['city', 'registered_via',
       'payment_method', 'payments_pan_days', 'is_auto_renew', 'actual_paid']
    
    X_val = df[features]

    risk_score = model_cox.predict(X_val)

    df_risk = X_val.copy()
    df_risk["date_ini"] = df["date_ini"].copy()


    df_risk["risk_score"] = risk_score
    df_risk["msno"] = df["msno"]

    df_risk = df_risk.sort_values("risk_score", ascending=False)

    df_risk["risk_percentile"] = (
        df_risk["risk_score"]
        .rank(pct=True)
        )

    df_risk["risk_group"] = pd.cut(
    df_risk["risk_percentile"],
    bins=[0, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0],
    labels=["baixo", "medio", "medio-alto","alto", "muito alto", "critico"],include_lowest=True
    )


    X_val_aft = df_risk[features]

    dval = xgb.DMatrix(X_val_aft)

    t_pred = model_aft.predict(dval)


    df_risk["expected_days_to_churn"] = t_pred
    df_risk["expected_days_to_churn"] = df_risk["expected_days_to_churn"].astype('int64')

    df_risk["expected_churn_date"] = (
        df_risk["date_ini"] +
        pd.to_timedelta(df_risk["expected_days_to_churn"], unit="D")
    )

    df_risk["expected_churn_date"] = pd.to_datetime(df_risk["expected_churn_date"]).dt.normalize()


   
    df_risk['priority_score'] = df_risk['actual_paid'] / (df_risk['expected_days_to_churn'] + 1)
    

    
    return df_risk

def Simulation(df,filter_risk=["baixo", "medio", "medio-alto","alto", "muito alto", "critico"]):

    scaler_pay, scaler_ac, mm_reg, encoder_freq = load_processing()

    df['actual_paid'] = scaler_ac.inverse_transform(df[['actual_paid']])

    df['registered_via'] = mm_reg.inverse_transform(df[['registered_via']])
    df['payments_pan_days'] = scaler_pay.inverse_transform(df[['payments_pan_days']])

    df1 = df.copy()

    for col, series_mapping in encoder_freq.mapping.items():

        inv_map = {round(v, 10): k for k, v in series_mapping.items()}
        
        new_col_name = f"{col}_reverted"

        df1[new_col_name] = df1[col].round(10).map(inv_map)

     

    df2 = df1.sort_values(by='priority_score', ascending=False).reset_index(drop=True)

    df3 = simular_reversao(df2[df2["risk_group"].isin(filter_risk)], list(range(0,105,5)))

    return df3

def interpretation(df):

    _ , model_aft = load_models()

    features = ['city', 'registered_via',
       'payment_method', 'payments_pan_days', 'is_auto_renew', 'actual_paid']

    df_val = df[features]

    explainer = shap.TreeExplainer(model_aft)


    shap_values = explainer.shap_values(df_val)

    shap_exp = shap.Explanation(
    values=shap_values, 
    data=df_val, 
    feature_names=df_val.columns
    )
    
    return shap_values, shap_exp


# --- INTERFACE ---

def main():


    img_path = Path(r"img/logo.png")
    
    if img_path.exists():
        img_base64 = get_base64_of_bin_file(img_path)
        st.markdown(
            f"""
            <div style="text-align:center;">
                <img 
                    src="data:image/png;base64,{img_base64}"
                    style="width:100px; height:100px; object-fit:contain;"
                >
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        # Caso o caminho mude no futuro, este aviso te ajudará a debugar
        st.sidebar.error("Logotipo não encontrado no caminho especificado.")




    st.markdown(
    """
    <h1 style='text-align: center; color: #002B5B;'>
        🛡️ Painel de Retenção - Churn Survival
    </h1>
    """, 
    unsafe_allow_html=True
    )

    # 1. BOTÃO DE ATUALIZAÇÃO (Pipeline de Dados e Modelos)
    if st.button('🔄 Atualizar Dados e Processar Modelos'):
        with st.spinner('Buscando dados e executando predições...'):
            # Executa o pipeline sequencial
            df_raw = processing_data()                
            df_com_risco = apply_models(df_raw)       
            
            # Guardamos a base completa na sessão
            st.session_state['df_base_completa'] = df_com_risco
            
            # Explicação Global (SHAP)
            shap_vals, shap_exp = interpretation(df_com_risco)
            st.session_state['shap_vals'] = shap_vals
            st.session_state['shap_exp'] = shap_exp
            
        st.success("Dados atualizados com sucesso!")

    # 2. VERIFICAÇÃO DE DADOS CARREGADOS
    if 'df_base_completa' in st.session_state:
        df_full = st.session_state['df_base_completa']

        if 'mes_ano' not in df_full.columns:
            df_full['mes_ano'] = df_full['expected_churn_date'].dt.strftime('%Y/%m')
            df_full['ano'] = df_full['expected_churn_date'].dt.year

        # 1. Filtro de Risco (Baseado na base completa)

        st.sidebar.write("---")
        st.sidebar.markdown("<p style='color: #002B5B; font-size: 17px; font-weight: bold;'>Grau de Risco</p>", unsafe_allow_html=True)

        categorias_risco = ["baixo", "medio", "medio-alto", "alto", "muito alto", "critico"]
        padrao_risco = ["alto", "muito alto", "critico"]
        f_risk = st.sidebar.multiselect("", options=categorias_risco, default=padrao_risco)
        df_f1 = df_full[df_full['risk_group'].isin(f_risk)]



        df_f2 = df_f1.copy()
        


        st.sidebar.write("---")
        st.sidebar.markdown("<p style='color: #002B5B; font-size: 17px; font-weight: bold;'>Dias até o Churn</p>", unsafe_allow_html=True)
      


        if not df_f2.empty:
            min_base = int(df_f2['expected_days_to_churn'].min())
            max_base = int(df_f2['expected_days_to_churn'].max())

            # --- CORREÇÃO DO ERRO ---
            # Se o estado não existir ou se os valores antigos estiverem fora do novo range
            if 'dias_range' not in st.session_state:
                st.session_state.dias_range = (min_base, max_base)
            else:
                # Valida se o valor salvo ainda é permitido para os novos dados filtrados
                curr_min, curr_max = st.session_state.dias_range
                new_min = max(min_base, min(curr_min, max_base))
                new_max = max(min_base, min(curr_max, max_base))
                st.session_state.dias_range = (new_min, new_max)
            
            # Atualiza n_min e n_max para garantir sincronia com os number_inputs
            st.session_state.n_min = st.session_state.dias_range[0]
            st.session_state.n_max = st.session_state.dias_range[1]
            # ------------------------

            def slider_changed():
                st.session_state.n_min = st.session_state.dias_range[0]
                st.session_state.n_max = st.session_state.dias_range[1]

            def input_changed():
                if st.session_state.n_min > st.session_state.n_max:
                    st.session_state.n_min = st.session_state.n_max
                st.session_state.dias_range = (st.session_state.n_min, st.session_state.n_max)

            col_min, col_max = st.sidebar.columns(2)

            with col_min:
                st.number_input(
                    "Mínimo", 
                    min_value=min_base, 
                    max_value=max_base, 
                    key="n_min",
                    # REMOVIDO: value=st.session_state.n_min,
                    on_change=input_changed
                )

            with col_max:
                st.number_input(
                    "Máximo", 
                    min_value=min_base, 
                    max_value=max_base, 
                    key="n_max",
                    # REMOVIDO: value=st.session_state.n_max,
                    on_change=input_changed
                )

            f_dias = st.sidebar.slider(
                "Arraste para ajustar",
                min_value=min_base,
                max_value=max_base,
                key="dias_range",
                on_change=slider_changed
            )
        else:
            f_dias = (0, 0)



        # df_filtrado final para uso nos gráficos e simulação
        df_filtrado = df_f2[df_f2['expected_days_to_churn'].between(f_dias[0], f_dias[1])].copy()

        st.sidebar.write("---")


        # Verificação de segurança para filtros vazios
        if df_filtrado.empty:
            st.warning("⚠️ Nenhum cliente encontrado para os filtros selecionados. Ajuste a barra lateral.")
            return


        st.markdown("""
            <div style="display: flex; align-items: center; margin: 30px 0;">
                <div style="flex-grow: 1; height: 5px; background-color: #ccc;"></div>
                <span style="
                    padding: 0 20px; 
                    font-weight: bold; 
                    color: #002B5B; 
                    font-size: 28px; 
                    display: flex; 
                    align-items: center; 
                    gap: 10px;">
                    <span style="font-size: 35px;">📋</span> Relação de Clientes em Risco
                </span>
                <div style="flex-grow: 1; height: 5px; margin: 30px 0;background-color: #ccc;"></div>
            </div>
        """, unsafe_allow_html=True)



        # --- 3. TABELA DE RELAÇÃO DE CLIENTES (DINÂMICA) ---
        
        df_filtrado_2 = df_filtrado.rename(columns={'msno':"id", 'risk_group':"Grupos_de_risco", 'expected_days_to_churn':"Dias_até_o_churn", 'expected_churn_date':"Data_prevista_do_churn", 'priority_score':"Score_de_prioridade"})
        cols_view = ['id', 'Grupos_de_risco', 'Dias_até_o_churn', 'Data_prevista_do_churn', 'Score_de_prioridade']
        
        df_filtrado_2["Data_prevista_do_churn"] = df_filtrado_2["Data_prevista_do_churn"].dt.strftime('%Y-%m-%d')
        st.dataframe(df_filtrado_2[cols_view].sort_values('Score_de_prioridade', ascending=False), use_container_width=True)
        st.markdown(
            """
            <p style='color: #000000; font-size: 14px; font-weight: 500; margin-bottom: 0px;'>
                ℹ️ <i><b>O Score de prioridade já está ranqueado</b></i>
            </p>
            """, 
            unsafe_allow_html=True
        )
       

        # --- 4. GRÁFICOS E SIMULAÇÃO (DINÂMICOS) ---
       
        st.markdown("""
            <div style="display: flex; align-items: center; margin: 30px 0;">
                <div style="flex-grow: 1; height: 5px; background-color: #ccc;"></div>
                <span style="
                    padding: 0 20px; 
                    font-weight: bold; 
                    color: #002B5B; 
                    font-size: 28px; 
                    display: flex; 
                    align-items: center; 
                    gap: 10px;">
                    <span style="font-size: 35px;">📊</span> Clientes por Mês
                </span>
                <div style="flex-grow: 1; height: 5px; margin: 30px 0;background-color: #ccc;"></div>
            </div>
        """, unsafe_allow_html=True)



   
        contagem_mes = df_filtrado['mes_ano'].value_counts().sort_index()
        st.bar_chart(contagem_mes)


        st.markdown("""
            <div style="display: flex; align-items: center; margin: 30px 0;">
                <div style="flex-grow: 1; height: 5px; background-color: #ccc;"></div>
                <span style="
                    padding: 0 20px; 
                    font-weight: bold; 
                    color: #002B5B; 
                    font-size: 28px; 
                    display: flex; 
                    align-items: center; 
                    gap: 10px;">
                    <span style="font-size: 35px;">💰</span> Simulação - Perda Evitada
                </span>
                <div style="flex-grow: 1; height: 5px; margin: 30px 0;background-color: #ccc;"></div>
            </div>
        """, unsafe_allow_html=True)


        df_simulacao = Simulation(df_filtrado)
        df_simulacao["Valor Recuperado"] = df_simulacao["Valor Recuperado"].map('{:,.0f}'.format)
        df_simulacao["Rec_em_3_meses"] = df_simulacao["Rec_em_3_meses"].map('{:,.0f}'.format)
        df_simulacao["Rec_em_6_meses"] = df_simulacao["Rec_em_6_meses"].map('{:,.0f}'.format)
        df_simulacao["Rec_em_12_meses"] = df_simulacao["Rec_em_12_meses"].map('{:,.0f}'.format)
        df_simulacao["Rec_em_24_meses"] = df_simulacao["Rec_em_24_meses"].map('{:,.0f}'.format)
        st.dataframe(df_simulacao, use_container_width=True)

        # --- DETALHAMENTO DA SIMULAÇÃO ---
        st.markdown("""
            **Observação sobre a Simulação:**
            As simulações utilizam o **Score de Prioridade**, obtido pela fórmula: $R / (t + 1)$, onde $R$ é o valor pago e $t$ é o tempo faltante para o churn.
            
            1. **Cenários:** Percentual da base filtrada que conseguimos reter.
            2. **Clientes atendidos:** Volume absoluto de clientes impactados. 
            3. **Valor recuperado:** Soma do valor mensal dos clientes retidos.
            4. **Rec_em_[i]_meses:** Estimativa de receita preservada no intervalo de tempo.
            """)

        st.markdown("""
            <div style="display: flex; align-items: center; margin: 30px 0;">
                <div style="flex-grow: 1; height: 5px; background-color: #ccc;"></div>
                <span style="
                    padding: 0 20px; 
                    font-weight: bold; 
                    color: #002B5B; 
                    font-size: 28px; 
                    display: flex; 
                    align-items: center; 
                    gap: 10px;">
                    <span style="font-size: 35px;">🧠</span> Explicabilidade do Modelo (SHAP)
                </span>
                <div style="flex-grow: 1; height: 5px; margin: 30px 0; background-color: #ccc;"></div>
            </div>
        """, unsafe_allow_html=True)

        
        # Só executa se os valores do SHAP já tiverem sido calculados (pós-clique no botão)
        if 'shap_exp' in st.session_state and 'shap_vals' in st.session_state:
            col_sh1, col_sh2 = st.columns(2)
            
            with col_sh1:
                st.write("**Feature Importance (Bar Plot)**")
                fig_bar = plt.figure()
                # Acessando de forma segura
                shap.plots.bar(st.session_state['shap_exp'], show=False)
                st.pyplot(plt.gcf())
                st.markdown("""
                    **Como ler este gráfico de barras:**
                    1. **Eixo Y (Features):** As variáveis estão listadas por ordem de importância global para o modelo (o quanto impactam a previsão do tempo de vida).
                    2. **Eixo X (Mean SHAP):** Representa a magnitude média do impacto daquela variável. 
                    3. **Barras Longas:** Indicam que essa variável tem um papel fundamental na decisão do modelo sobre quando o churn ocorrerá.
                    
                    **Diferença do Summary Plot:** Enquanto este gráfico mostra **quais** variáveis são importantes, o Summary Plot (ao lado) detalha **como** cada uma delas aumenta ou diminui o tempo de vida.
                """)

            with col_sh2:
                st.write("**Summary Plot (Beeswarm)**")
                fig_sum = plt.figure()
                
                # Use o df_full (ou a variável que contém sua base processada completa)
                features_names = ['city', 'registered_via', 'payment_method', 'payments_pan_days', 'is_auto_renew', 'actual_paid']
                
                shap.summary_plot(
                    st.session_state['shap_vals'], 
                    df_full[features_names], # Substituí df_analise por df_full para evitar outro KeyError
                    show=False
                )
                st.pyplot(plt.gcf())
                st.markdown("""
                    **Como ler este gráfico:**
                    1. **Eixo Y (Variáveis):** Estão ordenadas da mais importante (topo) para a menos importante.
                    2. **Eixo X (SHAP Value):**
                            
                        **Positivo (> 0):** Aumenta o tempo de vida (Retarda o Churn).
                            
                        **Negativo (< 0):** Diminui o tempo de vida (Acelera o Churn).

                    3. **Cores (Valor da Variável):**
                            
                        * <span style='color:red'>●</span> **Vermelho:** Valores altos da variável.
                            
                        * <span style='color:blue'>●</span> **Azul:** Valores baixos da variável.

                    **Insights:** Pontos Vermelhos no lado Negativo indicam que valores altos daquela variável (ex: *actual_paid*) aceleram o churn.
                """, unsafe_allow_html=True)
        else:
            # Caso o usuário ainda não tenha clicado no botão de atualizar
            st.info("ℹ️ Clique no botão 'Atualizar Dados' no topo da página para gerar a explicabilidade do modelo (SHAP).")

    else:
        st.info("👋 Bem-vindo! Clique no botão 'Atualizar Dados' para processar a base e os modelos.")

if __name__ == "__main__":
    main()