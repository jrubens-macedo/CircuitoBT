##########################################################
##   Modelagem de circuito secundário de distribuição   ##
##   Data: 10/06/2024   REV 6.0                         ##
##   by Prof. José Rubens Macedo Junior (LADEE/UFU)     ##
##########################################################

import os
import pandas as pd
import py_dss_interface
import numpy as np
import matplotlib.pyplot as plt
import re

############################
### Simulação no OpenDSS ###
############################

dss = py_dss_interface.DSS()
dss.dssinterface.allow_forms = False   ## Ativa/Desativa as telas e plots do DSS

### Chamando o dss file ###
file_dss = os.path.join(os.path.dirname(__file__), 'dssfiles/circbtfull_storage.dss') ## Chama o dss principal usando a os
file_dss_loadshapes = os.path.join(os.path.dirname(__file__), 'dssfiles/loadshapes.dss') ## Chama o dss principal usando a os

########################################################################
# Adicionando baterias ao circuito
########################################################################

bateria = "n"    # definição de inclusão ou não das baterias em um determinado poste (s=sim n=não)
socbat = 0       # definição do SOC inicial das baterias (0 a 100%)

poste_bat1 = "P7"     # definição do poste para conexão das baterias
kwrated_bat1 = 20     # definição do kW da bateria
kwhrated_bat1 = 110   # definição do kWh da bateria

#################################################################
#  Função para gerar um dataframe com os valores dos Loadshapes
#################################################################
def extract_mult_values(line):
    pattern = re.compile(r"mult=\((.*?)\)")
    match = pattern.search(line)
    if match:
        values = match.group(1)
        return [float(x) for x in values.split()]
    return []

# Dicionário para armazenar os dados dos loadshapes
loadshapes_data = {}

# Leitura do arquivo
with open(file_dss_loadshapes) as file:
    for line in file:
        if line.startswith('New loadshape'):
            parts = line.split()
            name = parts[1].split('.')[1]
            values = extract_mult_values(line)
            loadshapes_data[name] = values

# Criação do DataFrame
df = pd.DataFrame.from_dict(loadshapes_data, orient='index').transpose()

# Criando o novo loadshape CurvaGD = CurvaGD_CARGA - CurvaGD_GEN
curva_gd_carga = df['CurvaGD_CARGA']
curva_gd_gen = df['CurvaGD_GEN']
curva_gd = curva_gd_carga + (-curva_gd_gen)

# Adicionando o novo loadshape ao DataFrame
df['CurvaGD'] = curva_gd

# Extraindo os valores de CurvaCARGA em um novo vetor
values1 = df['CurvaCARGA'].tolist()
values2 = df['CurvaGD'].tolist()
values3 = df['CurvaIP'].tolist()
values4 = df['CurvaBAT'].tolist()
values5 = df['CurvaVE_Fast_1'].tolist()
values6 = df['CurvaVE_Fast_2'].tolist()
values7 = df['CurvaVE_Slow'].tolist()

############################
### Executando o DSS #######
############################

dss.text(f"Compile [{file_dss}]")
dss.text("Set mode=daily")
dss.text("Set stepsize=10m")
dss.text("Set number=144")

# Explorando os atributos do circuito
loadshapes = dss.loadshapes.names  # Comando para descobrir quais são os loadshapes do circuito
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
    dss.text(f"New Monitor.P_{i} element =Transformer.{i} terminal=1 mode=1 ppolar=no")   # mode = 1 -> medição de potências || ppolar=no -> forma retangular (P+jQ)
    dss.text(f"New Monitor.V_{i} element =Transformer.{i} terminal=2 mode=0 ppolar=yes")  # mode = 0 -> medição de tensões || ppolar=yes -> forma polar (mod/ang)

# Adicionando medidores de tensão nas barras (usando o terminal 2 das linhas)
lines = dss.lines.names
dss.text("New Monitor.V_P0_P1 element =Transformer.TRAFO terminal=2 mode=0")
for i in lines:
    dss.text(f"New Monitor.V_{i} element =Line.{i} terminal=2 mode=0")  # mode = 0 -> medição de tensões

