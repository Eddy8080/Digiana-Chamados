# Checklist Railway

Use este checklist antes de cada deploy em produção.

## Variáveis obrigatórias

No serviço Django do Railway, confirmar:

- `DATABASE_URL=${{Postgres.DATABASE_URL}}`
- `ADMIN_USERNAME`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

Observações:

- A variável `DATA_BASE` não é usada pelo projeto.
- O serviço Django precisa estar vinculado ao serviço Postgres.
- `ADMIN_PASSWORD` só é usado se o banco estiver vazio.
- Em banco com usuários existentes, `setup_inicial` não cria nem altera usuários.

## Comando de start esperado

O deploy deve executar:

```text
collectstatic -> migrate -> setup_inicial -> gunicorn
```

Não deve executar:

```text
loaddata fixtures_inicial.json
```

## Sinais esperados no log

Com banco PostgreSQL configurado corretamente:

- `Running migrations`
- `No migrations to apply` ou migrations aplicadas com `OK`
- `Usuários já existem — setup inicial ignorado.`
- Gunicorn iniciando na porta `$PORT`

Em banco vazio, o esperado é:

- `Superusuário "<ADMIN_USERNAME>" criado com sucesso.`
- Gunicorn iniciando na porta `$PORT`

## Sinal de erro crítico

Se aparecer:

```text
ERRO CRITICO: Django está usando SQLite no Railway.
DATABASE_URL ou PGHOST não está configurado.
```

então o deploy deve ser considerado inválido. Corrigir `DATABASE_URL` ou vínculo com Postgres antes de continuar.

## Dados

- Produção não deve rodar `loaddata`.
- Produção não deve restaurar `fixtures_inicial.json`.
- Chamados, perfis, respostas, anexos e usuários reais devem permanecer no PostgreSQL de produção.
- Cadastros base podem ser criados manualmente com `python manage.py seed_base`, se necessário.
