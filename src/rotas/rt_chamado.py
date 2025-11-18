from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from src.classes.tipos import ConfigEnvSetings, DadosFuncionario, DadosFuncionarioForm, DadosChamado, PayloadFuncionario
import requests
from datetime import datetime
from src.modulos.logger import logger
from src.modulos.planilha import Planilha, PATH_TO_TEMP
from src.modulos.abrir_chamados import AbrirChamados
import os
import tempfile
import configparser

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("/chamado", response_class=HTMLResponse)
async def chamado(request: Request):
    """Página de chamado com dados do funcionário"""
    user = request.session.get('user')
    if not user:
        return RedirectResponse(url="/login")
    
    email = user.get('email')
    if not email:
        return RedirectResponse(url="/login")
    
    try:
        # Criar payload usando Pydantic
        payload = PayloadFuncionario(Email=email)
        headers = {
            ConfigEnvSetings.API_NAME: ConfigEnvSetings.API_KEY
        }
        response = requests.post(
            ConfigEnvSetings.API_ENDPOINT_FUNCIONARIO,
            json=payload.model_dump(),
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        funcionario_data = response.json()
        
        # Validar e criar instância Pydantic
        funcionario = DadosFuncionario(**funcionario_data)
        
        # Criar dados formatados para o formulário
        dados_funcionario = DadosFuncionarioForm(
            elaborador=funcionario.Nome or '',
            solicitante=funcionario.Nome or '',
            data_abertura=datetime.now().strftime('%d/%m/%Y %H:%M'),
            telefone_contato=funcionario.Telefone or '',
            cargo=funcionario.Função or '',
            secao=funcionario.Seção or '',
            empresa=funcionario.Empresa or '',
            centro_custo=funcionario.Centro_Custo or '',
            chapa=funcionario.Chapa,
            gerencia=funcionario.Gerencia,
            email=funcionario.Email or ''
        )
        
        logger.info(f"Dados do funcionário carregados para: {email}")
        
        return templates.TemplateResponse(
            "chamado.html",
            {
                "request": request,
                "dados": dados_funcionario.model_dump(),
                "user": user
            }
        )
        
    except requests.RequestException as e:
        logger.error(f"Erro ao buscar dados do funcionário: {str(e)}")
        return templates.TemplateResponse(
            "chamado.html",
            {
                "request": request,
                "dados": None,
                "user": user,
                "error": "Erro ao carregar dados do funcionário. Tente novamente mais tarde."
            }
        )
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        return templates.TemplateResponse(
            "chamado.html",
            {
                "request": request,
                "dados": None,
                "user": user,
                "error": "Erro inesperado ao processar a solicitação."
            }
        )


@router.post("/chamado", response_class=HTMLResponse)
async def criar_chamado(
    request: Request,
    ds_titulo: str = Form(...),
    ds_chamado: str = Form(...),
    solicitante: str = Form(None),
    num_tel_contato: str = Form(None),
    sap_ibid: str = Form("Não"),
    planilha: UploadFile = File(None),
    qtd_chamados: int = Form(1),
    ignorar_primeira_linha: str = Form("1")
):
    """Processa criação de chamado(s) - único ou em lote via planilha"""
    user = request.session.get('user')
    if not user:
        return RedirectResponse(url="/login")
    
    email = user.get('email')
    if not email:
        return RedirectResponse(url="/login")
    
    try:
        # Buscar dados do funcionário novamente para garantir que temos os dados atualizados
        payload_func = PayloadFuncionario(Email=email)
        headers = {
            ConfigEnvSetings.API_NAME: ConfigEnvSetings.API_KEY
        }
        response_func = requests.post(
            ConfigEnvSetings.API_ENDPOINT_FUNCIONARIO,
            json=payload_func.model_dump(),
            headers=headers,
            timeout=10
        )
        response_func.raise_for_status()
        funcionario_data = response_func.json()
        
        # Validar e criar instância Pydantic
        funcionario = DadosFuncionario(**funcionario_data)
        
        # Criar dados formatados para o formulário
        dados_funcionario = DadosFuncionarioForm(
            elaborador=funcionario.Nome or '',
            solicitante=solicitante or funcionario.Nome or '',
            data_abertura=datetime.now().strftime('%d/%m/%Y %H:%M'),
            telefone_contato=num_tel_contato or funcionario.Telefone or '',
            cargo=funcionario.Função or '',
            secao=funcionario.Seção or '',
            empresa=funcionario.Empresa or '',
            centro_custo=funcionario.Centro_Custo or '',
            chapa=funcionario.Chapa,
            gerencia=funcionario.Gerencia,
            email=funcionario.Email or ''
        )
        
        chamados_criados = 0
        chamados_erro = 0
        
        # Se há planilha, processar em lote
        if planilha and planilha.filename:
            if not planilha.filename.endswith('.xlsx'):
                return templates.TemplateResponse(
                    "chamado.html",
                    {
                        "request": request,
                        "dados": dados_funcionario.model_dump(),
                        "user": user,
                        "error": "Apenas arquivos .xlsx são suportados."
                    }
                )
            
            # Salvar arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                content = await planilha.read()
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            try:
                # Processar planilha
                planilha_obj = Planilha(tmp_path)
                linhas_processadas = planilha_obj.criar_base_chamados()
                
                if not linhas_processadas:
                    os.unlink(tmp_path)
                    return templates.TemplateResponse(
                        "chamado.html",
                        {
                            "request": request,
                            "dados": dados_funcionario.model_dump(),
                            "user": user,
                            "error": "Erro ao processar planilha. Verifique o formato do arquivo."
                        }
                    )
                
                # Usar o novo módulo para abrir chamados em sequência
                ignorar_cabecalho = ignorar_primeira_linha == "1"
                abrir_chamados = AbrirChamados(email)
                resultado = abrir_chamados.abrir_chamados_sequencia(
                    titulo=ds_titulo,
                    descricao=ds_chamado,
                    qtd_chamados=qtd_chamados,
                    inicio_linha=1,
                    ignorar_primeira_linha=ignorar_cabecalho
                )
                
                chamados_criados = resultado['sucessos']
                chamados_erro = resultado['erros']
                
                # Limpar arquivos temporários
                planilha_obj.limpar_arquivo_temporario()
                os.unlink(tmp_path)
                
                mensagem = f"{chamados_criados} chamado(s) criado(s) com sucesso!"
                if chamados_erro > 0:
                    mensagem += f" {chamados_erro} chamado(s) falharam."
                
                return templates.TemplateResponse(
                    "chamado.html",
                    {
                        "request": request,
                        "dados": dados_funcionario.model_dump(),
                        "user": user,
                        "success": mensagem
                    }
                )
                
            except Exception as e:
                logger.error(f"Erro ao processar planilha: {str(e)}")
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                return templates.TemplateResponse(
                    "chamado.html",
                    {
                        "request": request,
                        "dados": dados_funcionario.model_dump(),
                        "user": user,
                        "error": f"Erro ao processar planilha: {str(e)}"
                    }
                )
        else:
            # Criar chamado único usando Pydantic
            payload_chamado = DadosChamado(
                Usuario=email,
                Titulo=ds_titulo,
                Descricao=ds_chamado
            )
            
            try:
                response_chamado = requests.post(
                    ConfigEnvSetings.API_ENDPOINT_CHAMADO,
                    json=payload_chamado.model_dump(),
                    headers=headers,
                    timeout=10
                )
                response_chamado.raise_for_status()
                logger.info(f"Chamado único criado com sucesso: {ds_titulo}")
                
                return templates.TemplateResponse(
                    "chamado.html",
                    {
                        "request": request,
                        "dados": dados_funcionario.model_dump(),
                        "user": user,
                        "success": "Chamado criado com sucesso!"
                    }
                )
            except Exception as e:
                logger.error(f"Erro ao criar chamado: {str(e)}")
                return templates.TemplateResponse(
                    "chamado.html",
                    {
                        "request": request,
                        "dados": dados_funcionario.model_dump(),
                        "user": user,
                        "error": f"Erro ao criar chamado: {str(e)}"
                    }
                )
        
    except requests.RequestException as e:
        logger.error(f"Erro ao buscar dados do funcionário: {str(e)}")
        return templates.TemplateResponse(
            "chamado.html",
            {
                "request": request,
                "dados": None,
                "user": user,
                "error": "Erro ao carregar dados do funcionário. Tente novamente mais tarde."
            }
        )
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        return templates.TemplateResponse(
            "chamado.html",
            {
                "request": request,
                "dados": None,
                "user": user,
                "error": f"Erro inesperado: {str(e)}"
            }
        )


@router.post("/chamado/carregar-planilha", response_class=JSONResponse)
async def carregar_planilha(request: Request, planilha: UploadFile = File(...)):
    """
    Carrega a planilha e cria o temp.txt imediatamente após o upload
    """
    user = request.session.get('user')
    if not user:
        return JSONResponse(
            status_code=401,
            content={"erro": "Usuário não autenticado", "sucesso": False}
        )
    
    if not planilha.filename.endswith('.xlsx'):
        return JSONResponse(
            status_code=400,
            content={"erro": "Apenas arquivos .xlsx são suportados.", "sucesso": False}
        )
    
    try:
        # Salvar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await planilha.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Processar planilha e criar temp.txt
            planilha_obj = Planilha(tmp_path)
            planilha_obj.carregar_planilha()  # Isso já cria o temp.txt vazio
            linhas_processadas = planilha_obj.criar_base_chamados()  # Isso preenche o temp.txt
            
            # Limpar arquivo temporário da planilha (mas manter temp.txt)
            os.unlink(tmp_path)
            
            if not linhas_processadas:
                return JSONResponse(
                    status_code=400,
                    content={
                        "erro": "Erro ao processar planilha. Verifique o formato do arquivo.",
                        "sucesso": False
                    }
                )
            
            return JSONResponse(
                content={
                    "sucesso": True,
                    "mensagem": f"Planilha carregada com sucesso! {linhas_processadas} linha(s) processada(s).",
                    "linhas_processadas": linhas_processadas
                }
            )
            
        except Exception as e:
            logger.error(f"Erro ao processar planilha: {str(e)}")
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            return JSONResponse(
                status_code=500,
                content={
                    "erro": f"Erro ao processar planilha: {str(e)}",
                    "sucesso": False
                }
            )
            
    except Exception as e:
        logger.error(f"Erro ao carregar planilha: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "erro": f"Erro ao carregar planilha: {str(e)}",
                "sucesso": False
            }
        )


