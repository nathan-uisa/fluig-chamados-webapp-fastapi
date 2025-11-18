import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Criar diretório de logs se não existir
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configurar formato de log
log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Configurar logger raiz
logger = logging.getLogger("api_fluig")
logger.setLevel(logging.INFO)

# Evitar duplicação de handlers
if not logger.handlers:
    # Handler para arquivo com rotação
    log_file = log_dir / "api_fluig.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_format)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    
    # Adicionar handlers ao logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Desabilitar propagação para evitar logs duplicados
logger.propagate = False