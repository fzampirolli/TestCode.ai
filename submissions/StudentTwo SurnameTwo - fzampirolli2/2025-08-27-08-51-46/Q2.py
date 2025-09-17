from abc import ABC, abstractmethod

class ComponenteCurricular:
    def __init__(self, titulo):
        self.titulo = titulo

class ProgramaAcademico(ABC):
    def __init__(self, nome, semestres: int):
        if semestres < 0:
            raise ValueError("Duração inválida do programa")
        self.nome = nome
        self.semestres = semestres
        self.unidades = []

    @abstractmethod
    def calcular_carga_total(self):
        pass

class EnsinoGraduacao(ProgramaAcademico):
    def __init__(self, nome, semestres: int):
        super().__init__(nome, semestres)
        print("Programa de graduação criado")

    def calcular_carga_total(self):
        carga = self.semestres * 195
        print(f"Carga horária total: {carga}")
        return carga

    def adicionar_unidade(self, unidade: ComponenteCurricular):
        self.unidades.append(unidade.titulo)

class EnsinoPosGraduacao(ProgramaAcademico):
    def __init__(self, nome, semestres: int):
        super().__init__(nome, semestres)
        print("Programa de pós-graduação criado")

    def calcular_carga_total(self):
        carga = self.semestres * 135
        print(f"Carga horária total: {carga}")
        return carga

    def adicionar_unidade(self, unidade: ComponenteCurricular):
        self.unidades.append(unidade.titulo)


if __name__ == "__main__":
    entrada = input().split("; ")
    nome_programa = entrada[0].strip()
    duracao = int(entrada[1].strip())
    tipo_programa = entrada[2].strip().lower()

    if tipo_programa == "graduacao":
        curso = EnsinoGraduacao(nome_programa, duracao)
    elif tipo_programa == "pos":
        curso = EnsinoPosGraduacao(nome_programa, duracao)
    else:
        print("Tipo de programa não reconhecido")
        exit(1)

    curso.calcular_carga_total()

    disciplina_input = input().strip()
    disciplina = ComponenteCurricular(disciplina_input)
    curso.adicionar_unidade(disciplina)

    print(f"Componentes curriculares: {curso.unidades}")
