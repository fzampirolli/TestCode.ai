import sys
from abc import ABC, abstractmethod

class Funcionario:
    
    def __init__(self, nome, salario):
        
        self.nome = nome
        self.salario = salario
        self.listaprojetos = []
        
        if salario<0:
            raise ValueError("Salário inválido")
        
    @abstractmethod
    def calcular_bonus(self):
        pass
    
    def adicionar_projeto(self, projeto):
        self.listaprojetos.append(projeto.nome)
        
    
    
class Desenvolvedor(Funcionario):
    
    def calcular_bonus(self):
        return self.salario*0.11
    
class Gerente(Funcionario):
    
    def calcular_bonus(self):
        return self.salario*0.21
        
class Projeto:
    
    def __init__(self):
        self.nome = nome
        
entrada = input().split("; ")
nome = entrada[0].strip()
salario = entrada[1].strip()
tipo = entrada[2].strip().lower

if tipo == "Gerente":
    funcionario = Gerente(nome,salario)
elif tipo == "Desenvolvedor":
    funcionario = Desenvolvedor(nome, salario)
else:
    print(f"Funcionario não encontrado")

linha_projetos = input().strip()
if linha_projetos:
    nomes = linha_projetos.split("; ")
    for nomes_eq in nomes:
        projeto = Projeto(nomes_eq.strip())
        funcionario.adicionar_projeto(projeto)
        

        
    
        
    
    