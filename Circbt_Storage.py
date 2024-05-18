##########################################################
##   Modelagem de circuito secundário de distribuição   ##
##   Data: 18/05/2024   REV 1.0                         ##
##   by Prof. José Rubens Macedo Junior (LADEE/UFU)     ##
##########################################################

import os
import pandas as pd
import py_dss_interface
import numpy as np
import matplotlib.pyplot as plt

############################
### Simulação no OpenDSS ###
############################

dss = py_dss_interface.DSS()
dss.dssinterface.allow_forms = True ## Ativa/Desativa as telas e plots do DSS

### Chamando o dss file ###
file_dss = os.path.join(os.path.dirname(__file__), 'dssfiles/circbtfull_storage.dss') ## Chama o dss principal usando a os

### Definição de variáveis
status_bat = "sem"

############################
### Executando o DSS #######
############################

dss.text(f"Compile [{file_dss}]")
dss.text("Set mode=daily")
dss.text("Set stepsize=10m")
dss.text("Set number=288")

# Explorando os atributos do circuito
buses = dss.circuit.buses_names  # Comando para descobrir quais são as barras do circuito
lines = dss.lines.names          # Comando para descobrir quais são as linhas do circuito
loads = dss.loads.names          # Comando para descobrir quais são as cargas do circuito
generators = dss.generators.names        # Comando para descobrir quais são as cargas do circuito
transformers = dss.transformers.names    # Comando para descobrir quais são os trafos do circuito

# Adicionando um EnergyMeter no início do circuito (primário do trafo)
dss.text("New EnergyMeter.ETRAFO element= Transformer.TRAFO terminal=1")

# Adicionando medidores de potência e tensão no transformador
transformers = dss.transformers.names
for i in transformers:
    dss.text(f"New Monitor.P_{i} element =Transformer.{i} terminal=1 mode=1 ppolar=no")  # mode = 1 -> medição de potências || ppolar=no -> forma retangular (P+jQ)
    dss.text(f"New Monitor.V_{i} element =Transformer.{i} terminal=2 mode=0 ppolar=yes")  # mode = 0 -> medição de tensões || ppolar=yes -> forma polar (mod/ang)

# Adicionando medidores de tensão nas barras (usando o terminal 2 das linhas)
lines = dss.lines.names
for i in lines:
    dss.text(f"New Monitor.V_{i} element =Line.{i} terminal=2 mode=0")  # mode = 0 -> medição de tensões

##########################################
# Adicionando Baterias ao circuito
##########################################

bateria = "s"    # definição de inclusão ou não das baterias em um determinado poste (s=sim n=não)

poste_bat1 = "P7"     # definição do poste para conexão das baterias
kwrated_bat1 = 20     # definição do kW da bateria
kwhrated_bat1 = 100   # definição do kWh da bateria
if bateria == "s":
    dss.text(f"New Storage.Bateria{poste_bat1} bus={poste_bat1}.1.2.3.4 phases=3 kv=0.22 conn=wye kwrated={kwrated_bat1} kwhrated={kwhrated_bat1} dispmode=follow daily=CurvaBAT")
    status_bat = "com"

# Dando Solve no circuito
dss.solution.solve()

# Extraindo dados do monitor V_P6_P7 (Bus P7)
monitor = dss.monitors
monitor.name = "V_P6_P7"
monitor_v_a = np.array(monitor.channel(1))  # Supondo Va = canal1
monitor_v_b = np.array(monitor.channel(3))  # Supondo Vb = canal3
monitor_v_c = np.array(monitor.channel(5))  # Supondo Vc = canal5
time_minutes = np.arange(0, len(monitor_v_a) * 10, 10)  # Criando um array de tempo
time_hours = time_minutes / 60  # Convertendo o tempo de minutos para horas

# Extraindo dados do monitor TRAFO
monitor.name = "P_TRAFO"
monitor_p_a = np.array(monitor.channel(1))  # Supondo Pa = canal1
monitor_p_b = np.array(monitor.channel(3))  # Supondo Pb = canal3
monitor_p_c = np.array(monitor.channel(5))  # Supondo Pc = canal5
monitor_q_a = np.array(monitor.channel(2))  # Supondo Qa = canal2
monitor_q_b = np.array(monitor.channel(4))  # Supondo Qb = canal4
monitor_q_c = np.array(monitor.channel(6))  # Supondo Qc = canal6

# Calculando potência aparente
monitor_s_a = np.sqrt(monitor_p_a**2 + monitor_q_a**2)
monitor_s_b = np.sqrt(monitor_p_b**2 + monitor_q_b**2)
monitor_s_c = np.sqrt(monitor_p_c**2 + monitor_q_c**2)
monitor_stotal = monitor_s_a + monitor_s_b + monitor_s_c

# Convertendo dados para DataFrames
df1 = pd.DataFrame({
    'tempo': time_hours,
    'Tensao_Va': monitor_v_a,
    'Tensao_Vb': monitor_v_b,
    'Tensao_Vc': monitor_v_c
})
df2 = pd.DataFrame({
    'tempo': time_hours,
    'kW_a': monitor_p_a,
    'kW_b': monitor_p_b,
    'kW_c': monitor_p_c
})
df3 = pd.DataFrame({
    'tempo': time_hours,
    'kvar_a': monitor_q_a,
    'kvar_b': monitor_q_b,
    'kvar_c': monitor_q_c
})
df4 = pd.DataFrame({
    'tempo': time_hours,
    'kVA_a': monitor_s_a,
    'kVA_b': monitor_s_b,
    'kVA_c': monitor_s_c,
    'kVA_total': monitor_stotal
})