class PreviewRequest(BaseModel):
    """Modelo para requisição de prévia"""
    titulo: str
    descricao: str
    qtd_chamados: int = 5
    ignorar_primeira_linha: bool = True


@router.post("/chamado/preview", response_class=JSONResponse)
async def preview_chamados(request: Request, preview_data: PreviewRequest):
    """
    Gera prévia dos chamados com placeholders substituídos
    """
    user = request.session.get('user')
    if not user:
        return JSONResponse(
            status_code=401,
            content={"erro": "Usuário não autenticado"}
        )
    
    email = user.get('email')
    if not email:
        return JSONResponse(
            status_code=401,
            content={"erro": "Email não encontrado na sessão"}
        )
    
    try:
        # Verificar se temp.txt existe
        if not os.path.exists(PATH_TO_TEMP):
            return JSONResponse(
                status_code=400,
                content={
                    "erro": "Arquivo temp.txt não encontrado. Faça upload da planilha primeiro.",
                    "preview": []
                }
            )
        
        # Usar o módulo AbrirChamados para processar
        abrir_chamados = AbrirChamados(email)
        
        if not abrir_chamados.carregar_dados_temp():
            return JSONResponse(
                status_code=400,
                content={
                    "erro": "Erro ao carregar dados do temp.txt",
                    "preview": []
                }
            )
        
        # Obter seções disponíveis
        secoes = sorted(
            [int(s) for s in abrir_chamados.config_planilha.sections() if s.isdigit()],
            key=int
        )
        
        if not secoes:
            return JSONResponse(
                status_code=400,
                content={
                    "erro": "Nenhuma linha válida encontrada no temp.txt",
                    "preview": []
                }
            )
        
        # Se ignorar_primeira_linha for True, remover a primeira seção (cabeçalho)
        if preview_data.ignorar_primeira_linha and secoes:
            primeira_secao = min(secoes)
            secoes = [s for s in secoes if s != primeira_secao]
        
        # Limitar quantidade
        qtd = min(preview_data.qtd_chamados, len(secoes))
        secoes_processar = secoes[:qtd]
        
        preview_items = []
        
        # Processar cada linha
        for numero_linha in secoes_processar:
            linha_str = str(numero_linha)
            resultado = abrir_chamados.processar_chamado(
                preview_data.titulo,
                preview_data.descricao,
                linha_str
            )
            
            if 'erro' in resultado:
                preview_items.append({
                    'linha': numero_linha,
                    'titulo': preview_data.titulo,
                    'descricao': preview_data.descricao,
                    'erro': resultado['erro']
                })
            else:
                preview_items.append({
                    'linha': numero_linha,
                    'titulo': resultado['titulo'],
                    'descricao': resultado['descricao'],
                    'erro': None
                })
        
        return JSONResponse(
            content={
                "sucesso": True,
                "total_linhas": len(secoes),
                "preview": preview_items
            }
        )
        
    except Exception as e:
        logger.error(f"Erro ao gerar prévia: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "erro": f"Erro ao gerar prévia: {str(e)}",
                "preview": []
            }
        )
