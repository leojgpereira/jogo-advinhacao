from socket import *
import signal
import json
from threading import Thread, Event
import time
import pickle
import uuid
import random

clientSocket = socket(AF_INET, SOCK_STREAM)

def controlC(signum, frame):
    requisicao = {
        "acao": "SIGINT",
        "data": None
    }

    clientSocket.send(json.dumps(requisicao).encode("utf-8"))
    clientSocket.close()
    exit(0)

def aguardandoConvite(conexao, event):
    while True:
        conexao[0].listen(1)
        
        try:
            conexao[1], address = conexao[0].accept()
        except ConnectionAbortedError:
            conexao[0].close()
            exit(0)

        print("\nNovo convite recebido")
        print("Aceitar conexão? (sim/nao)")

        while True:
            if not event.is_set():
                ganhador = False
                print("Conexão estabelecida com o adversário")
                print("Aguarde...")

                mensagem = pickle.loads(conexao[1].recv(2048))

                if conexao[2] == True:
                    if mensagem["acao"] ==  "SOLICITACAO" and mensagem["code"] == "GAME_INI":
                        requisicao = {
                            "acao": "SOLICITACAO",
                            "code": "GAME_ACK",
                        }

                        conexao[1].send(pickle.dumps(requisicao))
                        break
                else:
                    requisicao = {
                        "acao": "SOLICITACAO",
                        "code": "GAME_NEG",
                    }

                    conexao[1].send(pickle.dumps(requisicao))
                    conexao[1].close()

                    print()
                    print("Convite recusado")
                    print()

                    event.set()
                    break

            time.sleep(1)
        
        if conexao[2] == True:
            palavras = ['ABACAXI', 'ABELHA', 'ABOBORA', 'AMOR', 'AVENTURA', 'AVIAO', 'BAILARINA', 'BALA', 'BALEIA', 'BANCO', 'CADEIRA', 'CAFE', 'CACHORRO', 'CADEADO', 'DANCA', 'DEDO', 'ELEFANTE', 'ESCOVA', 'ESCUDO', 'FADA', 'FAMILIA', 'FESTA', 'FLORESTA', 'FLOR', 'FOGUETE', 'FUTEBOL', 'GATO', 'GUITARRA', 'HAMSTER', 'HELICOPTERO', 'HEROI', 'HISTORIA', 'ILHA', 'INVERNO', 'JARDIM', 'JOGAR', 'LANTERNA', 'LEAO', 'LIVRO', 'LUA', 'MACACO', 'MALA', 'MANGUEIRA', 'MAR', 'MARTE', 'MENSAGEM', 'MONTANHA', 'NADAR', 'NAVE', 'NAVIO', 'NEVE', 'NOITE']

            index = random.randint(0, len(palavras) - 1)
            palavra = palavras[index]

            requisicao = {
                "acao": "SOLICITACAO",
                "code": "JOGANDO",
                "data": {
                    "palavra": [letra for letra in palavra],
                    "acertos": ["_" for letra in palavra],
                    "chutes": set(),
                    "concluido": False
                }
            }

            conexao[1].send(pickle.dumps(requisicao))
            mensagem = pickle.loads(conexao[1].recv(2048))

            gameOver = False

            if mensagem["acao"] == "SOLICITACAO" and mensagem["code"] == "GAME_OVER":
                gameOver = True
                gameOverId = mensagem["data"]["id"]

                print()
                print("Jogador adversário desistiu")
                print()

            while not gameOver and not mensagem["data"]["concluido"]:
                requisicao = {
                    "acao": "SOLICITACAO",
                    "code": "JOGANDO",
                    "data": {
                        "palavra": mensagem["data"]["palavra"],
                        "acertos": mensagem["data"]["acertos"],
                        "chutes": mensagem["data"]["chutes"],
                        "concluido": mensagem["data"]["concluido"],
                    }
                }

                print()
                print(mensagem["data"]["acertos"])
                print()

                letra = input("Sua vez de jogar... escolha uma letra: ")
                requisicao["data"]["chutes"].add(letra)

                for i in range(len(mensagem["data"]["palavra"])):
                    if mensagem["data"]["palavra"][i] == letra:
                        requisicao["data"]["acertos"][i] = letra
                
                if requisicao["data"]["acertos"].count("_") < 1:
                        requisicao["data"]["concluido"] =  True

                        ganhador = True

                        conexao[1].send(pickle.dumps(requisicao))
                        conexao[1].close()

                        event.set()
                        break
                
                conexao[1].send(pickle.dumps(requisicao))

                print("Aguardando jogador adversário...")

                mensagem = conexao[1].recv(2048)
                mensagem = pickle.loads(mensagem)

                if mensagem["acao"] == "SOLICITACAO" and mensagem["code"] == "GAME_OVER":
                    gameOver = True
                    gameOverId = mensagem["data"]["id"]

                    print()
                    print("Jogador adversário desistiu")
                    print()

            if ganhador and not gameOver:
                print()
                print("*" * 35)
                print("***** Você ganhou... Parabéns!!****")
                print("*" * 35)
                print()
            elif not ganhador and not gameOver:
                print()
                print("*" * 35)
                print("*Você perdeu... tente novamente :(*")
                print("*" * 35)
                print()

            conexao[1].close()

            if gameOver:
                requisicao = {
                    "acao": "GAME_OVER",
                    "data": mensagem["data"]
                }

                clientSocket.send(json.dumps(requisicao).encode("utf-8"))

            event.set()