# Inserindo a bateria no circuito
if bateria == "s":
    dss.text(f"New Storage.Bateria{poste_bat1} bus={poste_bat1}.1.2.3.4 phases=3 kv=0.22 conn=wye kwrated={kwrated_bat1} kwhrated={kwhrated_bat1} %stored={socbat} dispmode=follow daily=CurvaBAT")

# Dando Solve no circuito
dss.solution.solve()

##### Extraindo dados do monitor do poste escolhido para conexão da bateria
codposte = poste_bat1[1:]
codposte = int(codposte)
monitor = dss.monitors
monitor.name = f"V_P{codposte-1}_{poste_bat1}"
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

# Calculando a potência ativa, reativa e aparente total
monitor_ptotal = (monitor_p_a + monitor_p_b + monitor_p_c)
monitor_qtotal = (monitor_q_a + monitor_q_b + monitor_q_c)
monitor_stotal = np.sqrt(monitor_ptotal**2 + monitor_qtotal**2)

## Calculando DRP e DRC

# Calculando DRP e DRC fase A
registros_precaria_inferior_a = sum(1 for valor in monitor_v_a if valor >= 110 and valor < 117)
registros_precaria_superior_a = sum(1 for valor in monitor_v_a if valor > 133 and valor <= 135)
DRP_A = 100*((registros_precaria_superior_a + registros_precaria_inferior_a)) / len(monitor_v_a)
registros_critica_inferior_a = sum(1 for valor in monitor_v_a if valor < 110)
registros_critica_superior_a = sum(1 for valor in monitor_v_a if valor > 135)
DRC_A = 100*((registros_critica_superior_a + registros_critica_inferior_a)) / len(monitor_v_a)

# Calculando DRP e DRC fase B
registros_precaria_inferior_b = sum(1 for valor in monitor_v_b if valor >= 110 and valor < 117)
registros_precaria_superior_b = sum(1 for valor in monitor_v_b if valor > 133 and valor <= 135)
DRP_B = 100*((registros_precaria_superior_b + registros_precaria_inferior_b)) / len(monitor_v_b)
registros_critica_inferior_b = sum(1 for valor in monitor_v_b if valor < 110)
registros_critica_superior_b = sum(1 for valor in monitor_v_b if valor > 135)
DRC_B = 100*((registros_critica_superior_b + registros_critica_inferior_b)) / len(monitor_v_b)

# Calculando DRP e DRC fase C
registros_precaria_inferior_c = sum(1 for valor in monitor_v_c if valor >= 110 and valor < 117)
registros_precaria_superior_c = sum(1 for valor in monitor_v_c if valor > 133 and valor <= 135)
DRP_C = 100*((registros_precaria_superior_c + registros_precaria_inferior_c)) / len(monitor_v_c)
registros_critica_inferior_c = sum(1 for valor in monitor_v_c if valor < 110)
registros_critica_superior_c = sum(1 for valor in monitor_v_c if valor > 135)
DRC_C = 100*((registros_critica_superior_c + registros_critica_inferior_c)) / len(monitor_v_c)

# Calculando o percentil 99% e 1%
percentil_99_a = np.percentile(monitor_v_a, 99)
percentil_1_a = np.percentile(monitor_v_a, 1)
percentil_99_b = np.percentile(monitor_v_b, 99)
percentil_1_b = np.percentile(monitor_v_b, 1)
percentil_99_c = np.percentile(monitor_v_c, 99)
percentil_1_c = np.percentile(monitor_v_c, 1)

