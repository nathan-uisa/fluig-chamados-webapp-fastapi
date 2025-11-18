from pydantic import BaseModel, EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Required





class ConfigEnv(BaseSettings):
    GOOGLE_CLIENT_ID:str
    GOOGLE_CLIENT_PROJECT_ID:str
    GOOGLE_AUTH_URI:str
    GOOGLE_TOKEN_URI:str
    GOOGLE_AUTH_PROVIDER_X509_CERT_URL:str
    GOOGLE_REDIRECT_URIS:str
    GOOGLE_CLIENT_SECRET:str


    API_ENDPOINT_FUNCIONARIO:str
    API_KEY:str
    API_NAME:str
    API_ENDPOINT_CHAMADO:str


    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
ConfigEnvSetings = ConfigEnv()

class PayloadFuncionario(BaseModel):
    """Payload para buscar dados do funcionário na API"""
    Email: EmailStr


class DadosChamado(BaseModel):
    """Modelo para criação de chamado via API"""
    Usuario: EmailStr
    Titulo: str
    Descricao: str


class DadosFuncionario(BaseModel):
    """Modelo para dados retornados da API de funcionário"""
    Nome: Optional[str] = None
    Email: Optional[str] = None
    Telefone: Optional[str] = None
    Função: Optional[str] = None
    Seção: Optional[str] = None
    Empresa: Optional[str] = None
    Centro_Custo: Optional[str] = None
    Chapa: Optional[str] = None
    Gerencia: Optional[str] = None
    Email_Pessoal: Optional[str] = None
    CNPJ_Empresa: Optional[str] = None
    Codigo_Pessoa: Optional[str] = None
    Data_Admissao: Optional[str] = None
    SearchField: Optional[str] = None
    Codigo_Empresa: Optional[str] = None
    CPF: Optional[str] = None
    Data_Nascimento: Optional[str] = None
    Codigo_Secao: Optional[str] = None
    Codigo_Equipe: Optional[str] = None
    Codigo_Função: Optional[str] = None
    
    class Config:
        extra = "ignore"
        populate_by_name = True


class DadosFuncionarioForm(BaseModel):
    """Modelo para dados formatados do funcionário usados no formulário"""
    elaborador: str
    solicitante: str
    data_abertura: str
    telefone_contato: str
    cargo: str
    secao: str
    empresa: str
    centro_custo: str
    chapa: Optional[str] = None
    gerencia: Optional[str] = None
    email: str

"""
Retorno da API de funcionário
{
	"Seção": "Sistemas",
	"Código_Função": "3461",
	"Email_Pessoal": "nathan-renner@hotmail.com",
	"Email": "nathan.azevedo@uisa.com.br",
	"Empresa": "USINAS ITAMARATI",
	"Centro_Custo": "110051404.00.0",
	"Gerencia": "17.01 - Gerência de Tecnologia da Informação",
	"Telefone": "5565996204906",
	"CNPJ_Empresa": "15.009.178/0001-70",
	"Código_Pessoa": "75471",
	"Chapa": "8004717",
	"Função": "Desenvolvedor JR",
	"Data_Admissao": "2025-10-08 00:00:00.0",
	"SearchField": "8004717 - NATHAN RENNER DE AZEVEDO",
	"Código_Empresa": "1",
	"CPF": "70424905175",
	"Data_Nascimento": "24/05/1998",
	"Nome": "NATHAN RENNER DE AZEVEDO",
	"Código_Seção": "1.00.17.01.110051404.00.0",
	"Código_Equipe": "null"
}
"""