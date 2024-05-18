import pandas as pd
import matplotlib.pyplot as plt

# Definir o caminho do arquivo corretamente
file_path = r'C:\pythonjr\circuito_bt\dssfiles\gerador_loadshapes.xlsm'

# Ler o arquivo Excel
df = pd.read_excel(file_path, header=None)

# Selecionar os intervalos (linhas dos vetores que contém os loadshapes)
values1 = df.iloc[2, 2:146]  # De C3 a EP3 (144 valores)
values2 = df.iloc[7, 2:146]  # Ajustar para começar da coluna correta
values3 = df.iloc[5, 2:146]  # Ajustar para começar da coluna correta
values4 = df.iloc[6, 2:146]  # Ajustar para começar da coluna correta

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