print('************ Indicadores de tensão em regime permanente **************')
print('                Fase A        Fase B       Fase C')
print(f'DRP             {DRP_A:0.2f}%         {DRP_B:0.2f}%        {DRP_C:0.2f}%')
print(f'DRC             {DRC_A:0.2f}%         {DRC_B:0.2f}%        {DRC_C:0.2f}%')
print(f'P99%            {percentil_99_a:0.2f}        {percentil_99_b:0.2f}       {percentil_99_c:0.2f}')
print(f'P1%             {percentil_1_a:0.2f}        {percentil_1_b:0.2f}       {percentil_1_c:0.2f}')
print('**********************************************************************')

# Convertendo dados para DataFrames
df1 = pd.DataFrame({
    'tempo': time_hours,
    'Tensao_Va': monitor_v_a,
    'Tensao_Vb': monitor_v_b,
    'Tensao_Vc': monitor_v_c
})
df2 = pd.DataFrame({
    'tempo': time_hours,
    'kW_total': monitor_ptotal,
})
df3 = pd.DataFrame({
    'tempo': time_hours,
    'kvar_total': monitor_qtotal,
})
df4 = pd.DataFrame({
    'tempo': time_hours,
    'kVA_total': monitor_stotal,
})

######## PLOTAGEM DE GRÁFICOS ########################################################################

# Plotando resultados de tensão
plt.figure(figsize=(6, 6))
plt.step(df1['tempo'], df1['Tensao_Va'], label='Fase A', color='red')
plt.step(df1['tempo'], df1['Tensao_Vb'], label='Fase B', color='blue')
plt.step(df1['tempo'], df1['Tensao_Vc'], label='Fase C', color='green')
plt.axhspan(117, 133, color='lightgreen', alpha=0.3)  # Faixa de tensão adequada
plt.axhspan(133, 135, color='yellow', alpha=0.3)  # Faixa de tensão precária
plt.axhspan(110, 117, color='yellow', alpha=0.3)  # Faixa de tensão precária
plt.axhspan(135, 150, color='lightcoral', alpha=0.3)  # Faixa de tensão precária
plt.axhspan(0, 110, color='lightcoral', alpha=0.3)  # Faixa de tensão precária
plt.xlabel('Horário (h)', fontsize=15)
plt.ylabel('Tensão (V)', fontsize=15)
#plt.title('(b)', fontsize=20)
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
plt.step(df2['tempo'], df2['kW_total'], color='red')
plt.xlabel('Horário (h)', fontsize=15)
plt.ylabel('Potência Ativa (kW)', fontsize=15)
plt.tick_params(axis='x', labelsize=12)
plt.tick_params(axis='y', labelsize=12)
plt.grid(True, linestyle='--')
plt.ylim(-30, 120)
plt.xlim(0, 24)
plt.xticks(np.arange(0, 25, 2))
plt.show()

# Plotando resultados de potência reativa no trafo
plt.figure(figsize=(6, 6))
plt.step(df3['tempo'], df3['kvar_total'], color='red')
plt.xlabel('Horário (h)', fontsize=15)
plt.ylabel('Potência Reativa (kvar)', fontsize=15)
plt.tick_params(axis='x', labelsize=12)
plt.tick_params(axis='y', labelsize=12)
plt.grid(True, linestyle='--')
plt.ylim(0, 30)
plt.xlim(0, 24)
plt.xticks(np.arange(0, 25, 2))
plt.show()

# Plotando resultados de potência aparente no trafo
plt.figure(figsize=(6, 6))
plt.step(df4['tempo'], df4['kVA_total'], color='black')
plt.xlabel('Horário (h)', fontsize=15)
plt.ylabel('Potência Aparente (kVA)', fontsize=15)
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

#### Gravando os vetores de potência em um dataframe

# Selecionando as respectivas potências nos dataframes
kW_total_file = df2['kW_total']
kvar_total_file = df3['kvar_total']
kVA_total_file = df4['kVA_total']
# Salvando a coluna em um arquivo CSV
kW_total_file.to_csv('kW_total.csv', index=False)
kvar_total_file.to_csv('kvar_total.csv', index=False)
kVA_total_file.to_csv('kVA_total.csv', index=False)


