from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
from src.rotas.rt_login import router as login_router
from src.rotas.rt_chamado import router as chamado_router
from src.modulos.logger import logger

app = FastAPI(title="Login Google", version="1.0.0")

# Configurar sessões
app.add_middleware(SessionMiddleware, secret_key="sua-chave-secreta-aqui-altere-em-producao")

# Montar arquivos estáticos e templates
app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")

# Incluir rotas
app.include_router(login_router)
app.include_router(chamado_router)

# Configurações do Google OAuth agora são carregadas diretamente de ConfigEnvSetings nas rotas
# Não é mais necessário armazenar no app.state

logger.info("Aplicação FastAPI iniciada")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Página inicial - redireciona para login"""
    return RedirectResponse(url="/login")


if __name__ == "__main__":
    logger.info("Iniciando servidor Uvicorn na porta 3000")
    print("-" * 60)
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=3000,
        reload=True,
        log_level="info"
    )
