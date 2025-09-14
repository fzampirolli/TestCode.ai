#!/usr/bin/env python3

import os, sys, json, yaml, logging, asyncio, aiohttp, pickle, random, re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import pandas as pd
import textwrap

@dataclass
class SubmissaoAluno:
    nome: str
    login: str
    pasta: Path
    arquivos: Dict[str, Path]
    status: str = "pendente"
    nota_final: float = 0.0
    feedback: str = ""
    prompt: str = "" 
    tentativas_api: int = 0
    notas_questoes: Dict[str, float] = field(default_factory=dict)
    notas_moodle_percent: Dict[str, float] = field(default_factory=dict)
    notas_moodle_pontos: Dict[str, float] = field(default_factory=dict)
    historico_avaliacoes: List[Dict] = field(default_factory=list)

class GerenciadorAvaliacao:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._carregar_config(config_path)
        self._configurar_logging()
        self.submissoes: List[SubmissaoAluno] = []
        self.state_file = Path("output/processamento_state.pkl")
        self.retry_queue_file = Path("output/retry_queue.json")
        
        # CORRIGIDO: Carrega as configurações usando as chaves corretas do YAML ('assessment', etc.)
        assessment_config = self.config.get('assessment', {})
        self.llm_attempts = assessment_config.get('llm_attempts', 1)
        self.selection_criteria = assessment_config.get('selection_criteria', 'highest').lower()
        
        if self.selection_criteria not in ["highest", "average", "lowest"]:
            self.logger.warning(f"Critério de seleção '{self.selection_criteria}' inválido. Usando 'highest' como padrão.")
            self.selection_criteria = "highest"
        self.logger.info(f"Critério de seleção de nota final: {self.selection_criteria}")

        self.detailed_feedback = assessment_config.get('detailed_feedback', False) 
        self.logger.info(f"Modo de feedback detalhado: {'Ativado' if self.detailed_feedback else 'Desativado'}")

    def _carregar_config(self, config_path: str) -> dict:
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                print(f"Arquivo de configuração não encontrado: {config_path}")
                sys.exit(1)
                
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config:
                print("Arquivo de configuração está vazio")
                sys.exit(1)
            
            # CORRIGIDO: Usa as chaves corretas do YAML ('assessment', 'questions')
            required_keys = ['api', 'questions', 'assessment']
            for key in required_keys:
                if key not in config:
                    print(f"Chave obrigatória '{key}' não encontrada no config")
                    sys.exit(1)
            
            # CORRIGIDO: Validação para a nova configuração de tentativas com a chave correta
            if 'llm_attempts' not in config['assessment']:
                 print("Chave 'llm_attempts' não encontrada em 'assessment' no config. Usando padrão de 1.")
                 config['assessment']['llm_attempts'] = 1
            
            api_config = config.get('api', {})
            if 'url' not in api_config:
                print("'api.url' não encontrada no config")
                sys.exit(1)
                
            # CORRIGIDO: Chave 'models' em vez de 'modelos'
            if 'models' not in api_config:
                api_config['models'] = ['llama-3.1-8b-instant']
                
            print(f"Configuração carregada: {config_path}")
            return config
            
        except yaml.YAMLError as e:
            print(f"Erro ao parsear YAML: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Erro ao carregar config: {e}")
            sys.exit(1)
    
    def _configurar_logging(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"avaliacao_{timestamp}.log"
        
        logging.basicConfig(
            level=getattr(logging, self.config.get('log_level', 'INFO')),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def salvar_estado(self):
        state_dir = Path("output")
        state_dir.mkdir(exist_ok=True)
        try:
            with open(self.state_file, 'wb') as f:
                pickle.dump(self.submissoes, f)
            self.logger.info("Estado salvo")
        except Exception as e:
            self.logger.error(f"Erro ao salvar estado: {e}")
    
    def carregar_estado(self) -> bool:
        if self.state_file.exists():
            try:
                with open(self.state_file, 'rb') as f:
                    self.submissoes = pickle.load(f)
                self.logger.info(f"Estado anterior carregado: {len(self.submissoes)} submissões")
                for submissao in self.submissoes:
                    if not hasattr(submissao, 'historico_avaliacoes'):
                        submissao.historico_avaliacoes = []
                    if not hasattr(submissao, 'prompt'):
                        submissao.prompt = ""
                return True
            except Exception as e:
                self.logger.warning(f"Erro ao carregar estado: {e}")
        return False
    
    def descobrir_submissoes(self, pasta_base: str) -> List[SubmissaoAluno]:
        self.logger.info(f"Descobrindo submissões em {pasta_base}")
        
        pasta_base = Path(pasta_base)
        submissoes = []

        for pasta_aluno in sorted(pasta_base.iterdir(), key=lambda x: x.name.lower()):
            if not pasta_aluno.is_dir():
                continue
                
            nome_completo = pasta_aluno.name
            if " - " not in nome_completo:
                self.logger.warning(f"Pasta ignorada (formato inválido): {nome_completo}")
                continue
            
            nome, login = nome_completo.rsplit(" - ", 1)
            
            submissao_dir = self._encontrar_submissao_recente(pasta_aluno)
            if not submissao_dir:
                self.logger.warning(f"Nenhuma submissão encontrada para {nome}")
                continue
            
            arquivos = self._mapear_arquivos_questoes(submissao_dir)
            if not arquivos:
                self.logger.warning(f"Arquivos de questão não encontrados para {nome}")
                continue
            
            percentuais, pontos = self.extrair_notas_moodle(pasta_aluno)
            
            submissao = SubmissaoAluno(
                nome=nome,
                login=login,
                pasta=submissao_dir,
                arquivos=arquivos,
                notas_moodle_percent=percentuais,
                notas_moodle_pontos=pontos
            )
            submissoes.append(submissao)
            
        self.logger.info(f"{len(submissoes)} submissões encontradas")
        self.submissoes = submissoes
        return submissoes

    def _encontrar_submissao_recente(self, pasta_aluno: Path) -> Optional[Path]:
        submissoes = [d for d in pasta_aluno.iterdir()
                     if d.is_dir() and not d.name.endswith('.ceg')]
        if not submissoes:
            return None
        return max(submissoes, key=lambda x: x.stat().st_mtime)
    
    def _mapear_arquivos_questoes(self, submissao_dir: Path) -> Dict[str, Path]:
        arquivos = {}
        # CORRIGIDO: Usa as chaves corretas ('questions', 'accepted_extensions')
        for questao in self.config['questions']:
            questao_id = questao['id']
            extensoes = questao['accepted_extensions']
            arquivo_encontrado = None
            for ext in extensoes:
                padrao = f"{questao_id}*{ext}"
                matches = list(submissao_dir.glob(padrao))
                if matches:
                    arquivo_encontrado = matches[0]
                    break
            if arquivo_encontrado:
                arquivos[questao_id] = arquivo_encontrado
            else:
                self.logger.warning(f"Arquivo {questao_id} não encontrado em {submissao_dir}")
        return arquivos

    async def processar_submissoes(self):
        # CORRIGIDO: Usa a variável self.llm_attempts
        self.logger.info(f"Iniciando processamento. Serão feitas {self.llm_attempts} tentativa(s) de avaliação por aluno.")

        for i in range(self.llm_attempts):
            tentativa_num = i + 1
            self.logger.info(f"--- INICIANDO TENTATIVA DE AVALIAÇÃO {tentativa_num}/{self.llm_attempts} ---")
            
            await self._processar_rodada_adaptativa(self.submissoes, tentativa_num)
            
            self.salvar_estado()
            self._relatorio_rodada(tentativa_num)
            
            if tentativa_num < self.llm_attempts:
                wait_time = min(60, 10 * tentativa_num)
                self.logger.info(f"Aguardando {wait_time}s antes da próxima tentativa geral...")
                await asyncio.sleep(wait_time)
        
        self.logger.info("Todas as tentativas foram concluídas. Consolidando os resultados finais...")
        self._consolidar_resultados_finais()
        self.salvar_estado()
        self._relatorio_final()

    def _consolidar_resultados_finais(self):
        # CORRIGIDO: Usa as variáveis e critérios corretos ('llm_attempts', 'selection_criteria')
        if self.llm_attempts > 1:
            self.logger.info(f"Consolidando resultados finais usando o critério: '{self.selection_criteria}'")
        else:
            self.logger.info("Consolidando resultados finais da única tentativa.")
        
        for submissao in self.submissoes:
            if not submissao.historico_avaliacoes:
                submissao.status = "erro_sem_feedback"
                submissao.feedback = "Nenhuma avaliação bem-sucedida foi recebida da LLM."
                submissao.nota_final = 0.0
                continue

            tentativa_selecionada = None
            nota_final_consolidada = 0.0

            if self.llm_attempts > 1:
                if self.selection_criteria == "highest":
                    tentativa_selecionada = max(submissao.historico_avaliacoes, key=lambda t: t['nota_final'])
                elif self.selection_criteria == "lowest":
                    tentativa_selecionada = min(submissao.historico_avaliacoes, key=lambda t: t['nota_final'])
                elif self.selection_criteria == "average":
                    notas = [t['nota_final'] for t in submissao.historico_avaliacoes]
                    nota_final_consolidada = sum(notas) / len(notas)
                    # Encontra a tentativa mais próxima da média
                    tentativa_selecionada = min(submissao.historico_avaliacoes, key=lambda t: abs(t['nota_final'] - nota_final_consolidada))
                
                if self.selection_criteria != "average":
                    nota_final_consolidada = tentativa_selecionada['nota_final']
            else:
                tentativa_selecionada = submissao.historico_avaliacoes[0]
                nota_final_consolidada = tentativa_selecionada['nota_final']
            
            submissao.nota_final = nota_final_consolidada
            submissao.feedback = tentativa_selecionada['feedback']
            submissao.notas_questoes = tentativa_selecionada['notas_questoes']
            submissao.prompt = tentativa_selecionada.get('prompt', '')
            submissao.status = "concluido"
            
            # CORRIGIDO: Usa a variável self.selection_criteria
            log_detalhe = f"(critério: {self.selection_criteria})" if self.llm_attempts > 1 else f"(de 1 tentativa)"
            self.logger.info(f"Nota final para {submissao.nome}: {submissao.nota_final:.2f} {log_detalhe}")

    async def _processar_rodada_adaptativa(self, submissoes_da_rodada: List[SubmissaoAluno], rodada: int):
        threads = self.config.get('processing', {}).get('parallel_threads', 4)
        delay_base = 2
        
        self.logger.info(f"Rodada {rodada}: {threads} threads paralelas, delay base {delay_base}s")
        
        semaforo = asyncio.Semaphore(threads)
        async with aiohttp.ClientSession() as session:
            tasks = [self._processar_submissao_com_delay(session, semaforo, sub, delay_base * (i // threads), rodada)
                     for i, sub in enumerate(submissoes_da_rodada)]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _processar_submissao_com_delay(self, session: aiohttp.ClientSession,
                                           semaforo: asyncio.Semaphore,
                                           submissao: SubmissaoAluno,
                                           delay: int, rodada: int):
        if delay > 0:
            await asyncio.sleep(delay)
        
        async with semaforo:
            try:
                self.logger.info(f"[Tentativa {rodada}] Processando: {submissao.nome} (API call {submissao.tentativas_api + 1})")
                
                submissao.tentativas_api += 1
                prompt = self._montar_prompt(submissao)
                
                resposta, prompt_enviado = await self._chamar_api_com_retry_adaptativo(session, prompt, rodada)
                
                if resposta and len(resposta.strip()) > 50:
                    notas_q = self._extrair_notas_questoes(resposta, submissao)
                    nota_f = sum(notas_q.values()) or self._extrair_nota_final(resposta)
                    
                    resultado_tentativa = {
                        "nota_final": nota_f,
                        "feedback": resposta,
                        "notas_questoes": notas_q,
                        "tentativa_num": rodada,
                        "prompt": prompt_enviado 
                    }
                    submissao.historico_avaliacoes.append(resultado_tentativa)
                    
                    self.logger.info(f"[Tentativa {rodada}] {submissao.nome} - SUCESSO! Nota desta tentativa: {nota_f:.2f}")
                else:
                    self.logger.warning(f"[Tentativa {rodada}] {submissao.nome} - Resposta da API inválida ou vazia.")
                    
            except Exception as e:
                self.logger.error(f"[Tentativa {rodada}] {submissao.nome} - Erro inesperado: {str(e)}", exc_info=True)

    async def _chamar_api_com_retry_adaptativo(self, session: aiohttp.ClientSession,
                                             prompt: str, rodada: int) -> Tuple[Optional[str], str]:
        max_retries = 3
        api_config = self.config['api']
        timeout_base = api_config.get('timeout', 120)
        models = api_config['models']
        
        api_key = os.getenv('API_KEY') or os.getenv('GROQ_API_KEY')
        if not api_key:
            self.logger.error("API_KEY não encontrada nas variáveis de ambiente.")
            return None, prompt
        
        api_url = api_config['url']
        
        for retry in range(max_retries):
            try:
                modelo = random.choice(models)
                
                payload = {
                    "model": modelo,
                    "messages": [
                        {"role": "system", "content": "Você é um corretor de código eficiente e rigoroso."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": api_config.get('max_tokens', 4000),
                    "temperature": api_config.get('temperature', 0.1),
                    "stream": False
                }
                
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                timeout = aiohttp.ClientTimeout(total=timeout_base + (retry * 20))
                
                async with session.post(api_url, json=payload, headers=headers, timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('choices'):
                            content = data['choices'][0]['message']['content']
                            if len(content.strip()) > 50:
                                return content, prompt
                    
                    elif response.status == 429:
                        wait = min(60, 15 * (2 ** retry))
                        self.logger.warning(f"Rate limit atingido (429). Aguardando {wait}s para tentar novamente...")
                        await asyncio.sleep(wait)
                    else:
                        response_text = await response.text()
                        self.logger.error(f"Erro da API (Status {response.status}): {response_text[:200]}...")
            except Exception as e:
                self.logger.error(f"Erro na chamada à API (tentativa {retry + 1}): {e}")
            
            if retry < max_retries - 1:
                await asyncio.sleep(min(30, (3 ** retry) + random.uniform(0, 5)))
        
        return None, prompt

    def _montar_prompt(self, submissao: SubmissaoAluno) -> str:
        prompt_parts = []
        # CORRIGIDO: Usa as chaves corretas do YAML
        assessment_name = self.config['assessment']['name']
        
        if self.detailed_feedback:
            prompt_parts.append(f"""
# AVALIAÇÃO AUTOMATIZADA DETALHADA - {assessment_name}
Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## INSTRUÇÕES GERAIS
Você é um professor assistente especialista. Analise o código do aluno para cada questão COM BASE EM CADA ITEM DA RUBRICA FORNECIDA.
Forneça um feedback DETALHADO!

Para cada questão, CONSIDERANDO RIGOROSAMENTE A RUBRICA FORNECIDA:
1.  Forneça um feedback construtivo e aprofundado.
2.  Destaque os pontos positivos e onde o aluno acertou.
3.  Aponte os erros ou áreas de melhoria de forma clara.
4.  Ofereça sugestões práticas e exemplos de como o código poderia ser melhorado ou corrigido.
5.  No final da análise de cada questão, forneça a nota formatada.

PARA CADA ITEM X DA RUBRICA, explique se foi atendido ou não, e por quê:
   - ✅ CORRETO: item X atendido
   - ❌ INCORRETO: item X não atendido
   - ⚠️ PARCIALMENTE CORRETO: item X atendido parcialmente

FORMATO DE SAÍDA OBRIGATÓRIO DA NOTA DE CADA QUESTÃO:
- QUESTAO_[ID]: [NOTA]/[MAXIMO] - [comentário breve]
""")
        else:
            prompt_parts.append(f"""
# AVALIAÇÃO AUTOMATIZADA - {assessment_name}
Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## INSTRUÇÕES GERAIS
Você é um professor assistente especialista. Analise o código do aluno para cada questão COM BASE EM CADA ITEM DA RUBRICA FORNECIDA.
Forneça um feedback CONCISO!

FORMATO DE SAÍDA OBRIGATÓRIO DA NOTA DE CADA QUESTÃO:
- QUESTAO_[ID]: [NOTA]/[MAXIMO] - [comentário breve]
""")
        
        # CORRIGIDO: Usa as chaves corretas ('questions', 'rubric_file', 'max_points')
        for questao in self.config['questions']:
            questao_id = questao['id']
            if questao_id in submissao.arquivos:
                try:
                    with open(questao['rubric_file'], 'r', encoding='utf-8') as f:
                        rubrica = f.read()
                    with open(submissao.arquivos[questao_id], 'r', encoding='utf-8', errors='ignore') as f:
                        codigo = f.read()
                    
                    max_points = questao['max_points']
                    prompt_parts.append(f"""
---
## {questao['name']} ({questao_id}) - Máximo: {max_points} pontos

### RUBRICA DE AVALIAÇÃO:
{rubrica}

### CÓDIGO SUBMETIDO PELO ALUNO:
{codigo}

Lembre-se de incluir a linha: QUESTAO_{questao_id}: [NOTA]/{max_points} - [comentário]
""")
                except Exception as e:
                    self.logger.warning(f"Erro ao ler arquivos para {questao_id}: {e}")
        
        return '\n'.join(prompt_parts)

    def _extrair_notas_questoes(self, feedback: str, submissao: SubmissaoAluno) -> Dict[str, float]:
        notas = {}
        padrao_questao = r'QUESTAO_(\w+):\s*(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)'
        matches = re.findall(padrao_questao, feedback, re.IGNORECASE | re.MULTILINE)
        for questao_id, nota_str, maximo_str in matches:
            try:
                nota, maximo = float(nota_str), float(maximo_str)
                if 0 <= nota <= maximo:
                    notas[questao_id] = nota
                else:
                    self.logger.warning(f"Nota inválida para {questao_id}: {nota}/{maximo}")
            except ValueError as e:
                self.logger.warning(f"Erro ao converter nota {questao_id}: {e}")
        return notas
    
    def extrair_notas_moodle(self, pasta_aluno: Path) -> Tuple[Dict[str, float], Dict[str, float]]:
        arquivo_execution = self._encontrar_arquivo_execution(pasta_aluno)
        if not arquivo_execution or not arquivo_execution.exists():
            return {}, {}

        import re

        notas_percentuais, questao_atual = {}, None
        nota_final = None

        try:
            with open(arquivo_execution, 'r', encoding='utf-8', errors='ignore') as f:
                for linha in f:
                    linha = linha.strip()

                    # Detecta início de questão
                    match_questao = re.search(r'-\s*Question\s*(\d+):', linha, re.IGNORECASE)
                    if match_questao:
                        questao_atual = f"Q{match_questao.group(1)}"
                        continue

                    # Captura percentual da questão
                    if questao_atual:
                        match_completa = re.search(r'\(([0-9]+(?:\.[0-9]+)?)%\)', linha)
                        if match_completa:
                            notas_percentuais[questao_atual] = float(match_completa.group(1))
                            questao_atual = None  # Próxima questão

                    # Captura nota final
                    match_final = re.search(r'Grade\s*:=>>\s*([0-9]+(?:\.[0-9]+)?)', linha)
                    if match_final:
                        nota_final = float(match_final.group(1))

            notas_pontos = self._converter_percentuais_para_pontos(notas_percentuais)

            # Se quiser, adiciona a nota final como 'Final'
            if nota_final is not None:
                notas_percentuais['Final'] = nota_final
                notas_pontos['Final'] = nota_final  # ou converter se necessário

            return notas_percentuais, notas_pontos

        except Exception as e:
            self.logger.error(f"Erro ao ler execution.txt: {e}")
            return {}, {}



    def _converter_percentuais_para_pontos(self, percentuais: Dict[str, float]) -> Dict[str, float]:
        pontos = {}
        # CORRIGIDO: Usa as chaves corretas ('questions', 'max_points')
        pesos_questoes = {q['id']: q['max_points'] for q in self.config['questions']}
        for questao_id, percentual in percentuais.items():
            if questao_id in pesos_questoes:
                pontos[questao_id] = round((percentual / 100.0) * pesos_questoes[questao_id], 2)
        return pontos
    
    def _encontrar_arquivo_execution(self, pasta_submissao: Path) -> Optional[Path]:
        try:
            pastas_ceg = [p for p in pasta_submissao.iterdir() if p.is_dir() and p.name.endswith('.ceg')]
            if not pastas_ceg:
                arquivo_direto = pasta_submissao / "execution.txt"
                return arquivo_direto if arquivo_direto.exists() else None
            pasta_ceg_recente = max(pastas_ceg, key=lambda x: x.stat().st_mtime)
            arquivo_execution = pasta_ceg_recente / "execution.txt"
            return arquivo_execution if arquivo_execution.exists() else None
        except Exception: return None

    def _relatorio_rodada(self, rodada: int):
        sucessos_rodada = sum(1 for s in self.submissoes if any(t['tentativa_num'] == rodada for t in s.historico_avaliacoes))
        self.logger.info(f"TENTATIVA {rodada} COMPLETA:")
        self.logger.info(f"   Avaliações bem-sucedidas nesta tentativa: {sucessos_rodada}/{len(self.submissoes)}")
        if len(self.submissoes) > 0:
            self.logger.info(f"   Taxa de sucesso da tentativa: {sucessos_rodada/len(self.submissoes)*100:.1f}%")
    
    def _relatorio_final(self):
        concluidos = [s for s in self.submissoes if s.status == "concluido"]
        pendentes = [s for s in self.submissoes if s.status != "concluido"]
        
        print("\n" + "="*80)
        print("RELATÓRIO FINAL DO PROCESSAMENTO")
        print("="*80)
        print(f"Processados com sucesso (obtiveram pelo menos 1 avaliação da IA): {len(concluidos)}")
        print(f"Não processados (nenhuma avaliação da IA): {len(pendentes)}")
        if self.submissoes:
            print(f"Taxa de sucesso final: {len(concluidos)/len(self.submissoes)*100:.1f}%")
        
        if pendentes:
            print(f"\nSUBMISSÕES COM FALHA FINAL:")
            for s in pendentes:
                print(f"   • {s.nome} (API calls: {s.tentativas_api})")
        
        print("="*80 + "\n")
        self.salvar_feedbacks_finais()

    def salvar_feedbacks_finais(self):
        self.logger.info("Salvando arquivos de feedback e prompt finais...")
        output_dir = Path("output") / "feedbacks"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for submissao in self.submissoes:
            if submissao.status != "concluido":
                continue
            
            if submissao.prompt:
                arquivo_prompt  = output_dir / f"{submissao.nome}_{submissao.login}_prompt.txt"
                with open(arquivo_prompt, 'w', encoding='utf-8') as f:
                    f.write(submissao.prompt)

            num_tentativas_reais = len(submissao.historico_avaliacoes)
            mensagem_explicativa = ""
            titulo_nota = ""

            if num_tentativas_reais > 1:
                # CORRIGIDO: Usa self.selection_criteria e adapta as strings
                criterio_str = self.selection_criteria.upper()
                titulo_nota = f"Nota Final ({criterio_str} de {num_tentativas_reais} tentativas): {submissao.nota_final:.2f} pontos"
                
                detalhe_feedback = ""
                if self.selection_criteria == "highest":
                    detalhe_feedback = "à tentativa com a MAIOR nota"
                elif self.selection_criteria == "lowest":
                    detalhe_feedback = "à tentativa com a MENOR nota"
                elif self.selection_criteria == "average":
                    detalhe_feedback = "à tentativa com a nota MAIS PRÓXIMA DA MÉDIA"
                
                texto_observacao = (
                    f"Observação: A 'Nota Final' é o resultado do critério '{criterio_str}' aplicado a {num_tentativas_reais} tentativas. "
                    f"O feedback detalhado e as notas por questão abaixo referem-se especificamente {detalhe_feedback}."
                )
                mensagem_explicativa = textwrap.fill(texto_observacao, width=100) + "\n\n"
            else:
                titulo_nota = f"Nota Final (de {num_tentativas_reais} tentativa): {submissao.nota_final:.2f} pontos"
            
            paragrafos_formatados = [textwrap.fill(p, width=100) for p in submissao.feedback.split('\n')]
            feedback_formatado = "\n".join(paragrafos_formatados)
            
            arquivo_feedback = output_dir / f"{submissao.nome}_{submissao.login}_feedback.txt"
            with open(arquivo_feedback, 'w', encoding='utf-8') as f:
                f.write(f"""
FEEDBACK DA AVALIAÇÃO - {self.config['assessment']['name']}
═══════════════════════════════════════════════════════════
Aluno: {submissao.nome} ({submissao.login})
Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{titulo_nota}
Total de Chamadas à API: {submissao.tentativas_api}

{mensagem_explicativa}{feedback_formatado}

═══════════════════════════════════════════════════════════
Este feedback foi gerado automaticamente por IA e pode
necessitar de revisão pelo professor.
""")
   
    def _extrair_nota_final(self, feedback: str) -> float:
        padroes = [
            r'NOTA FINAL[:\s]+(\d+(?:\.\d+)?)', r'Total[:\s]+(\d+(?:\.\d+)?)',
            r'Pontuação[:\s]+(\d+(?:\.\d+)?)'
        ]
        for padrao in padroes:
            match = re.search(padrao, feedback, re.IGNORECASE)
            if match: return float(match.group(1))
        return 0.0
    
    def gerar_relatorio_consolidado(self):
        self.logger.info("Gerando relatório consolidado detalhado...")
        # CORRIGIDO: Usa a chave 'questions'
        dados, questoes_config = [], {q['id']: q for q in self.config['questions']}
        for sub in self.submissoes:
            linha = {'Nome': sub.nome, 'Login': sub.login, 'Status': sub.status, 'Nota_Final_IA': sub.nota_final,
                     'Tentativas_API': sub.tentativas_api, 'Num_Avaliacoes_OK': len(sub.historico_avaliacoes)}
            for q_id in questoes_config:
                ia_p = sub.notas_questoes.get(q_id, 0.0)
                moodle_p = sub.notas_moodle_pontos.get(q_id, 0.0)
                linha.update({f"{q_id}_IA_Pontos": ia_p, f"{q_id}_Moodle_Pontos": moodle_p,
                              f"{q_id}_Moodle_Percent": sub.notas_moodle_percent.get(q_id, 0.0),
                              f"{q_id}_Diferenca": round(ia_p - moodle_p, 2)})
            total_moodle = sum(sub.notas_moodle_pontos.values())
            linha.update({'Nota_Final_Moodle': total_moodle, 'Diferenca_Total': round(sub.nota_final - total_moodle, 2)})
            dados.append(linha)
        if not dados: return self.logger.warning("Nenhum dado para gerar relatório.")
        df = pd.DataFrame(dados)
        stats = self._calcular_estatisticas_detalhadas(df, questoes_config)
        self._salvar_excel_completo(df, stats, questoes_config)
        self._exibir_relatorio_console(stats, questoes_config)

    def _calcular_estatisticas_detalhadas(self, df: pd.DataFrame, questoes_config: Dict) -> Dict:
        df.fillna(0, inplace=True)
        stats = {'geral': {'total_alunos': len(df), 'processados': len(df[df['Status'] == 'concluido']),
                 'media_ia': df['Nota_Final_IA'].mean(), 'media_moodle': df['Nota_Final_Moodle'].mean(),
                 'desvio_ia': df['Nota_Final_IA'].std(), 'desvio_moodle': df['Nota_Final_Moodle'].std(),
                 'correlacao_total': df['Nota_Final_IA'].corr(df['Nota_Final_Moodle']) if len(df) > 1 else 0.0,
                 'diferenca_media': df['Diferenca_Total'].mean()}, 'questoes': {}}
        for q_id, info in questoes_config.items():
            col_ia, col_moodle, col_diff = f"{q_id}_IA_Pontos", f"{q_id}_Moodle_Pontos", f"{q_id}_Diferenca"
            dados_corr = df[(df[col_ia] > 0) | (df[col_moodle] > 0)]
            stats['questoes'][q_id] = {
                # CORRIGIDO: usa 'max_points'
                'peso': info['max_points'], 'media_ia': df[col_ia].mean(), 'media_moodle': df[col_moodle].mean(),
                'media_percent': df[f"{q_id}_Moodle_Percent"].mean(), 'desvio_ia': df[col_ia].std(),
                'desvio_moodle': df[col_moodle].std(),
                'correlacao': dados_corr[col_ia].corr(dados_corr[col_moodle]) if len(dados_corr) > 1 else 0.0,
                'diferenca_media': df[col_diff].mean(), 'diferenca_abs_media': df[col_diff].abs().mean(),
                'concordancia': len(df[abs(df[col_diff]) <= 1.0]) / len(df) * 100 if len(df) > 0 else 0.0}
        return stats

    def _salvar_excel_completo(self, df: pd.DataFrame, stats: Dict, questoes_config: Dict):
        output_dir, timestamp = Path("output"), datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo_excel = output_dir / f"relatorio_completo_{timestamp}.xlsx"

        colunas_finais = ['Nota_Final_IA', 'Nota_Final_Moodle', 'Diferenca_Total']
        outras_colunas = [col for col in df.columns if col not in colunas_finais]
        nova_ordem = outras_colunas + colunas_finais
        df_reordenado = df[nova_ordem]

        with pd.ExcelWriter(arquivo_excel, engine='openpyxl') as writer:
            df_reordenado.to_excel(writer, sheet_name='Comparação Completa', index=False)
            
            stats_rows = [['=== GERAL ===', '']]
            stats_rows.extend([[k.replace('_', ' ').title(), f"{v:.2f}" if isinstance(v, float) else str(v)] for k, v in stats.get('geral', {}).items()])
            stats_rows.extend([['', ''], ['=== POR QUESTÃO ===', '']])
            for q_id, q_stats in stats.get('questoes', {}).items():
                stats_rows.append([f'--- {q_id} (peso: {q_stats.get("peso", "N/A")}) ---', ''])
                stats_rows.extend([[f'  {k.replace("_", " ").title()}', f"{v:.2f}" if isinstance(v, float) else str(v)] for k,v in q_stats.items() if k != 'peso'])
            pd.DataFrame(stats_rows, columns=['Métrica', 'Valor']).to_excel(writer, sheet_name='Estatísticas', index=False)

        self.logger.info(f"Relatório completo salvo em: {arquivo_excel}")

    def _exibir_relatorio_console(self, stats: Dict, questoes_config: Dict):
        print("\n" + "="*80 + "\nRELATÓRIO COMPARATIVO CONSOLE: IA vs MOODLE\n" + "="*80)
        geral = stats.get('geral')
        if not geral or geral.get('total_alunos', 0) == 0:
            return print("Nenhuma estatística para exibir.\n" + "="*80)
        print("ESTATÍSTICAS GERAIS:")
        print(f"   Alunos: {geral['total_alunos']} | Processados c/ Sucesso: {geral['processados']}")
        print(f"   Média Geral IA: {geral['media_ia']:.2f} (DP: {geral['desvio_ia']:.2f})")
        print(f"   Média Geral Moodle: {geral['media_moodle']:.2f} (DP: {geral['desvio_moodle']:.2f})")
        print(f"   Correlação Geral (IA vs Moodle): {geral['correlacao_total']:.3f}")
        print(f"   Diferença Média (IA - Moodle): {geral['diferenca_media']:.2f} pontos")
        if stats.get('questoes'):
            print(f"\nANÁLISE POR QUESTÃO:")
            for q_id, q_stats in stats['questoes'].items():
                nome = questoes_config.get(q_id, {}).get('name', '')[:30]
                print(f"\n   -> {q_id} - {nome} (peso: {q_stats.get('peso', 'N/A')} pts):")
                print(f"      Média IA: {q_stats['media_ia']:.2f} pts (DP: {q_stats['desvio_ia']:.2f})")
                print(f"      Média Moodle: {q_stats['media_moodle']:.2f} pts ({q_stats['media_percent']:.1f}% de acerto em média)")
                print(f"      Correlação: {q_stats['correlacao']:.3f}")
                print(f"      Concordância (diferença <= 1.0 pt): {q_stats['concordancia']:.1f}% dos alunos")
        print("\n" + "="*80)

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Sistema de Avaliação Automatizada com Múltiplas Tentativas')
    parser.add_argument('pasta_submissoes', help='Pasta contendo as submissões')
    parser.add_argument('--config', default='config/config.yaml', help='Caminho para o arquivo de configuração YAML.')
    parser.add_argument('--continuar', action='store_true', help='Continuar processamento anterior a partir de um estado salvo.')
    
    args = parser.parse_args()
    
    try:
        from dotenv import load_dotenv
        if load_dotenv('config/config.env'):
            print("Arquivo .env carregado.")
        else:
            print("Arquivo config/config.env não encontrado. Certifique-se de que a API_KEY está definida como variável de ambiente.")
    except ImportError:
        print("Pacote python-dotenv não instalado. Certifique-se de que a API_KEY está definida como variável de ambiente.")

    gerenciador = GerenciadorAvaliacao(args.config)
    
    if args.continuar and gerenciador.carregar_estado():
        print("Continuando processamento a partir do estado salvo.")
    else:
        gerenciador.descobrir_submissoes(args.pasta_submissoes)
        
    await gerenciador.processar_submissoes()
    gerenciador.gerar_relatorio_consolidado()
    
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Ocorreu um erro fatal na execução: {e}")