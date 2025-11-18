// Script para gerenciar o formulário de chamados e modal de prévia

document.addEventListener('DOMContentLoaded', function() {
    const planilhaInput = document.getElementById('planilha');
    const statusDiv = document.getElementById('status');
    const qtdGroup = document.getElementById('quantidade-group');
    const ignorarCabecalhoGroup = document.getElementById('ignorar-cabecalho-group');
    const previewButtonGroup = document.getElementById('preview-button-group');
    const formChamado = document.getElementById('formChamado');
    const btnPreview = document.getElementById('btn-preview');
    const modalPreview = document.getElementById('modal-preview');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const modalLoading = document.getElementById('modal-loading');
    const modalError = document.getElementById('modal-error');
    const modalPreviewContent = document.getElementById('modal-preview-content');

    // Gerenciar upload de planilha
    if (planilhaInput) {
        planilhaInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                statusDiv.textContent = '✓ Arquivo selecionado: ' + file.name;
                statusDiv.style.display = 'block';
                qtdGroup.style.display = 'block';
                ignorarCabecalhoGroup.style.display = 'block';
                previewButtonGroup.style.display = 'block';
            } else {
                statusDiv.textContent = '';
                statusDiv.style.display = 'none';
                qtdGroup.style.display = 'none';
                ignorarCabecalhoGroup.style.display = 'none';
                previewButtonGroup.style.display = 'none';
            }
        });
    }

    // Abrir modal de prévia
    if (btnPreview) {
        btnPreview.addEventListener('click', async function() {
            const titulo = document.getElementById('ds_titulo').value;
            const descricao = document.getElementById('ds_chamado').value;
            const qtdChamados = parseInt(document.getElementById('qtd_chamados').value) || 5;
            const ignorarPrimeiraLinha = document.getElementById('ignorar_primeira_linha').checked;

            if (!titulo || !descricao) {
                alert('Por favor, preencha o título e a descrição antes de visualizar a prévia.');
                return;
            }

            // Mostrar modal
            modalPreview.style.display = 'flex';
            modalLoading.style.display = 'block';
            modalError.style.display = 'none';
            modalPreviewContent.style.display = 'none';

            try {
                const response = await fetch('/chamado/preview', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        titulo: titulo,
                        descricao: descricao,
                        qtd_chamados: qtdChamados,
                        ignorar_primeira_linha: ignorarPrimeiraLinha
                    })
                });

                const data = await response.json();

                modalLoading.style.display = 'none';

                if (!response.ok || data.erro) {
                    modalError.textContent = data.erro || 'Erro ao gerar prévia';
                    modalError.style.display = 'block';
                    return;
                }

                // Exibir prévia
                let html = '';
                if (data.total_linhas) {
                    html += `<div style="margin-bottom: 16px; padding: 12px; background: var(--bg-section); border-radius: var(--border-radius); border: 1px solid var(--border-primary);">
                        <strong style="color: var(--text-primary);">Total de linhas disponíveis:</strong> 
                        <span style="color: var(--text-secondary);">${data.total_linhas}</span>
                    </div>`;
                }

                if (data.preview && data.preview.length > 0) {
                    data.preview.forEach(function(item) {
                        html += `<div style="margin-bottom: 20px; padding: 16px; background: var(--bg-section); border-radius: var(--border-radius); border: 1px solid var(--border-primary);">`;
                        html += `<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">`;
                        html += `<span style="color: var(--text-muted); font-size: 13px; font-weight: 600;">Linha ${item.linha}:</span>`;
                        if (item.erro) {
                            html += `<span style="color: var(--error-text); font-size: 13px;">⚠️ ${item.erro}</span>`;
                        } else {
                            html += `<span style="color: var(--success-text); font-size: 13px;">✓ Processado</span>`;
                        }
                        html += `</div>`;
                        html += `<div style="margin-bottom: 8px;">`;
                        html += `<strong style="color: var(--text-primary); font-size: 14px; display: block; margin-bottom: 4px;">Título:</strong>`;
                        html += `<div style="color: var(--text-secondary); padding: 10px; background: var(--bg-input); border-radius: var(--border-radius); border: 1px solid var(--border-primary);">${escapeHtml(item.titulo || '(vazio)')}</div>`;
                        html += `</div>`;
                        html += `<div>`;
                        html += `<strong style="color: var(--text-primary); font-size: 14px; display: block; margin-bottom: 4px;">Descrição:</strong>`;
                        html += `<div style="color: var(--text-secondary); padding: 10px; background: var(--bg-input); border-radius: var(--border-radius); border: 1px solid var(--border-primary); white-space: pre-wrap;">${escapeHtml(item.descricao || '(vazio)')}</div>`;
                        html += `</div>`;
                        html += `</div>`;
                    });
                } else {
                    html += `<div style="text-align: center; padding: 40px; color: var(--text-muted);">Nenhuma prévia disponível</div>`;
                }

                modalPreviewContent.innerHTML = html;
                modalPreviewContent.style.display = 'block';
            } catch (error) {
                modalLoading.style.display = 'none';
                modalError.textContent = 'Erro ao carregar prévia: ' + error.message;
                modalError.style.display = 'block';
            }
        });
    }

    // Fechar modal
    if (btnCloseModal) {
        btnCloseModal.addEventListener('click', function() {
            modalPreview.style.display = 'none';
        });
    }

    // Fechar modal ao clicar fora
    if (modalPreview) {
        modalPreview.addEventListener('click', function(e) {
            if (e.target === modalPreview) {
                modalPreview.style.display = 'none';
            }
        });
    }

    // Fechar modal com ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modalPreview && modalPreview.style.display === 'flex') {
            modalPreview.style.display = 'none';
        }
    });

    // Validação do formulário
    if (formChamado) {
        formChamado.addEventListener('submit', function(e) {
            const titulo = document.getElementById('ds_titulo').value;
            const descricao = document.getElementById('ds_chamado').value;
            
            if (!titulo || !descricao) {
                e.preventDefault();
                alert('Por favor, preencha o título e a descrição do chamado.');
                return false;
            }
        });
    }
});

// Função auxiliar para escapar HTML e prevenir XSS
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

