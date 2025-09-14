import java.io.*;
import java.util.*;

public class Q1{
    
    public static class CentralNotificacoes{
        
        // o teste 4 me parece estar com as saidas erradas, ele pede 'alerta de bateria'
        // mas o usuario nunca da input de alerta de bateria
        
        static CentralNotificacoes instance = null;
        
        ArrayList<String> notificacoes = new ArrayList<>();
        
        private CentralNotificacoes(){
            
        }
        
        public static CentralNotificacoes getInstance(){
            if(instance ==  null){
                instance = new CentralNotificacoes();
                System.out.println("Central iniciada");
            } else {
                System.out.println("Central já ativa");
            }
            return instance;
        }
        
        public void listar(){
            System.out.println("Notificações:");
            for (String notif : notificacoes){
                System.out.println(notif);
            }
        }
        
        public void adicionar(String notif){
            System.out.println("Nova notificação: " + notif);
            notificacoes.add(notif);
        }
    }
    
    public static void main(String args[]) throws IOException {
        BufferedReader r = new BufferedReader(new InputStreamReader(System.in));
        String notif = r.readLine();
        CentralNotificacoes instance = CentralNotificacoes.getInstance();
        
        while(r.ready()){
            switch(r.readLine()){
                case "nova_instancia": CentralNotificacoes.getInstance(); break;
                case "adicionar": instance.adicionar(notif); break;
            }   
        }
    }
}