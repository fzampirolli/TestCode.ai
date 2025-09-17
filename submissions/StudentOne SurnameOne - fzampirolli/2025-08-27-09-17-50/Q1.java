import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;

/**
 * Implementação de um sistema de notificações com instância única (Singleton).
 */
public class Q1 {

    // Classe responsável por gerenciar notificações
    public static class GerenciadorNotificacoes {

        private static GerenciadorNotificacoes instanciaUnica;
        private final ArrayList<String> filaNotificacoes;

        private GerenciadorNotificacoes() {
            filaNotificacoes = new ArrayList<>();
        }

        // Método estático para acessar a instância única
        public static GerenciadorNotificacoes acessar() {
            if (instanciaUnica == null) {
                instanciaUnica = new GerenciadorNotificacoes();
                System.out.println("Sistema de notificações iniciado");
            } else {
                System.out.println("Sistema já em execução");
            }
            return instanciaUnica;
        }

        // Adiciona uma nova notificação
        public void incluir(String mensagem) {
            filaNotificacoes.add(mensagem);
            System.out.println("Notificação registrada: " + mensagem);
        }

        // Exibe todas as notificações armazenadas
        public void exibir() {
            System.out.println("Lista de notificações:");
            for (String msg : filaNotificacoes) {
                System.out.println(msg);
            }
        }
    }

    // Programa principal
    public static void main(String[] args) throws IOException {
        BufferedReader leitor = new BufferedReader(new InputStreamReader(System.in));
        String primeiraEntrada = leitor.readLine();
        GerenciadorNotificacoes notificacoes = GerenciadorNotificacoes.acessar();

        String comando;
        while ((comando = leitor.readLine()) != null) {
            switch (comando) {
                case "nova_instancia":
                    GerenciadorNotificacoes.acessar();
                    break;
                case "adicionar":
                    notificacoes.incluir(primeiraEntrada);
                    break;
                case "listar":
                    notificacoes.exibir();
                    break;
                default:
                    System.out.println("Comando desconhecido: " + comando);
            }
        }
    }
}