######## PLOTAGEM DOS LOADSHAPES ########################################################################

# Criar um array para o eixo x representando o tempo em horas
time_hours = [i * 10 / 60 for i in range(144)]  # 144 valores, cada um representando 10 minutos

# Criar a figura e os subplots
fig, axs = plt.subplots(2, 2, figsize=(10, 8))

# Definir os ticks do eixo x
xticks = range(0, 25, 2)

# Tamanho da fonte
font_size = 16
tick_size = 14

# Plotar o primeiro gráfico
axs[0, 0].step(time_hours, values1, where='post', color='blue')  # Usar gráfico de degrau
axs[0, 0].set_title('(a) Carga sem GD', fontsize=font_size)
axs[0, 0].set_xlabel('Horário (h)', fontsize=font_size)
axs[0, 0].set_ylabel('Potência Ativa (pu)', fontsize=font_size)
axs[0, 0].grid(True, linestyle='--')
axs[0, 0].set_xticks(xticks)
axs[0, 0].tick_params(axis='both', which='major', labelsize=tick_size)

# Plotar o segundo gráfico
axs[0, 1].step(time_hours, values2, where='post', color='red')  # Usar gráfico de degrau
axs[0, 1].set_title('(b) Carga com GD', fontsize=font_size)
axs[0, 1].set_xlabel('Horário (h)', fontsize=font_size)
axs[0, 1].set_ylabel('Potência Ativa (pu)', fontsize=font_size)
axs[0, 1].grid(True, linestyle='--')
axs[0, 1].set_xticks(xticks)
axs[0, 1].tick_params(axis='both', which='major', labelsize=tick_size)

# Plotar o terceiro gráfico
axs[1, 0].step(time_hours, values3, where='post', color='green')  # Usar gráfico de degrau
axs[1, 0].set_title('(c) Carga de iluminação pública', fontsize=font_size)
axs[1, 0].set_xlabel('Horário (h)', fontsize=font_size)
axs[1, 0].set_ylabel('Potência Ativa (pu)', fontsize=font_size)
axs[1, 0].grid(True, linestyle='--')
axs[1, 0].set_xticks(xticks)
axs[1, 0].tick_params(axis='both', which='major', labelsize=tick_size)

# Plotar o quarto gráfico
axs[1, 1].step(time_hours, values4, where='post', color='purple')  # Usar gráfico de degrau
axs[1, 1].set_title('(d) Carga e descarga das baterias', fontsize=font_size)
axs[1, 1].set_xlabel('Horário (h)', fontsize=font_size)
axs[1, 1].set_ylabel('Potência Ativa (pu)', fontsize=font_size)
axs[1, 1].grid(True, linestyle='--')
axs[1, 1].set_xticks(xticks)
axs[1, 1].tick_params(axis='both', which='major', labelsize=tick_size)

# Ajustar o layout
plt.tight_layout()
plt.show()


##### Plotagem dos LOADSHAPES dos carregamento de veículos elétricos ############################

# Criar a figura e os subplots
fig, axs = plt.subplots(3, 1, figsize=(5, 10))

# Definir os ticks do eixo x
xticks = range(0, 25, 2)

# Tamanho da fonte
font_size = 14
tick_size = 12

# Plotar o primeiro gráfico
axs[0].step(time_hours, values5, where='post', color='blue')  # Usar gráfico de degrau
axs[0].set_title('(a) Recarga rápida tipo 1', fontsize=font_size)
axs[0].set_xlabel('Horário (h)', fontsize=font_size)
axs[0].set_ylabel('Potência Ativa (pu)', fontsize=font_size)
axs[0].grid(True, linestyle='--')
axs[0].set_xticks(xticks)
axs[0].tick_params(axis='both', which='major', labelsize=tick_size)

