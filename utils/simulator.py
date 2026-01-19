import pandas as pd


def simular_reversao(data, percentuais):
    total_perda_potencial = data['actual_paid'].sum()
    resultados = []
    
    for p in percentuais:
       
        n_clientes = int(len(data) * (p / 100))
        clientes_salvos = data.head(n_clientes)
        
        receita_recuperada = clientes_salvos['actual_paid'].sum()
        percentual_valor_salvo = (receita_recuperada / total_perda_potencial) * 100

        Recuperado_em_3_meses = receita_recuperada * 3
        Recuperado_em_6_meses = receita_recuperada * 6
        Recuperado_em_12_meses = receita_recuperada * 12
        Recuperado_em_24_meses = receita_recuperada * 24
        
        resultados.append({
            'Cenário (Redução Churn %)': f"{p}%",
            'Clientes Atendidos': n_clientes,
            'Valor Recuperado': receita_recuperada,
            '% do Valor Total Salvo': percentual_valor_salvo,
            'Rec_em_3_meses': Recuperado_em_3_meses,
            'Rec_em_6_meses': Recuperado_em_6_meses,
            'Rec_em_12_meses': Recuperado_em_12_meses,
            'Rec_em_24_meses': Recuperado_em_24_meses
        })
    
    return pd.DataFrame(resultados)


