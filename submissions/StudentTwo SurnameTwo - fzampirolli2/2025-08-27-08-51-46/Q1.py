class GerenciadorMensagens:
    _unica_instancia = None

    def __new__(cls):
        if cls._unica_instancia is None:
            cls._unica_instancia = super().__new__(cls)
            cls._unica_instancia._mensagens = ["Conexão estabelecida", "Mensagem inicial"]
            print("Sistema de mensagens iniciado")
        else:
            print("Sistema de mensagens já em execução")
        return cls._unica_instancia

    def registrar(self, conteudo):
        self._mensagens.append(conteudo)
        print(f"Mensagem registrada: {conteudo}")

    def exibir(self):
        print("Mensagens armazenadas:")
        for m in self._mensagens:
            print(m)


if __name__ == "__main__":
    entrada = input().strip()
    comando = input().strip()

    sistema = GerenciadorMensagens()

    if comando == "registrar":
        sistema.registrar(entrada)
    elif comando == "exibir":
        sistema.registrar(entrada)
        sistema.exibir()
    elif comando == "nova_instancia":
        sistema = GerenciadorMensagens()
    else:
        print("Comando não reconhecido")
