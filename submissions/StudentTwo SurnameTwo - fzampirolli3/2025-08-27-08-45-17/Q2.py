from abc import ABC, abstractmethod

class Disciplina:
    def __init__(self, nome):
        self.nome = nome

class Curso(ABC):
    def __init__(self, nome, duracao: int):
        self.nome = nome
        self.duracao = duracao
        self.disciplinas = []
        
        if self.duracao < 0:
            raise ValueError("Duração inválida")
        
    @abstractmethod
    def calcular_carga_horaria(self):
        pass
    
class Graduacao(Curso):
    def __init__(self, nome, duracao: int):
        super().__init__(nome, duracao)
        
    def calcular_carga_horaria(self):
        carga = self.duracao * 200
        print(f"Carga horária: {carga}")
        
    def adicionar_disciplina(self, disciplina: Disciplina):
        self.disciplinas.append(disciplina.nome)
    
class PosGraduacao(Curso):
    def __init__(self, nome, duracao: int):
        super().__init__(nome, duracao)
        
    def calcular_carga_horaria(self):
        carga = self.duracao * 134
        print(f"Carga horária: {carga}")
        
    def adicionar_disciplina(disciplina: Disciplina):
        self.disciplinas.append(disciplina.nome)
        
nome, duracao, tipo = input().split("; ")
duracao_int = int(duracao)

if tipo == "graduacao":
    curso = Graduacao(nome, duracao_int)
    print("Graduação criada")
    
elif tipo == "pos":
    curso = PosGraduacao(nome, duracao_int)
    print("Pós-graduação criada")
    
curso.calcular_carga_horaria()

entradas_d = input().split("; ")