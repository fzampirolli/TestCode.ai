import sys
class SomSistema:
    
    _instancia = None
    
    def __new__(cls):
        
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia.somp = None
            print("Gerenciador de som criado")
            
        else: 
            print("Gerenciador já existente")
            
        return cls._instancia
            
    def tocar_som (self, som):
        self.somp = som
        print(f"Tocando som: {som}")
        
    def som_atual(self):
        print(f"Som atual: {self.somp}")
        

sistema = SomSistema()
entrada = input().strip()
comando= input().strip()
sistema.tocar_som(entrada)

if comando == "tocar_som":
    sistema.tocar_som(entrada)
elif comando == "som_atual":
    sistema.som_atual()
elif comando == "nova_instancia":
    sistema = SomSistema()
else:
    print("Comando invalida")
    exit()
        
            
        