from socket import *
import json
from threading import Thread
import pickle
from datetime import datetime

#Carrega o arquivo usuarios.json da memória
with open('usuarios.json', 'r') as usuariosInput:
    usuariosCadastrados = json.load(usuariosInput)

#Carrega o arquivo usuarios.json da memória
with open('usuarios-autenticados.json', 'r') as usuariosInput:
    usuariosAutenticados = json.load(usuariosInput)

#Carrega o arquivo usuarios.json da memória
with open('usuarios-jogando.json', 'r') as usuariosInput:
    usuariosJogando = json.load(usuariosInput)

# with open('game.log', 'r') as usuariosInput:
#     gameLogFile = json.load(usuariosInput)

#Função responsável por capturar o sinal de crtl + c.
def sigint(connectionSocket):
    address = connectionSocket.getpeername()
    connectionSocket.close()

    for i in range(len(usuariosAutenticados)):
        autenticado = usuariosAutenticados[i]

        if autenticado['ip'] == address[0] and autenticado['porta'] == address[1]:
            usuariosAutenticados.remove(i)

            with open("usuarios-autenticados.json", "w") as autenticadosOutput:
                json.dump(usuariosAutenticados, autenticadosOutput)

            break

    exit(0)

#Função responsável por autenticar os usuários cadastrados no sistema, esses usuários estão salvos no
#arquivo usuários autenticados.json.
def autenticar(connectionSocket, usuario, porta):
    for usuarioCadastrado in usuariosCadastrados:
        if usuario['usuario'] == usuarioCadastrado['usuario'] and usuario['senha'] == usuarioCadastrado['senha']:
            inativo =  {
                "usuario": usuario["usuario"],
                "status": "INATIVO",
                "ip": connectionSocket.getpeername()[0],
                "porta": porta,
            }

            usuariosAutenticados.append(inativo)

            with open("usuarios-autenticados.json", "w") as autenticadosOutput:
                json.dump(usuariosAutenticados, autenticadosOutput)

            resposta = {
                "acao": "AUTENTICAR",
                "code": "OK"
            }

            now = datetime.now()
            date_time = now.strftime("%d/%m/%Y, %H:%M:%S")
            gameLogFile = open("game.log", "a")
            gameLogFile.write("%s: Usuário %s conectou-se\n" % (date_time, usuario["usuario"]))
            gameLogFile.close()

            now = datetime.now()
            date_time = now.strftime("%d/%m/%Y, %H:%M:%S")
            gameLogFile = open("game.log", "a")
            gameLogFile.write("%s: Usuário %s tornou-se INATIVO\n" % (date_time, usuario["usuario"]))
            gameLogFile.close()

            break
        else:
            resposta = {
                "acao": "AUTENTICAR",
                "code": "UNAUTHORIZED"
            }

    connectionSocket.send(json.dumps(resposta).encode("utf-8"))

#Função resposável por registrar o novo usuário e salvar no arquivo usuários.json
def registrar(connectionSocket, usuario):
    usuariosCadastrados.append(usuario)

    with open("usuarios.json", "w") as usuariosOutput:
        json.dump(usuariosCadastrados, usuariosOutput)

    resposta = {
        "acao": "REGISTRAR",
        "code": "OK"
    }

    now = datetime.now()
    date_time = now.strftime("%d/%m/%Y, %H:%M:%S")
    gameLogFile = open("game.log", "a")
    gameLogFile.write("%s: Usuário %s realizou cadastro\n" % (date_time, usuario["usuario"]))
    gameLogFile.close()
    
    connectionSocket.send(json.dumps(resposta).encode("utf-8"))

#Função responsável por listar os usuários que estão online atualmente.
def listarUsuariosOnline(connectionSocket):
    listaUsuariosOnline = [usuario for usuario in usuariosAutenticados if usuario['status'] == 'INATIVO']

    resposta = {
        "acao": "LISTAR_USUARIOS_ONLINE",
        "code": "OK",
        "data": listaUsuariosOnline
    }

    connectionSocket.send(json.dumps(resposta).encode("utf-8"))

#Função responsável por listar os usuários online, esses usuários estão salvos
#no arquivo usuarios-jogando.json
def listarUsuariosJogando(connectionSocket):
    listaUsuariosJogando = [partida for partida in usuariosJogando]

    resposta = {
        "acao": "LISTAR_USUARIOS_JOGANDO",
        "code": "OK",
        "data": listaUsuariosJogando
    }

    connectionSocket.send(json.dumps(resposta).encode("utf-8"))

