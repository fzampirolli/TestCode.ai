import abc from ABC, abstractmethod

class Disciplina:
    def __init__(self, nome):
        self.nome = nome

class Curso(ABC):
    def __init__(self, nome, duracao):
        self.nome = nome
        self.duracao = duracao
        self.disciplinas = []
        
        if duracao < 0:
            raise ValueError("Duração inválida")
        
    @abstractmethod
    def calcular_carga_horaria(self):
        pass
    
class Graduacao(Curso):
    def __init__(self, nome, duracao):
        super().__init__(nome, duracao)
        
    def calcular_carga_horaria(self):
        carga = self.duracao * 200
        print(f"Carga horária: {carga}")
        
    def adicionar_disciplina(self, disciplina: Disciplina):
        self.disciplinas.append(disciplina.nome)
    
class PosGraduacao(Curso):
    def __init__(self, nome, duracao):
        super().__init__(nome, duracao)
        
    def calcular_carga_horaria(self):
        carga = self.duracao * 134
        print(f"Carga horária: {carga}")
        
    def adicionar_disciplina(disciplina: Disciplina):
        self.disciplinas.append(disciplina.nome)
        
