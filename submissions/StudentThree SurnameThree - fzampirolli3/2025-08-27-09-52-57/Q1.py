class AudioManager:
    _unique_instance = None

    def __new__(cls):
        if cls._unique_instance is None:
            cls._unique_instance = super().__new__(cls)
            cls._unique_instance._current_track = None
            print("Módulo de áudio inicializado")
        else:
            print("Módulo de áudio já em uso")
        return cls._unique_instance

    def reproduzir(self, faixa):
        self._current_track = faixa
        print(f"Reproduzindo: {faixa}")

    def status(self):
        if self._current_track:
            print(f"Faixa em execução: {self._current_track}")
        else:
            print("Nenhuma faixa em execução no momento")


# Execução principal
if __name__ == "__main__":
    player = AudioManager()
    entrada = input().strip()
    comando = input().strip()

    if comando == "reproduzir":
        player.reproduzir(entrada)
    elif comando == "status":
        player.reproduzir(entrada)
        player.status()
    elif comando == "nova_instancia":
        player = AudioManager()
    else:
        print("Comando não reconhecido")
        exit(1)
