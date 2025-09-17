import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

/**
 * Exemplo de hierarquia de cursos usando herança e classe abstrata.
 */
public class Q2 {

    // Classe base abstrata
    public abstract static class Curso {
        protected String titulo;
        protected int duracaoSemestres;
        protected List<UnidadeCurricular> unidades;

        public Curso(String titulo, int duracaoSemestres) {
            if (duracaoSemestres < 0) {
                throw new DuracaoInvalidaException();
            }
            this.titulo = titulo;
            this.duracaoSemestres = duracaoSemestres;
            this.unidades = new ArrayList<>();
        }

        // Método abstrato para cálculo de carga horária
        public abstract int obterCargaHoraria();

        // Adiciona disciplina ao curso
        public void incluirUnidade(UnidadeCurricular uc) {
            unidades.add(uc);
        }

        // Exibe informações do curso
        public void apresentar() {
            System.out.println("Carga horária total: " + obterCargaHoraria());
            StringBuilder buffer = new StringBuilder("Componentes curriculares: ");
            for (int i = 0; i < unidades.size(); i++) {
                buffer.append(unidades.get(i).rotulo);
                if (i < unidades.size() - 1) {
                    buffer.append("; ");
                }
            }
            System.out.println(buffer);
        }
    }

    // Curso de graduação
    public static class CursoGraduacao extends Curso {
        public CursoGraduacao(String titulo, int duracaoSemestres) {
            super(titulo, duracaoSemestres);
            System.out.println("Curso de graduação criado");
        }

        @Override
        public int obterCargaHoraria() {
            return duracaoSemestres * 180;
        }
    }

    // Curso de pós-graduação
    public static class CursoPosGraduacao extends Curso {
        public CursoPosGraduacao(String titulo, int duracaoSemestres) {
            super(titulo, duracaoSemestres);
            System.out.println("Curso de pós-graduação criado");
        }

        @Override
        public int obterCargaHoraria() {
            return duracaoSemestres * 140;
        }
    }

    // Representa uma disciplina/unidade curricular
    public static class UnidadeCurricular {
        String rotulo;

        public UnidadeCurricular(String rotulo) {
            this.rotulo = rotulo;
        }
    }

    // Exceção personalizada para valores inválidos
    public static class DuracaoInvalidaException extends RuntimeException {
        public DuracaoInvalidaException() {
            super("Erro: duração informada inválida");
        }
    }

    // Programa principal
    public static void main(String[] args) throws IOException {
        BufferedReader leitor = new BufferedReader(new InputStreamReader(System.in));
        String[] dadosCurso = leitor.readLine().split("; ");
        try {
            int semestres = Integer.parseInt(dadosCurso[1]);
            Curso cursoEscolhido;

            if ("pos".equalsIgnoreCase(dadosCurso[2])) {
                cursoEscolhido = new CursoPosGraduacao(dadosCurso[0], semestres);
            } else {
                cursoEscolhido = new CursoGraduacao(dadosCurso[0], semestres);
            }

            String[] dadosDisciplinas = leitor.readLine().split("; ");
            for (String nome : dadosDisciplinas) {
                cursoEscolhido.incluirUnidade(new UnidadeCurricular(nome));
            }

            cursoEscolhido.apresentar();
        } catch (DuracaoInvalidaException e) {
            System.out.println(e.getMessage());
        }
    }
}
