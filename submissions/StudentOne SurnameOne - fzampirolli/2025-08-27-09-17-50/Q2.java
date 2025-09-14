import java.io.*;
import java.util.*;

public class Q2 {
    
    
    public abstract static class Curso {
        String nome;
        int duracao; // semestres
        List<Disciplina> disciplinas = new ArrayList<>();
        
        public abstract int calcularCargaHoraria();
        public Curso(String nome, int duracao){
            if(duracao < 0){
                throw new ValueError();
            }
            this.nome = nome; this.duracao = duracao;
        }
        public void adicionarDisciplina(Disciplina d){
            disciplinas.add(d);
        }
        public void printData(){
            System.out.println("Carga horária: " + calcularCargaHoraria());
            String disc = "Disciplinas: ";
            for(int i = 0; i < disciplinas.size(); i++){
                Disciplina d = disciplinas.get(i);
                disc += d.nome;
                if(i < disciplinas.size() - 1){
                    disc += "; ";
                }
            }
            System.out.println(disc);
        }
    }
    
    public static class Graduacao extends Curso{
        public Graduacao(String nome, int duracao){
            super(nome,duracao);
            System.out.println("Graduação criada");
        }
        
        public int calcularCargaHoraria(){
            return duracao * 184;
        }
    }
    
    public static class PosGraduacao extends Curso{
        public PosGraduacao(String nome, int duracao){
            super(nome,duracao);
            System.out.println("Pós-graduação criada");
        }
        
        public int calcularCargaHoraria(){
            return duracao * 137;
        }
    }
    
    public static class Disciplina{
        String nome;
        public Disciplina(String nome){
            this.nome = nome;
        }
    }
    
    public static class ValueError extends RuntimeException{ //presumo que seja uma excessão nativa em python
        public ValueError(){
            super("ValueError: Duração inválida");
        }
    }
    
    public static void main(String args[]) throws IOException {
        BufferedReader r = new BufferedReader(new InputStreamReader(System.in));
        String[] cursoData = r.readLine().split("; ");
        try{ 
            int h = Integer.parseInt(cursoData[1]);        
            Curso curso = cursoData[2].equals("pos") ? new PosGraduacao(cursoData[0],h) : new Graduacao(cursoData[0],h);
            String[] discData = r.readLine().split("; "); 
            for(String disc : discData){
                Disciplina d = new Disciplina(disc);
                curso.adicionarDisciplina(d);
            }
            
            curso.printData();
        } catch (ValueError e){
            System.out.println(e);
        }
    }
}