# Filtrando para mostrar apenas as últimas 24 horas
last_24_hours_1 = df1[df1['tempo'] >= df1['tempo'].max() - 24].copy()
last_24_hours_2 = df2[df2['tempo'] >= df2['tempo'].max() - 24].copy()
last_24_hours_3 = df3[df3['tempo'] >= df3['tempo'].max() - 24].copy()
last_24_hours_4 = df4[df4['tempo'] >= df4['tempo'].max() - 24].copy()

# Ajustando a escala de tempo para começar em 00h00
last_24_hours_1.loc[:, 'tempo'] = last_24_hours_1['tempo'] - last_24_hours_1['tempo'].min()
last_24_hours_2.loc[:, 'tempo'] = last_24_hours_2['tempo'] - last_24_hours_2['tempo'].min()
last_24_hours_3.loc[:, 'tempo'] = last_24_hours_3['tempo'] - last_24_hours_3['tempo'].min()
last_24_hours_4.loc[:, 'tempo'] = last_24_hours_4['tempo'] - last_24_hours_4['tempo'].min()

# Plotando resultados de tensão
plt.figure(figsize=(6, 6))
plt.plot(last_24_hours_1['tempo'], last_24_hours_1['Tensao_Va'], label='Fase A', color='red')
plt.plot(last_24_hours_1['tempo'], last_24_hours_1['Tensao_Vb'], label='Fase B', color='blue')
plt.plot(last_24_hours_1['tempo'], last_24_hours_1['Tensao_Vc'], label='Fase C', color='green')
plt.axhspan(117, 133, color='lightgreen', alpha=0.3)  # Faixa de tensão adequada
plt.axhspan(133, 135, color='yellow', alpha=0.3)  # Faixa de tensão precária
plt.axhspan(110, 117, color='yellow', alpha=0.3)  # Faixa de tensão precária
plt.axhspan(135, 150, color='lightcoral', alpha=0.3)  # Faixa de tensão precária
plt.axhspan(0, 110, color='lightcoral', alpha=0.3)  # Faixa de tensão precária
plt.xlabel('tempo (h)', fontsize=15)
plt.ylabel('Tensão (V)', fontsize=15)
plt.title(f'Perfil Diário de Tensão ({status_bat} Storage)', fontsize=15)  # Usando f-string para incluir o valor de status_bat
plt.legend(fontsize=11, loc='upper right')
plt.tick_params(axis='x', labelsize=12)
plt.tick_params(axis='y', labelsize=12)
plt.grid(True, linestyle='--')
plt.ylim(105, 140)
plt.xlim(0, 24)
plt.xticks(np.arange(0, 25, 2))
plt.show()

# Plotando resultados de potência ativa no trafo
plt.figure(figsize=(6, 6))
plt.plot(last_24_hours_2['tempo'], last_24_hours_2['kW_a'], label='Fase A', color='red')
plt.plot(last_24_hours_2['tempo'], last_24_hours_2['kW_b'], label='Fase B', color='blue')
plt.plot(last_24_hours_2['tempo'], last_24_hours_2['kW_c'], label='Fase C', color='green')
plt.xlabel('tempo (h)', fontsize=15)
plt.ylabel('Potência Ativa (kW)', fontsize=15)
plt.title(f'Perfil Diário de Carregamento ({status_bat} Storage)', fontsize=15)  # Usando f-string para incluir o valor de status_bat
plt.legend(fontsize=11, loc='upper right')
plt.tick_params(axis='x', labelsize=12)
plt.tick_params(axis='y', labelsize=12)
plt.grid(True, linestyle='--')
plt.ylim(-30, 50)
plt.xlim(0, 24)
plt.xticks(np.arange(0, 25, 2))
plt.show()

# Plotando resultados de potência reativa no trafo
plt.figure(figsize=(6, 6))
plt.plot(last_24_hours_3['tempo'], last_24_hours_3['kvar_a'], label='Fase A', color='red')
plt.plot(last_24_hours_3['tempo'], last_24_hours_3['kvar_b'], label='Fase B', color='blue')
plt.plot(last_24_hours_3['tempo'], last_24_hours_3['kvar_c'], label='Fase C', color='green')
plt.xlabel('tempo (h)', fontsize=15)
plt.ylabel('Potência Reativa (kvar)', fontsize=15)
plt.title(f'Perfil Diário de Carregamento ({status_bat} Storage)', fontsize=15)  # Usando f-string para incluir o valor de status_bat
plt.legend(fontsize=11, loc='upper right')
plt.tick_params(axis='x', labelsize=12)
plt.tick_params(axis='y', labelsize=12)
plt.grid(True, linestyle='--')
plt.ylim(0, 15)
plt.xlim(0, 24)
plt.xticks(np.arange(0, 25, 2))
plt.show()

# Plotando resultados de potência aparente no trafo
plt.figure(figsize=(6, 6))
plt.plot(last_24_hours_4['tempo'], last_24_hours_4['kVA_total'], label='Stotal', color='black')
plt.xlabel('tempo (h)', fontsize=15)
plt.ylabel('Potência Aparente (kVA)', fontsize=15)
plt.title(f'Perfil Diário de Carregamento ({status_bat} Storage)', fontsize=15)  # Usando f-string para incluir o valor de status_bat
plt.tick_params(axis='x', labelsize=12)
plt.tick_params(axis='y', labelsize=12)
plt.grid(True, linestyle='--')
plt.axhspan(0, 75, color='lightgreen', alpha=0.3)  # Limite carregamento nominal
plt.axhspan(75, 90, color='yellow', alpha=0.3)    # Sobrecarga admissível
plt.axhspan(90, 200, color='lightcoral', alpha=0.3)  # Limite máximo de sobrecarga
plt.ylim(0, 150)
plt.xlim(0, 24)
plt.xticks(np.arange(0, 25, 2))
plt.show()