def main():
    serverName = "127.0.0.1"
    serverPort = 12000

    clientSocket.connect((serverName,serverPort))

    signal.signal(signal.SIGINT, controlC)

    autenticado = False

    while not autenticado:
        print("Escolha uma opção:")
        print("(1) Registrar")
        print("(2) Logar")
        print()

        opcao = input("Opção: ")

        if opcao == "1":
            print()

            nome = input("Nome: ")
            usuario = input("Usuário: ")
            senha = input("Senha: ")

            novoUsuario = {
                "nome": nome,
                "usuario": usuario,
                "senha": senha
            }

            requisicao = {
                "acao": "REGISTRAR",
                "data": novoUsuario
            }

            clientSocket.send(json.dumps(requisicao).encode("utf-8"))
            mensagem = json.loads(clientSocket.recv(2048).decode())

            if(mensagem["acao"] == "REGISTRAR" and mensagem["code"] == "OK"):
                print("Usuário registrado com sucesso!")

        elif opcao == "2":
            print()

            usuario = input("Usuário: ")
            senha = input("Senha: ")

            usuario = {
                "usuario": usuario,
                "senha": senha
            }

            conviteSocket = socket(AF_INET,SOCK_STREAM)
            conviteSocket.bind(("", 0))
            connectionSocket = None
            event = Event()
            event.set()
            conexaoAceita = False
            conexao = [conviteSocket, connectionSocket, conexaoAceita]
            convite = Thread(target = aguardandoConvite, args = [conexao, event])
            convite.start()

            requisicao = {
                "acao": "AUTENTICAR",
                "porta": conviteSocket.getsockname()[1],
                "data": usuario
            }

            clientSocket.send(json.dumps(requisicao).encode("utf-8"))
            mensagem = json.loads(clientSocket.recv(2048).decode())

            if(mensagem["acao"] == "AUTENTICAR" and mensagem["code"] == "OK"):
                print("Usuário autenticado com sucesso!")
                autenticado = True
            else:
                print("Usuário e/ou senha incorretos!")
        else:
            print("Escolha uma opção válida")
            print()
    
    while autenticado:
        event.wait()

        print("Escolha uma opção:")
        print("(1) Listar usuários online")
        print("(2) Listar usuários jogando")
        print("(3) Iniciar jogo")
        print("(4) Desconectar")
        print()

        opcao = input("Opção: ")
        
        if opcao == "1":
            requisicao = {
                "acao": "LISTAR_USUARIOS_ONLINE",
                "data": None
            }

            clientSocket.send(json.dumps(requisicao).encode("utf-8"))
            mensagem = json.loads(clientSocket.recv(2048).decode())
            
            if mensagem["acao"] == "LISTAR_USUARIOS_ONLINE" and mensagem["code"] == "OK":
                data = mensagem["data"]
                print("-------------------- Lista de usuários online --------------------")
                for usuario in data:
                    print(usuario["usuario"], "ONLINE", usuario['ip'], usuario['porta'])

                print("------------------------------------------------------------------")
            else:
                print("Não foi possível recuperar a lista de usuários online!")
            
            print()
        elif opcao == "2":
            requisicao = {
                "acao": "LISTAR_USUARIOS_JOGANDO",
                "data": None
            }

            clientSocket.send(json.dumps(requisicao).encode("utf-8"))
            mensagem = json.loads(clientSocket.recv(2048).decode())
            
            if mensagem["acao"] == "LISTAR_USUARIOS_JOGANDO" and mensagem["code"] == "OK":
                data = mensagem["data"]
                print("-------------------- Lista de usuários jogando --------------------")
                for partida in data:
                    print("%s (%s:%s) x %s (%s:%s)" % (partida["jogador_1"]["usuario"], partida["jogador_1"]["ip"], partida["jogador_1"]["porta"], partida["jogador_2"]["usuario"], partida["jogador_2"]["ip"], partida["jogador_2"]["porta"]))

                print("------------------------------------------------------------------")
            else:
                print("Não foi possível recuperar a lista de usuários jogando!")
            
            print()
        elif opcao == "3":
            id = uuid.uuid4()

            ip = input("Insira o IP do jogador que deseja convidar: ")
            porta = input("Digite a porta do usuário que deseja convidar: ")

            if int(porta) == conviteSocket.getsockname()[1]:
                print()
                print("Não é possível jogar contra você mesmo")
                print()
                continue

            adversarioSocket = socket(AF_INET, SOCK_STREAM)
            adversarioSocket.connect((ip, int(porta)))
            print("Aguardando aceite do adversário")

            requisicao = {
                "acao": "SOLICITACAO",
                "code": "GAME_INI",
            }

            adversarioSocket.send(pickle.dumps(requisicao))
            mensagem = pickle.loads(adversarioSocket.recv(2048))

            if mensagem["acao"] == "SOLICITACAO" and mensagem["code"] == "GAME_ACK":
                print()   
                print("Convite aceito!")
                print()

                ip_2 = adversarioSocket.getpeername()[0]
                porta_2 = adversarioSocket.getpeername()[1]

                requisicao = {
                    "acao": "GAME_ACK",
                    "data": {
                        "id": str(id),
                        "ip_1": clientSocket.getsockname()[0],
                        "porta_1": conviteSocket.getsockname()[1],
                        "ip_2": adversarioSocket.getpeername()[0],
                        "porta_2": adversarioSocket.getpeername()[1]
                    }
                }

                clientSocket.send(json.dumps(requisicao).encode("utf-8"))
            elif mensagem["acao"] == "SOLICITACAO" and mensagem["code"] == "GAME_NEG":
                print()
                print("Convite recusado!")
                print()

                continue

            mensagem = adversarioSocket.recv(2048)
            mensagem = pickle.loads(mensagem)

            ganhador = False
            gameOver = False

            while not mensagem["data"]["concluido"]:
                requisicao = {
                    "acao": "SOLICITACAO",
                    "code": "JOGANDO",
                    "data": {
                        "palavra": mensagem["data"]["palavra"],
                        "acertos": mensagem["data"]["acertos"],
                        "chutes": mensagem["data"]["chutes"],
                        "concluido": mensagem["data"]["concluido"],
                    }
                }

                print()
                print(mensagem["data"]["acertos"])
                print()

                letra = input("Sua vez de jogar... escolha uma letra: ")

                if letra == "GAME_OVER":
                    gameOver = True

                    print()
                    print("Você desistiu")
                    print()

                if not gameOver:
                    requisicao["data"]["chutes"].add(letra)

                    for i in range(len(mensagem["data"]["palavra"])):
                        if mensagem["data"]["palavra"][i] == letra:
                            requisicao["data"]["acertos"][i] = letra
                    
                    if requisicao["data"]["acertos"].count("_") < 1:
                        requisicao["data"]["concluido"] =  True
                        ganhador = True

                        adversarioSocket.send(pickle.dumps(requisicao))
                        adversarioSocket.close()

                        break
                    
                    adversarioSocket.send(pickle.dumps(requisicao))

                    print("Aguardando jogador adversário...")

                    mensagem = adversarioSocket.recv(2048)
                    mensagem = pickle.loads(mensagem)
                else:
                    requisicao = {
                        "acao": "SOLICITACAO",
                        "code": "GAME_OVER",
                        "data": {
                            "id": str(id),
                            "ip_1": clientSocket.getsockname()[0],
                            "porta_1": conviteSocket.getsockname()[1],
                            "ip_2": adversarioSocket.getpeername()[0],
                            "porta_2": adversarioSocket.getpeername()[1]
                        }
                    }

                    adversarioSocket.send(pickle.dumps(requisicao))
                    adversarioSocket.close()
                    break

            if not gameOver and ganhador:
                print()
                print("*" * 35)
                print("*****Você ganhou... parabéns!!*****")
                print("*" * 35)
                print()

                requisicao = {
                    "acao": "GAME_OVER",
                    "data": {
                        "id": str(id),
                        "ip_1": clientSocket.getsockname()[0],
                        "porta_1": conviteSocket.getsockname()[1],
                        "ip_2": ip_2,
                        "porta_2": porta_2
                    }
                }

                clientSocket.send(json.dumps(requisicao).encode("utf-8"))
            elif not gameOver and not ganhador:
                print()
                print("*" * 35)
                print("*Você perdeu... tente novamente :(*")
                print("*" * 35)
                print()

                requisicao = {
                    "acao": "GAME_OVER",
                    "data": {
                        "id": str(id),
                        "ip_1": clientSocket.getsockname()[0],
                        "porta_1": conviteSocket.getsockname()[1],
                        "ip_2": ip_2,
                        "porta_2": porta_2
                    }
                }

                clientSocket.send(json.dumps(requisicao).encode("utf-8"))
        elif opcao == "4":
            requisicao = {
                "acao": "DESCONECTAR",
                "data": {
                    "porta": conviteSocket.getsockname()[1]
                }
            }

            clientSocket.send(json.dumps(requisicao).encode("utf-8"))
            conviteSocket.close()
            clientSocket.close()
            exit(0)
        elif opcao == "sim":
            conexao[2] = True
            event.clear()
        elif opcao == "nao":
            conexao[2] = False
            event.clear()
        else:
            print("Selecione uma opção válida!")
    
    clientSocket.close()

main()