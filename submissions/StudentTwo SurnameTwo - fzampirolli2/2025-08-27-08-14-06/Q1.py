class CentralNotificacoes:
    _instancia = None
    
    def __new__(cls):
        if cls._instancia == None:
            cls._instancia = super().__new__(cls)
            cls._instancia.msg = ["Nova Conexão"]
            print("Central iniciada")
            
        else:
            print("Central já ativa")
            
        return _instancia
    def adicionar(self, msg):
        self.msg.append(msg)
        print(f"Nova notificação: {msg}")
    
    def listar(self):
        for msg in self.msg:
            print(f"{msg}")
            
msg = input()
comando = input()

app = CentralNotificacoes()

if comando == "adicionar":
    app.adicionar(msg)
    
elif comando == "listar":
    app.adicionar(msg)
    app.listar()
    
elif comando == "nova_instancia":
    app = CentralNotificacoes()