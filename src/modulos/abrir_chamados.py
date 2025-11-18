import configparser
import re
import os
import requests
from typing import Dict, List, Optional
from src.modulos.logger import logger
from src.modulos.planilha import PATH_TO_TEMP
from src.classes.tipos import DadosChamado, ConfigEnvSetings


class AbrirChamados:
    """
    Classe para abrir chamados em sequência usando dados processados de planilha.
    Processa placeholders como <A>, <B>, etc. no título e descrição.
    """
    
    def __init__(self, email_usuario: str):
        """
        Inicializa a classe para abrir chamados.
        
        Args:
            email_usuario: Email do usuário que está criando os chamados
        """
        self.email_usuario = email_usuario
        self.config_planilha = configparser.ConfigParser()
        self.headers = {
            ConfigEnvSetings.API_NAME: ConfigEnvSetings.API_KEY
        }
    
    def carregar_dados_temp(self) -> bool:
        """
        Carrega os dados processados do arquivo temp.txt.
        
        Returns:
            True se carregou com sucesso, False caso contrário
        """
        try:
            if not os.path.exists(PATH_TO_TEMP):
                logger.error(f"Arquivo temp.txt não encontrado: {PATH_TO_TEMP}")
                return False
            
            self.config_planilha.read(PATH_TO_TEMP, encoding='utf-8')
            
            if not self.config_planilha.sections():
                logger.warning("Nenhuma seção encontrada no arquivo temp.txt")
                return False
            
            logger.info(f"Dados carregados: {len(self.config_planilha.sections())} linhas encontradas")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados do temp.txt: {str(e)}")
            return False
    
    def substituir_placeholders(self, texto: str, numero_linha: str) -> str:
        """
        Substitui placeholders como <A>, <B>, etc. pelos valores da planilha.
        
        Args:
            texto: Texto com placeholders (ex: "Chamado <A> - <B>")
            numero_linha: Número da linha/seção no config (ex: "1", "2", etc.)
        
        Returns:
            Texto com placeholders substituídos
        """
        if not texto:
            return texto
        
        # Encontrar todos os placeholders no formato <LETRA>
        placeholders = re.findall(r'<([A-Z]+)>', texto.upper())
        texto_processado = texto
        
        for letra in placeholders:
            letra_lower = letra.lower()
            
            # Verificar se a coluna existe na seção
            if self.config_planilha.has_option(numero_linha, letra_lower):
                valor = self.config_planilha.get(numero_linha, letra_lower)
                # Substituir placeholder (case-insensitive)
                texto_processado = re.sub(
                    f'<{letra}>', 
                    valor, 
                    texto_processado, 
                    flags=re.IGNORECASE
                )
            else:
                logger.warning(
                    f"Coluna '{letra_lower}' não encontrada na linha {numero_linha}. "
                    f"Placeholder <{letra}> não será substituído."
                )
        
        return texto_processado
    
    def processar_chamado(self, titulo: str, descricao: str, numero_linha: str) -> Dict:
        """
        Processa um chamado substituindo placeholders pelos valores da planilha.
        
        Args:
            titulo: Título do chamado com placeholders
            descricao: Descrição do chamado com placeholders
            numero_linha: Número da linha/seção no config
        
        Returns:
            Dicionário com título e descrição processados, ou erro se linha não encontrada
        """
        secao = str(numero_linha)
        
        if secao not in self.config_planilha.sections():
            return {
                'titulo': titulo,
                'descricao': descricao,
                'erro': f'Linha {secao} não encontrada'
            }
        
        titulo_processado = self.substituir_placeholders(titulo, secao)
        desc_processada = self.substituir_placeholders(descricao, secao)
        
        return {
            'titulo': titulo_processado,
            'descricao': desc_processada,
        }
    
    def criar_chamado_api(self, titulo: str, descricao: str) -> Dict:
        """
        Cria um chamado via API.
        
        Args:
            titulo: Título do chamado
            descricao: Descrição do chamado
        
        Returns:
            Dicionário com resultado: {'sucesso': bool, 'mensagem': str, 'dados': dict}
        """
        try:
            payload_chamado = DadosChamado(
                Usuario=self.email_usuario,
                Titulo=titulo,
                Descricao=descricao
            )
            
            response = requests.post(
                ConfigEnvSetings.API_ENDPOINT_CHAMADO,
                json=payload_chamado.model_dump(),
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            logger.info(f"Chamado criado com sucesso: {titulo}")
            return {
                'sucesso': True,
                'mensagem': 'Chamado criado com sucesso',
                'dados': response.json() if response.content else {}
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao criar chamado via API: {str(e)}")
            return {
                'sucesso': False,
                'mensagem': f'Erro ao criar chamado: {str(e)}',
                'dados': {}
            }
        except Exception as e:
            logger.error(f"Erro inesperado ao criar chamado: {str(e)}")
            return {
                'sucesso': False,
                'mensagem': f'Erro inesperado: {str(e)}',
                'dados': {}
            }
    
    def abrir_chamados_sequencia(
        self, 
        titulo: str, 
        descricao: str, 
        qtd_chamados: int,
        inicio_linha: int = 1,
        ignorar_primeira_linha: bool = True
    ) -> Dict:
        """
        Abre múltiplos chamados em sequência usando dados da planilha processada.
        
        Args:
            titulo: Título do chamado com placeholders (ex: "Chamado <A> - <B>")
            descricao: Descrição do chamado com placeholders
            qtd_chamados: Quantidade de chamados a abrir
            inicio_linha: Linha inicial para começar a processar (padrão: 1)
            ignorar_primeira_linha: Se True, ignora a primeira seção (cabeçalho) (padrão: True)
        
        Returns:
            Dicionário com estatísticas: {
                'total_processados': int,
                'sucessos': int,
                'erros': int,
                'detalhes': List[Dict]
            }
        """
        # Carregar dados do temp.txt
        if not self.carregar_dados_temp():
            return {
                'total_processados': 0,
                'sucessos': 0,
                'erros': 1,
                'detalhes': [{
                    'linha': 0,
                    'sucesso': False,
                    'mensagem': 'Erro ao carregar dados do temp.txt'
                }]
            }
        
        secoes = sorted(
            [int(s) for s in self.config_planilha.sections() if s.isdigit()],
            key=int
        )
        
        if not secoes:
            return {
                'total_processados': 0,
                'sucessos': 0,
                'erros': 1,
                'detalhes': [{
                    'linha': 0,
                    'sucesso': False,
                    'mensagem': 'Nenhuma linha válida encontrada no temp.txt'
                }]
            }
        
        # Se ignorar_primeira_linha for True, remover a primeira seção (geralmente é o cabeçalho)
        if ignorar_primeira_linha and secoes:
            primeira_secao = min(secoes)
            secoes = [s for s in secoes if s != primeira_secao]
            logger.info(f"Ignorando primeira linha (seção {primeira_secao}) - cabeçalho da planilha")
        
        # Filtrar seções a partir do início
        secoes_filtradas = [s for s in secoes if s >= inicio_linha]
        
        # Limitar quantidade de chamados
        secoes_processar = secoes_filtradas[:qtd_chamados]
        
        if not secoes_processar:
            return {
                'total_processados': 0,
                'sucessos': 0,
                'erros': 1,
                'detalhes': [{
                    'linha': inicio_linha,
                    'sucesso': False,
                    'mensagem': f'Nenhuma linha encontrada a partir da linha {inicio_linha}'
                }]
            }
        
        logger.info(
            f"Iniciando criação de {len(secoes_processar)} chamado(s) "
            f"a partir da linha {inicio_linha}"
        )
        
        sucessos = 0
        erros = 0
        detalhes = []
        
        # Processar cada linha
        for numero_linha in secoes_processar:
            linha_str = str(numero_linha)
            
            # Processar placeholders
            resultado_processamento = self.processar_chamado(
                titulo, 
                descricao, 
                linha_str
            )
            
            if 'erro' in resultado_processamento:
                erros += 1
                detalhes.append({
                    'linha': numero_linha,
                    'sucesso': False,
                    'mensagem': resultado_processamento['erro']
                })
                logger.warning(
                    f"Linha {numero_linha}: {resultado_processamento['erro']}"
                )
                continue
            
            # Criar chamado via API
            resultado_api = self.criar_chamado_api(
                resultado_processamento['titulo'],
                resultado_processamento['descricao']
            )
            
            if resultado_api['sucesso']:
                sucessos += 1
                detalhes.append({
                    'linha': numero_linha,
                    'sucesso': True,
                    'mensagem': resultado_api['mensagem'],
                    'titulo': resultado_processamento['titulo']
                })
            else:
                erros += 1
                detalhes.append({
                    'linha': numero_linha,
                    'sucesso': False,
                    'mensagem': resultado_api['mensagem'],
                    'titulo': resultado_processamento['titulo']
                })
        
        logger.info(
            f"Processamento concluído: {sucessos} sucesso(s), {erros} erro(s)"
        )
        
        return {
            'total_processados': len(secoes_processar),
            'sucessos': sucessos,
            'erros': erros,
            'detalhes': detalhes
        }

