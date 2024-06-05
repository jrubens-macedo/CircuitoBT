import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Lendo os arquivos CSV
kVA_total_comBat = pd.read_csv(r'C:\pythonjr\circuito_bt\dssfiles\kVA_total_comBat.csv')
kVA_total_semBat = pd.read_csv(r'C:\pythonjr\circuito_bt\dssfiles\kVA_total_semBat.csv')
kW_total_comBat = pd.read_csv(r'C:\pythonjr\circuito_bt\dssfiles\kW_total_comBat.csv')
kW_total_semBat = pd.read_csv(r'C:\pythonjr\circuito_bt\dssfiles\kW_total_semBat.csv')
kvar_total_comBat = pd.read_csv(r'C:\pythonjr\circuito_bt\dssfiles\kvar_total_comBat.csv')
kvar_total_semBat = pd.read_csv(r'C:\pythonjr\circuito_bt\dssfiles\kvar_total_semBat.csv')

# Renomeando as colunas para que fiquem identificáveis no DataFrame final
kVA_total_comBat.columns = ['kVA_total_comBat']
kVA_total_semBat.columns = ['kVA_total_semBat']
kW_total_comBat.columns = ['kW_total_comBat']
kW_total_semBat.columns = ['kW_total_semBat']
kvar_total_comBat.columns = ['kvar_total_comBat']
kvar_total_semBat.columns = ['kvar_total_semBat']

# Concatenando as colunas para formar o DataFrame final
df = pd.concat([kVA_total_comBat, kVA_total_semBat, kW_total_comBat, kW_total_semBat, kvar_total_comBat, kvar_total_semBat], axis=1)

# Garantindo que o DataFrame final tenha as dimensões 144x6
df = df.head(144)

# Ajustando a escala de tempo
time_minutes = np.arange(0, len(df) * 10, 10)    # Criando um array de tempo
time_hours = time_minutes / 60                   # Convertendo o tempo de minutos para horas

# Plotando resultados de potência ativa no trafo
plt.figure(figsize=(6, 6))
plt.plot(time_hours, df['kW_total_semBat'], label='Sem Storage', color='blue')
plt.plot(time_hours, df['kW_total_comBat'], label='Com Storage', color='red')
plt.xlabel('Horário (h)', fontsize=15)
plt.ylabel('Potência Ativa (kW)', fontsize=15)
plt.tick_params(axis='x', labelsize=12)
plt.tick_params(axis='y', labelsize=12)
plt.grid(True, linestyle='--')
plt.legend(fontsize=11, loc='upper left')
plt.ylim(-30, 120)
plt.xlim(0, 24)
plt.xticks(np.arange(0, 25, 2))
plt.show()

# Plotando resultados de potência reativa no trafo
plt.figure(figsize=(6, 6))
plt.plot(time_hours, df['kvar_total_semBat'], label='Sem Storage', color='blue')
plt.plot(time_hours, df['kvar_total_comBat'], label='Com Storage', color='red')
plt.xlabel('Horário (h)', fontsize=15)
plt.ylabel('Potência Reativa (kvar)', fontsize=15)
plt.tick_params(axis='x', labelsize=12)
plt.tick_params(axis='y', labelsize=12)
plt.grid(True, linestyle='--')
plt.legend(fontsize=11, loc='upper left')
plt.ylim(0, 40)
plt.xlim(0, 24)
plt.xticks(np.arange(0, 25, 2))
plt.show()

# Plotando resultados de potência aparente no trafo
plt.figure(figsize=(6, 6))
plt.plot(time_hours, df['kVA_total_semBat'], label='Sem Storage', color='blue')
plt.plot(time_hours, df['kVA_total_comBat'], label='Com Storage', color='red')
plt.xlabel('Horário (h)', fontsize=15)
plt.ylabel('Potência Aparente (kVA)', fontsize=15)
plt.axhspan(0, 75, color='lightgreen', alpha=0.3)  # Limite carregamento nominal
plt.axhspan(75, 90, color='yellow', alpha=0.3)    # Sobrecarga admissível
plt.axhspan(90, 200, color='lightcoral', alpha=0.3)  # Limite máximo de sobrecarga
plt.tick_params(axis='x', labelsize=12)
plt.tick_params(axis='y', labelsize=12)
plt.grid(True, linestyle='--')
plt.legend(fontsize=11, loc='upper left')
plt.ylim(0, 120)
plt.xlim(0, 24)
plt.xticks(np.arange(0, 25, 2))
plt.show()

