# Publicar o ConversorHub no GitHub

1. Crie um repositório chamado `ConversorHub` no GitHub, sem marcar a opção de inicializar com README (o projeto já inclui um).
2. Extraia este pacote em uma pasta local e abra um terminal Git **dentro dessa pasta**.
3. Execute os comandos abaixo, trocando `SEU_USUARIO` pelo seu nome de usuário do GitHub:

```bash
git init
git branch -M main
git add .
git commit -m "docs: preparar ConversorHub para repositorio publico"
git remote add origin https://github.com/SEU_USUARIO/ConversorHub.git
git push -u origin main
```

Se você já clonou o repositório (com `origin` configurado), execute apenas:

```bash
git add .
git commit -m "docs: adicionar README e documentacao do ConversorHub"
git push origin main
```

O GitHub exibirá automaticamente o `README.md` na página principal.

## Antes de anunciar para seguidores

- Escolher uma licença para seu próprio código e incluir arquivo `LICENSE`.
- Validar distribuição/licenças de FFmpeg, LibreOffice e demais componentes.
- Concluir o instalador Windows que prepara as dependências automaticamente.
- Testar em máquina virtual Windows limpa, sem Python/FFmpeg/LibreOffice instalados.
- Criar uma Release oficial com instalador, notas e checksum SHA-256.
- Não divulgar a versão 0.1 como instalador final.
