import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import ssl
import os
import re
from dotenv import load_dotenv
from collections import defaultdict

# --- CORREÇÃO 1: Função agora verifica o retorno de sendmail() ---
def envia_email(servidor, porta, FROM_HEADER, LOGIN_USER, LOGIN_PASS, TO, CC=None, subject="", texto="", anexos=None) -> bool:
    if CC is None: CC = []
    if anexos is None: anexos = []

    msg = MIMEMultipart()
    msg['From'] = FROM_HEADER  # O endereço que aparece no campo "De:"
    msg['To'] = TO
    if CC:
        msg['Cc'] = ', '.join(CC)
    msg['Subject'] = subject
    msg.attach(MIMEText(texto, 'plain', 'utf-8'))

    for f_path in anexos:
        if not os.path.exists(f_path):
            print(f"    - ⚠️ Anexo não encontrado, pulando: {os.path.basename(f_path)}")
            continue
        try:
            with open(f_path, 'rb') as file:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(f_path)}"')
            msg.attach(part)
        except Exception as e:
            print(f"    - ❌ Erro ao anexar o arquivo {os.path.basename(f_path)}: {e}")
            return False

    try:
        recipients = [TO] + CC
        context = ssl.create_default_context()
        with smtplib.SMTP(servidor, porta) as server:
            server.starttls(context=context)
            server.login(LOGIN_USER, LOGIN_PASS)
            
            # Captura o dicionário de falhas retornado por sendmail
            falhas = server.sendmail(FROM_HEADER, recipients, msg.as_string())
            
            # Se o dicionário de falhas estiver vazio, o envio foi um sucesso
            if not falhas:
                return True
            else:
                # Se houver falhas, imprime o erro e retorna False
                print(f"    - ❌ Falha SMTP reportada pelo servidor: {falhas}")
                return False
                
    except Exception as e:
        # Captura outras exceções (login, conexão, etc.)
        print(f"    - ❌ Falha na conexão/envio para {TO}: {e}")
        return False


def agrupar_arquivos_por_aluno(pasta_base):
    alunos = defaultdict(lambda: {"nome": "", "arquivos": []})
    padrao = re.compile(r'^(.*?)_([a-zA-Z0-9\.]+)_([a-zA-Z]+)\.txt$')
    print(f"📁 Buscando arquivos na pasta: {pasta_base}")
    try:
        for nome_arquivo in sorted(os.listdir(pasta_base)):
            match = padrao.match(nome_arquivo)
            if match:
                nome_aluno_bruto, login, tipo_arquivo = match.groups()
                nome_aluno_limpo = nome_aluno_bruto.replace('_', ' ')
                alunos[login]['nome'] = nome_aluno_limpo
                caminho_completo = os.path.join(pasta_base, nome_arquivo)
                alunos[login]['arquivos'].append(caminho_completo)
    except FileNotFoundError:
        print(f"❌ Pasta {pasta_base} não encontrada!")
        return {}
    print(f"👥 Total de {len(alunos)} alunos encontrados.")
    return dict(alunos)


def gerar_texto_email(nome_aluno):
    texto = f"""Prezado(a) {nome_aluno},

A sua nota da Prova 1 da disciplina Programação Orientada a Objetos já está disponível no Moodle.

Em anexo, envio também dois arquivos:
1. _feedback.txt – Correção detalhada gerada automaticamente por Inteligência Artificial.
2. _prompt.txt – Texto exato enviado à IA para gerar a correção, que você pode testar em outras ferramentas, se desejar.

Ressalto que essa correção pode conter imprecisões ou erros. Utilize-a como apoio ao seu processo de aprendizagem na disciplina.

Atenciosamente,
Prof. Francisco Zampirolli
"""
    return texto


def main():
    load_dotenv('config/config.env')

    email_server = os.getenv('EMAIL_SERVER')
    email_port = int(os.getenv('EMAIL_PORT', 587))
    email_user = os.getenv('EMAIL_USER')      # Conta real usada para login SMTP
    email_pass = os.getenv('EMAIL_PASS')

    if not all([email_server, email_user, email_pass]):
        print("❌ Variáveis de ambiente EMAIL_SERVER, EMAIL_USER ou EMAIL_PASS não definidas!")
        return

    PASTA_BASE = "output/feedbacks"
    CC_EMAILS = []

    # --- CORREÇÃO 2: Define um remetente para o cabeçalho do e-mail ---
    # Este é o endereço que aparecerá no campo "De:" e para onde irão os bounces.
    # O login continua sendo feito com `email_user`.
    FROM_HEADER = f"Prof. Francisco Zampirolli <{email_user}>"

    print("🚀 Iniciando envio de feedbacks...")
    alunos_para_enviar = agrupar_arquivos_por_aluno(PASTA_BASE)

    if not alunos_para_enviar:
        print("⏹️ Nenhum aluno/arquivo encontrado.")
        return

    falhas_gerais = []

    for login, dados in sorted(alunos_para_enviar.items()):
        nome_aluno = dados['nome']
        arquivos_anexo = dados['arquivos']
        emails_a_tentar = [f"{login}@ufabc.edu.br", f"{login}@aluno.ufabc.edu.br"]

        print(f"\n📤 Processando: {nome_aluno} ({login})")
        texto_email = gerar_texto_email(nome_aluno)
        assunto = f"Feedback e Correção IA - Prova 1 - POO - {nome_aluno}"

        enviado_com_sucesso = False
        for email_destino in emails_a_tentar:
            print(f"  - Tentando enviar para: {email_destino}...")
            sucesso = envia_email(
                servidor=email_server,
                porta=email_port,
                FROM_HEADER=FROM_HEADER,    # Endereço do cabeçalho
                LOGIN_USER=email_user,      # Usuário para autenticação SMTP
                LOGIN_PASS=email_pass,
                TO=email_destino,
                CC=CC_EMAILS,
                subject=assunto,
                texto=texto_email,
                anexos=arquivos_anexo
            )
            if sucesso:
                enviado_com_sucesso = True
                nomes_anexos = [os.path.basename(f) for f in arquivos_anexo]
                print(f"  - ✅ E-mail para {email_destino} aceito pelo servidor (Anexos: {', '.join(nomes_anexos)})")
                break

        if not enviado_com_sucesso:
            falhas_gerais.append(f"{nome_aluno} ({login})")
            print(f"  - ❌ FALHA FINAL: Nenhum endereço de e-mail válido encontrado para {nome_aluno}.")

    # Salva falhas em arquivo
    if falhas_gerais:
        with open("falhas_envio.txt", "w", encoding="utf-8") as f:
            f.write("Não foi possível enviar e-mails para os seguintes alunos:\n")
            f.write("\n".join(falhas_gerais))
        print(f"\n⚠️  {len(falhas_gerais)} aluno(s) não receberam o e-mail. Veja o arquivo falhas_envio.txt")

    print("\n🎉 Processamento concluído!")


if __name__ == "__main__":
    main()