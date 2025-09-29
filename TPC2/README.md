import random
fosforos = 21

while True:
    a = input("Jogo -> 21 Fósforos. Quem pegar o último fósforo perde. Queres começar? (Sim ou Não)")
    if (a == "Sim"):
        print("Força nisso!")
        vez_jogador = True
        vez_computador = False
        break
    elif (a == "Não"):
        print("Então aqui vou eu!")
        vez_jogador = False
        vez_computador = True
        break
    else:
        print("Responde apenas: Sim ou Não.")

while fosforos > 1:
    while (vez_jogador == True):
            if fosforos == 1:
                 print("Perdeste!")
                 break
            try:
                 n = int(input("Quantos fósforos deseja tirar? (1 a 4)"))
                 if 1 <= n <= 4 and n <= fosforos:
                     fosforos -= n
                     print(f"Tiraste {n} fósforos!")
                     vez_jogador = False
                     vez_computador = True
                 else:
                     print("Tem de ser de 1 a 4.")
            except ValueError:
                 print("Digite um número!")
            print(f"Sobram {fosforos} fósforos!")
    while (vez_computador == True):
            if fosforos == 1:
                print("Perdi!")
                break
            elif 2 <= fosforos <= 5:
                comput = fosforos - 1
                vez_computador = False
                vez_jogador = True
            else:
               jogada = (fosforos - 1) % 5
               if 1 <= jogada <= 4 and jogada <= fosforos:
                    comput = jogada
                    vez_computador = False
                    vez_jogador = True
               else:
                   comput = random.randint(1, min(4, fosforos - 1))
                   vez_computador = False
                   vez_jogador = True
            fosforos -= comput
            print(f"Eu tiro {comput} fósforos!")
            print(f"Sobram {fosforos} fósforos!")
if fosforos == 1 and vez_jogador == True:
     print("Perdeste!")
