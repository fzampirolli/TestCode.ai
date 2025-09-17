from abc import ABC, abstractmethod

class Colaborador(ABC):
    def __init__(self, identificador, salario):
        if float(salario) < 0:
            raise ValueError("Valor de salário não permitido")

        self.identificador = identificador
        self.salario = float(salario)
        self._atividades = []

    @abstractmethod
    def obter_bonus(self):
        pass

    def registrar_atividade(self, atividade):
        self._atividades.append(atividade.titulo)


class Programador(Colaborador):
    def obter_bonus(self):
        return self.salario * 0.10


class Coordenador(Colaborador):
    def obter_bonus(self):
        return self.salario * 0.20


class Atividade:
    def __init__(self, titulo):
        self.titulo = titulo


if __name__ == "__main__":
    try:
        dados = input().split("; ")
        nome = dados[0].strip()
        salario = dados[1].strip()
        categoria = dados[2].strip().lower()

        if categoria == "coordenador":
            pessoa = Coordenador(nome, salario)
        elif categoria == "programador":
            pessoa = Programador(nome, salario)
        else:
            print("Categoria informada não reconhecida")
            exit(1)

        linha = input().strip()
        if linha:
            itens = linha.split("; ")
            for item in itens:
                atividade = Atividade(item.strip())
                pessoa.registrar_atividade(atividade)

        print(f"{categoria.capitalize()} registrado")
        print(f"Bônus calculado: {pessoa.obter_bonus()}")

        if pessoa._atividades:
            print(f"Atividades: {'; '.join(pessoa._atividades)}")

    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"Falha de execução: {e}")