# Plotar o segundo gráfico
axs[1].step(time_hours, values6, where='post', color='red')  # Usar gráfico de degrau
axs[1].set_title('(b) Recarga rápida tipo 2', fontsize=font_size)
axs[1].set_xlabel('Horário (h)', fontsize=font_size)
axs[1].set_ylabel('Potência Ativa (pu)', fontsize=font_size)
axs[1].grid(True, linestyle='--')
axs[1].set_xticks(xticks)
axs[1].tick_params(axis='both', which='major', labelsize=tick_size)

# Plotar o terceiro gráfico
axs[2].step(time_hours, values7, where='post', color='green')  # Usar gráfico de degrau
axs[2].set_title('(c) Recarga lenta', fontsize=font_size)
axs[2].set_xlabel('Horário (h)', fontsize=font_size)
axs[2].set_ylabel('Potência Ativa (pu)', fontsize=font_size)
axs[2].grid(True, linestyle='--')
axs[2].set_xticks(xticks)
axs[2].tick_params(axis='both', which='major', labelsize=tick_size)

# Ajustar o layout
plt.tight_layout()
plt.show()


######## NOVA PLOTAGEM DAS TENSÕES DOS POSTES AO LONGO DE 24 HORAS ########################################

# Função para extrair o nome da barra a partir do nome da linha

Fase_desejada = 1     # Fase A = 1, Fase B = 3 e Fase C = 5

if Fase_desejada == 1:
     fase_escolhida = "A"
     item = "(a)"
if Fase_desejada == 3:
     fase_escolhida = "B"
     item = "(b)"
if Fase_desejada == 5:
     fase_escolhida = "C"
     item = "(c)"

def extrair_nome_barra(nome_linha):
    return nome_linha.split('_')[-1].capitalize()

# Inicializando um DataFrame para armazenar as tensões de todos os postes
df_tensoes_postes = pd.DataFrame({'tempo': time_hours})

##### Iterando sobre todas as linhas para extrair as tensões das barras

# Armazenando as tensões da Fase A apenas da barra P1
barra = "P1"
monitor.name = "V_P0_P1"
tensao_fase = np.array(monitor.channel(Fase_desejada))  # Supondo Va = canal1
df_tensoes_postes[f'{barra}'] = tensao_fase

# Armazenando as tensões da Fase A das demais barras
for line in lines:
    barra = extrair_nome_barra(line)
    monitor.name = f"V_{line}"
    tensao_fase = np.array(monitor.channel(Fase_desejada))  # Supondo Va = canal1
    df_tensoes_postes[f'{barra}'] = tensao_fase

# Plotando as tensões de todos os postes
plt.figure(figsize=(7, 7))
for coluna in df_tensoes_postes.columns[1:]:  # Pulando a coluna 'tempo'
    plt.step(df_tensoes_postes['tempo'], df_tensoes_postes[coluna], where='post', label=coluna)

plt.xlabel('Horário (h)', fontsize=18)
plt.ylabel('Tensão (V)', fontsize=18)
#plt.title(f'{item} Tensões da fase {fase_escolhida} em todos os postes do circuito ({status_bat} Storage)', fontsize=15)
#plt.title('(a)', fontsize=20)
plt.axhspan(117, 133, color='lightgreen', alpha=0.3)  # Faixa de tensão adequada
plt.axhspan(133, 135, color='yellow', alpha=0.3)  # Faixa de tensão precária
plt.axhspan(110, 117, color='yellow', alpha=0.3)  # Faixa de tensão precária
plt.axhspan(135, 150, color='lightcoral', alpha=0.3)  # Faixa de tensão precária
plt.axhspan(0, 110, color='lightcoral', alpha=0.3)  # Faixa de tensão precária
#plt.legend(fontsize=11, loc='lower center', ncol=8)
plt.legend(fontsize=12, loc='lower center', ncol=5)
plt.tick_params(axis='x', labelsize=16)
plt.tick_params(axis='y', labelsize=16)
plt.grid(True, linestyle='--')
plt.ylim(100, 140)
plt.xlim(0, 24)
plt.xticks(np.arange(0, 25, 2))
plt.show()



