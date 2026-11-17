# Download free videos

Site simples para colar um link público do TikTok, carregar título/descrição/miniatura e baixar o vídeo na melhor qualidade que o TikTok disponibilizar ao extrator.

## Publicar pelo GitHub + Render

1. Crie um repositório no GitHub chamado `download-free-videos`.
2. Extraia o ZIP e envie **os arquivos e pastas que estão dentro dele** para a raiz do repositório. Não envie apenas o ZIP.
3. No Render, escolha **New + → Blueprint**.
4. Conecte o GitHub e selecione o repositório `download-free-videos`.
5. O Render vai localizar o arquivo `render.yaml`. Confirme a criação e aguarde o deploy.
6. Quando terminar, abra o endereço `.onrender.com` fornecido pelo Render.

O `render.yaml` já define o comando de instalação, o comando para iniciar o servidor e a verificação de saúde.

## Se preferir criar um Web Service manualmente

- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app --workers 1 --threads 4 --timeout 180`

## Importante

- O GitHub guarda o código; o Render executa o servidor. Não publique somente no GitHub Pages, porque ele não executa Python.
- O Render gratuito pode suspender o serviço quando fica sem uso. A primeira abertura depois disso pode demorar.
- O TikTok pode mudar o funcionamento dos links. Vídeos privados, removidos, restritos ou protegidos podem não carregar.
- A qualidade máxima e a disponibilidade de uma versão sem marca-d'água dependem do que a plataforma disponibiliza para aquele vídeo. Não há garantia para todos os links.
- Use apenas vídeos seus ou cujo download você tenha autorização para fazer. Respeite os direitos dos criadores e os termos da plataforma.
- Para um serviço aberto ao público, adicione limites de uso e monitoramento para evitar abuso e consumo excessivo de recursos.
