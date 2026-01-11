import json
import random
import numpy as np
import FreeSimpleGUI as sg
import matplotlib.pyplot as plt
import csv

def carregar_doentes(nome_ficheiro, tempo_consulta_medio):
    ficheiro = open(nome_ficheiro, "r", encoding="utf-8")
    pessoas = json.load(ficheiro)
    ficheiro.close()

    doentes = []

    i = 0
    while i < len(pessoas):
        pessoa = pessoas[i]

        nome = pessoa["nome"]
        idade = pessoa["idade"]

        r = random.random()
        if r < 0.05:
            pulseira = "Vermelha"
            prioridade = 1
        elif r < 0.15:
            pulseira = "Laranja"
            prioridade = 2
        elif r < 0.45:
            pulseira = "Amarela"
            prioridade = 3
        elif r < 0.85:
            pulseira = "Verde"
            prioridade = 4
        else:
            pulseira = "Azul"
            prioridade = 5
        tempo_consulta = random.randint((tempo_consulta_medio - tempo_consulta_medio // 2), tempo_consulta_medio + 5)
  
        especialidade = random.choices(
            ["Geral", "Pediatria", "Ortopedia"],
            weights=[0.6, 0.2, 0.2],
            k=1
        )[0]

        doentes.append({
            "nome": nome,
            "idade": idade,
            "tempo_consulta": tempo_consulta,
            "pulseira": pulseira,
            "prioridade": prioridade,
            "especialidade": especialidade
        })

        i += 1

    return doentes

def percentagem_ocupacao(estado):
    if len(estado["hist_ocup"]) == 0:
        return 0
    media = sum(estado["hist_ocup"]) / len(estado["hist_ocup"])
    return media * 100

def inicializar_estado(duracao, taxa, num_medicos, doentes, dist_chegada):
    estado = {}
    estado["atendidos_pulseira"] = {
    "Vermelha": 0,
    "Laranja": 0,
    "Amarela": 0,
    "Verde": 0,
    "Azul": 0
}
    estado["atendidos_especialidade"] = {
    "Geral": 0,
    "Pediatria": 0,
    "Ortopedia": 0
}

    estado["tempo"] = 0
    estado["duracao"] = duracao
    estado["taxa"] = taxa
    estado["indice"] = 0
    estado["doentes"] = doentes
    estado["tempo_total_clinica"] = 0
    estado["tempo_total_espera"] = 0
    estado["doentes_atendidos"] = []

    estado["filas"] = {
        "Geral": [],
        "Pediatria": [],
        "Ortopedia": []

    }

    estado["medicos"] = []
    i = 0
    while i < num_medicos:
        especialidade = random.choices(
            ["Geral", "Pediatria", "Ortopedia"],
            weights=[0.45, 0.25, 0.3],
            k=1
        )[0]

        estado["medicos"].append({
            "especialidade": especialidade,
            "atender": None
        })
        i += 1

    if dist_chegada == "Exponencial":
        estado["proxima_chegada"] = np.random.exponential(1 / taxa)
    elif dist_chegada == "Normal":
        estado["proxima_chegada"] = max(0, np.random.normal(1 / taxa, 1))
    elif dist_chegada == "Uniforme":
        estado["proxima_chegada"] = np.random.uniform(0, 2 / taxa)

    estado["hist_fila"] = []
    estado["hist_ocup"] = []
    estado["total_atendidos"] = 0


    return estado

def passo_simulacao(estado, dist_chegada):
    tempo = estado["tempo"]

    if tempo < estado["duracao"]:

        if tempo >= estado["proxima_chegada"] and estado["indice"] < len(estado["doentes"]):
            d = estado["doentes"][estado["indice"]]
            d["tempo_chegada"] = estado["tempo"]
            estado["filas"][d["especialidade"]].append(d)
            estado["indice"] += 1

            if dist_chegada == "Exponencial":
                estado["proxima_chegada"] += np.random.exponential(1 / estado["taxa"])
            elif dist_chegada == "Normal":
                estado["proxima_chegada"] += max(0, np.random.normal(1 / estado["taxa"], 1))
            elif dist_chegada == "Uniforme":
                estado["proxima_chegada"] += np.random.uniform(0, 2 / estado["taxa"])

        i = 0
        while i < len(estado["medicos"]):
            medico = estado["medicos"][i]
            if medico["atender"] is not None:
                medico["atender"]["tempo_restante"] -= 1
                if medico["atender"]["tempo_restante"] <= 0:
                    d = medico["atender"]
                    tempo_saida = estado["tempo"]
                    tempo_chegada = medico["atender"]["tempo_chegada"]
                    estado["tempo_total_clinica"] += (tempo_saida - tempo_chegada)
                    estado["total_atendidos"] += 1
                    pulseira = medico["atender"]["pulseira"]
                    estado["atendidos_pulseira"][pulseira] += 1
                    esp = medico["atender"]["especialidade"]
                    estado["atendidos_especialidade"][esp] += 1
                    d["tempo_espera"] = tempo_saida - tempo_chegada
                    estado["doentes_atendidos"].append(d)
                    medico["atender"] = None

            i += 1

        i = 0
        while i < len(estado["medicos"]):
            medico = estado["medicos"][i]
            fila = estado["filas"][medico["especialidade"]]

            if medico["atender"] is None and len(fila) > 0:
                indice_escolhido = 0
                j = 1
                while j < len(fila):
                    if fila[j]["prioridade"] < fila[indice_escolhido]["prioridade"]:
                        indice_escolhido = j
                    j += 1

                d = fila.pop(indice_escolhido)
                medico["atender"] = {
                    "nome": d["nome"],
                    "tempo_restante": d["tempo_consulta"],
                    "pulseira": d["pulseira"],
                    "tempo_chegada": d["tempo_chegada"],
                    "especialidade": d["especialidade"],
                    "tempo_chegada_inicio_atendimento": estado["tempo"]
                }
                tempo_espera = estado["tempo"] - d["tempo_chegada"]
                d["tempo_espera"] = tempo_espera
                estado["tempo_total_espera"] += tempo_espera
            i += 1

        ocupados = 0
        i = 0
        while i < len(estado["medicos"]):
            if estado["medicos"][i]["atender"] is not None:
                ocupados += 1
            i += 1

        tamanho_filas = sum(len(f) for f in estado["filas"].values())
        estado["hist_fila"].append(tamanho_filas)
        estado["hist_ocup"].append(ocupados / len(estado["medicos"]))

        estado["tempo"] += 1

def exportar_csv(estado, nome_ficheiro):
    ficheiro = open(nome_ficheiro, "w", newline="", encoding="utf-8")
    writer = csv.writer(ficheiro)
    writer.writerow(["tempo", "tamanho_fila", "ocupacao"])

    i = 0
    while i < len(estado["hist_fila"]):
        writer.writerow([
            i,
            estado["hist_fila"][i],
            estado["hist_ocup"][i]
        ])
        i += 1

    ficheiro.close()

def mostrar_graficos(estado):
    plt.figure()
    plt.plot(estado["hist_fila"])
    plt.title("Evolução do tamanho da fila")
    plt.xlabel("Tempo")
    plt.ylabel("Doentes")
    plt.grid()
    plt.show()

    plt.figure()
    plt.plot(estado["hist_ocup"])
    plt.title("Ocupação dos médicos")
    plt.xlabel("Tempo")
    plt.ylabel("Taxa")
    plt.grid()
    plt.show()

def histograma_pulseiras(estado):
    pulseiras = []
    valores = []

    for p in estado["atendidos_pulseira"]:
        pulseiras.append(p)
        valores.append(estado["atendidos_pulseira"][p])

    plt.figure()
    plt.bar(pulseiras, valores)
    plt.title("Doentes atendidos por pulseira (Manchester)")
    plt.xlabel("Pulseira")
    plt.ylabel("Número de doentes")
    plt.grid(axis="y")
    plt.show()

def histograma_doentes_especialidade(estado):
    especialidades = []
    valores = []

    for esp in estado["atendidos_especialidade"]:
        especialidades.append(esp)
        valores.append(estado["atendidos_especialidade"][esp])

    plt.figure()
    plt.bar(especialidades, valores)
    plt.title("Doentes atendidos por especialidade")
    plt.xlabel("Especialidade")
    plt.ylabel("Número de doentes")
    plt.grid(axis="y")
    plt.show()

def histograma_pulseiras(estado):
    pulseiras = ["Vermelha", "Laranja", "Amarela", "Verde", "Azul"]
    valores = [estado["atendidos_pulseira"][p] for p in pulseiras]
    plt.figure()
    plt.bar(pulseiras, valores)
    plt.title("Doentes atendidos por pulseira (Manchester)")
    plt.xlabel("Pulseira")
    plt.ylabel("Número de doentes")
    plt.grid(axis="y")
    plt.show()
    total_espera = {p: 0 for p in pulseiras}
    contagem = {p: 0 for p in pulseiras}
    for d in estado["doentes_atendidos"]:
        total_espera[d["pulseira"]] += d["tempo_espera"]
        contagem[d["pulseira"]] += 1
    medias = [total_espera[p] / contagem[p] if contagem[p] > 0 else 0 for p in pulseiras]
    plt.figure()
    plt.bar(pulseiras, medias, color ='red')
    plt.title("Tempo médio de espera por pulseira")
    plt.xlabel("Pulseira")
    plt.ylabel("Tempo médio de espera (minutos)")
    plt.grid(axis="y")
    plt.show()

def histograma_tempo_espera_especialidade(estado):
    especialidades = ["Geral", "Pediatria", "Ortopedia"]
    valores = []
    for esp in especialidades:
        tempos = [d["tempo_chegada"] - d["tempo_chegada"] + d["tempo_restante"] if "tempo_restante" in d else d["tempo_restante_atendido"] for d in estado["doentes_atendidos"] if d["especialidade"] == esp]
        tempos_espera = [d["tempo_chegada_inicio_atendimento"] - d["tempo_chegada"] for d in estado["doentes_atendidos"] if d["especialidade"] == esp]
        if len(tempos_espera) > 0:
            media = sum(tempos_espera) / len(tempos_espera)
        else:
            media = 0
        valores.append(media)
    plt.figure()
    plt.bar(especialidades, valores, color = 'red')
    plt.title("Tempo médio de espera por especialidade")
    plt.xlabel("Especialidade")
    plt.ylabel("Tempo médio de espera")
    plt.grid(axis="y")
    plt.show()

def run_gui():
    sg.theme("TanBlue")
    TITULO = ("Segoe UI", 20, "bold")
    SUBTITULO = ("Segoe UI", 12, "bold")
    TEXTO = ("Segoe UI", 11)
    config_col = [
        [sg.Text("Configuração", font=SUBTITULO)],
        [sg.Text("Número de médicos", font=TEXTO)],
        [sg.Input("3", key="MED", size=(6, 1))],

        [sg.Text("Taxa de chegada", font=TEXTO)],
        [sg.Input("0.15", key="TAXA", size=(6, 1))],

        [sg.Text("Distribuição das chegadas", font=TEXTO)],
        [sg.Combo(["Exponencial", "Normal", "Uniforme"], default_value="Exponencial",
                key="DIST_CHEGADA", readonly=True)],

        [sg.Text("Tempo médio de consulta", font=TEXTO)],
        [sg.Input("15", key="TEMPO_CONSULTA", size=(6,1))],

        [sg.Text("Duração da simulação", font=TEXTO)],
        [sg.Input("120", key="DUR", size=(6, 1))]
]

    control_col = [
        [sg.Text("Controlo", font=SUBTITULO)],
        [sg.Button("Iniciar", size=(14,1), button_color=("white", "#2ECC71"))],
        [sg.Button("Parar", size=(14,1), button_color=("white", "#E74C3C"))],
        [sg.Button("Gráficos", size=(14,1))],
        [sg.Button("H. Pulseiras", size=(14,1))],
        [sg.Button("H. Especialidades", size=(14,1))],
        [sg.Button("Exportar CSV", size=(14,1))]
]

    visual_col = [
        [sg.Frame("Fila de Espera", [
        [sg.Listbox(values=[], size=(42, 10), key="FILA")]
    ])],

        [sg.Frame("Médicos", [
        [sg.Listbox(values=[], size=(42, 6), key="MEDICOS")]
    ])],

        [sg.Frame("Estatísticas", [
            [sg.Text("Atendidos:", font=TEXTO), sg.Text("0", key="STAT_ATEND")],
            [sg.Text("Ocupação média:", font=TEXTO), sg.Text("0%", key="STAT_OCUP")],
            [sg.Text("Tempo médio na clínica:", font=TEXTO), sg.Text("0", key="STAT_TM_CLINICA")],
            [sg.Text("Tempo médio de espera:", font=TEXTO), sg.Text("0", key="STAT_TM_ESPERA")],
            [sg.Text("Pulseiras na fila:", font=TEXTO)],
            [sg.Text("Vermelha -", font=TEXTO), sg.Text("0", key="FILA_VERMELHA")],
            [sg.Text("Laranja -", font=TEXTO), sg.Text("0", key="FILA_LARANJA")],
            [sg.Text("Amarela -", font=TEXTO), sg.Text("0", key="FILA_AMARELA")],
            [sg.Text("Verde -", font=TEXTO), sg.Text("0", key="FILA_VERDE")],
            [sg.Text("Azul -", font=TEXTO), sg.Text("0", key="FILA_AZUL")]

    ])]
]

    layout = [
        [sg.Text("Simulação de Clínica Médica", font=TITULO, expand_x=True, justification="center")],
        [sg.Column(config_col),
        sg.VSeparator(),
        sg.Column(control_col),
        sg.VSeparator(),
        sg.Column(visual_col)]
]

    window = sg.Window("Clínica", layout)

    estado = None
    em_execucao = False

    em_loop = True

    while em_loop:
        event, values = window.read(timeout=500)

        if event == sg.WINDOW_CLOSED:
            em_loop = False


        if event == "Iniciar":
            dist_chegada = values["DIST_CHEGADA"]
            tempo_consulta_medio = int(values["TEMPO_CONSULTA"])
            doentes = carregar_doentes("pessoas.json", tempo_consulta_medio)
            estado = inicializar_estado(
                int(values["DUR"]),
                float(values["TAXA"]),
                int(values["MED"]),
                doentes,
                dist_chegada
            )
            em_execucao = True

        if event == "Parar":
            em_execucao = False

        if em_execucao and estado is not None:
            passo_simulacao(estado, dist_chegada)
            fila_texto = []
            for especialidade, fila in estado["filas"].items():
                for d in fila:
                    fila_texto.append(f"{d['pulseira']} - {d['nome']} ({especialidade})")
            window["FILA"].update(fila_texto)
            fila_contagem = {"Vermelha": 0, "Laranja": 0, "Amarela": 0, "Verde": 0, "Azul": 0}
            for fila in estado["filas"].values():
                for d in fila:
                    fila_contagem[d["pulseira"]] += 1
            window["FILA_VERMELHA"].update(fila_contagem["Vermelha"])
            window["FILA_LARANJA"].update(fila_contagem["Laranja"])
            window["FILA_AMARELA"].update(fila_contagem["Amarela"])
            window["FILA_VERDE"].update(fila_contagem["Verde"])
            window["FILA_AZUL"].update(fila_contagem["Azul"])
            medicos_texto = []
            for m in estado["medicos"]:
                if m["atender"] is None:
                    medicos_texto.append(f"{m['especialidade']} - Livre")
                else:
                    medicos_texto.append(f"{m['especialidade']} - {m['atender']['pulseira']} - A atender: {m['atender']['nome']}")
            window["MEDICOS"].update(medicos_texto)
            window["STAT_ATEND"].update(estado["total_atendidos"])
            window["STAT_OCUP"].update(f"{percentagem_ocupacao(estado):.1f}%")
            total_atendidos = estado["total_atendidos"]
            if total_atendidos > 0:
                tempo_medio_clinica = estado["tempo_total_clinica"] / total_atendidos
                tempo_medio_espera = estado["tempo_total_espera"] / total_atendidos
            else:
                tempo_medio_clinica = 0
                tempo_medio_espera = 0

            window["STAT_TM_CLINICA"].update(f"{tempo_medio_clinica:.1f}")
            window["STAT_TM_ESPERA"].update(f"{tempo_medio_espera:.1f}")
        if event == "Gráficos" and estado is not None:
            mostrar_graficos(estado)
        if event == "H. Pulseiras" and estado is not None:
            histograma_pulseiras(estado)
        if event == "H. Especialidades" and estado is not None:
            histograma_doentes_especialidade(estado)
            histograma_tempo_espera_especialidade(estado)
        if event == "Exportar CSV" and estado is not None:
            exportar_csv(estado, "resultados_simulacao.csv")

    window.close()

run_gui()