#Função responsável por inserir o usuário que iniciou um jogo no arquivo de usuarios-jogando.json
def inserirJogadorJogando(connectionSocket, data):
    for usuario in usuariosAutenticados:
        print(usuario["ip"], usuario["porta"])
        print(data)
        if data["ip_1"] == usuario["ip"] and data["porta_1"] == usuario["porta"]:
            usuario["status"] = "ATIVO"
            usuario1 = usuario["usuario"]

            now = datetime.now()
            date_time = now.strftime("%d/%m/%Y, %H:%M:%S")
            gameLogFile = open("game.log", "a")
            gameLogFile.write("%s: Usuário %s tornou-se ATIVO\n" % (date_time, usuario1))
            gameLogFile.close()
        
        if data["ip_2"] == usuario["ip"] and data["porta_2"] == usuario["porta"]:
            usuario["status"] = "ATIVO"
            usuario2 = usuario["usuario"]

            now = datetime.now()
            date_time = now.strftime("%d/%m/%Y, %H:%M:%S")
            gameLogFile = open("game.log", "a")
            gameLogFile.write("%s: Usuário %s tornou-se ATIVO\n" % (date_time, usuario2))
            gameLogFile.close()
    
    now = datetime.now()
    date_time = now.strftime("%d/%m/%Y, %H:%M:%S")
    gameLogFile = open("game.log", "a")
    gameLogFile.write("%s: Usuários %s e %s: PLAYING\n" % (date_time, usuario1, usuario2))
    gameLogFile.close()
    
    with open("usuarios-autenticados.json", "w") as autenticadosOutput:
        json.dump(usuariosAutenticados, autenticadosOutput)
    
    partida = {
        "id": data["id"],
        "jogador_1": {
            "usuario": usuario1,
            "ip": data["ip_1"],
            "porta": data["porta_1"],
        },
        
        "jogador_2": {
            "usuario": usuario2,
            "ip": data['ip_2'] ,
            "porta": data['porta_2'],
        }
    }

    usuariosJogando.append(partida)

    with open("usuarios-jogando.json", "w") as jogandoOutput:
        json.dump(usuariosJogando, jogandoOutput)


#Função responsável implementar o comando de GAME_OVER.
def gameOver(connectionSocker, data):
    for partida in usuariosJogando:
        if partida["id"] == data["id"]:
            usuariosJogando.remove(partida)
    
    with open("usuarios-jogando.json", "w") as jogandoOutput:
        json.dump(usuariosJogando, jogandoOutput)

    for usuario in usuariosAutenticados:
        print(usuario["ip"], usuario["porta"])
        print(data)
        if data["ip_1"] == usuario["ip"] and data["porta_1"] == usuario["porta"]:
            usuario["status"] = "INATIVO"

            now = datetime.now()
            date_time = now.strftime("%d/%m/%Y, %H:%M:%S")
            gameLogFile = open("game.log", "a")
            gameLogFile.write("%s: Usuário %s tornou-se INATIVO\n" % (date_time, usuario["usuario"]))
            gameLogFile.close()
        
        if data["ip_2"] == usuario["ip"] and data["porta_2"] == usuario["porta"]:
            usuario["status"] = "INATIVO"

            now = datetime.now()
            date_time = now.strftime("%d/%m/%Y, %H:%M:%S")
            gameLogFile = open("game.log", "a")
            gameLogFile.write("%s: Usuário %s tornou-se INATIVO\n" % (date_time, usuario["usuario"]))
            gameLogFile.close()
    
    with open("usuarios-autenticados.json", "w") as autenticadosOutput:
        json.dump(usuariosAutenticados, autenticadosOutput)


#Função responsável por desconectar o cliente.
def desconectar(connectionSocket, data):
    address = connectionSocket.getpeername()
    print(address)

    for i in range(len(usuariosAutenticados)):
        autenticado = usuariosAutenticados[i]

        if autenticado['ip'] == address[0] and autenticado['porta'] == data["porta"]:
            usuario = autenticado["usuario"]
            usuariosAutenticados.remove(autenticado)

            with open("usuarios-autenticados.json", "w") as autenticadosOutput:
                json.dump(usuariosAutenticados, autenticadosOutput)

            break

    now = datetime.now()
    date_time = now.strftime("%d/%m/%Y, %H:%M:%S")
    gameLogFile = open("game.log", "a")
    gameLogFile.write("%s: Usuário %s desconectou-se da rede\n" % (date_time, usuario))
    gameLogFile.close()
    
    connectionSocket.close()

    exit(0)

#Função responsável por receber as requisições vindas do cliente.
def cliente(connectionSocket, address):
    while True:
        mensagem = connectionSocket.recv(2048)
        mensagem = json.loads(mensagem.decode("utf-8"))
        
        if mensagem["acao"] == "REGISTRAR":
            registrar(connectionSocket, mensagem["data"])
        elif mensagem["acao"] == "AUTENTICAR":
            autenticar(connectionSocket, mensagem["data"], mensagem["porta"])
        elif mensagem["acao"] == "SIGINT":
            sigint(connectionSocket)
        elif mensagem["acao"] == "LISTAR_USUARIOS_ONLINE":
            listarUsuariosOnline(connectionSocket)
        elif mensagem["acao"] == "LISTAR_USUARIOS_JOGANDO":
            listarUsuariosJogando(connectionSocket)
        elif mensagem["acao"] == "GAME_ACK":
            inserirJogadorJogando(connectionSocket, mensagem["data"])
        elif mensagem["acao"] == "GAME_OVER":
            gameOver(connectionSocket, mensagem["data"])
        elif mensagem["acao"] == "DESCONECTAR":
            desconectar(connectionSocket, mensagem["data"])

def main():
    serverPort = 12000
    serverSocket = socket(AF_INET,SOCK_STREAM)
    serverSocket.bind(("",serverPort))
    serverSocket.listen(1)

    while True:
        connectionSocket, address = serverSocket.accept()
        new_thread = Thread(target = cliente, args = (connectionSocket, address))
        new_thread.start()

main()