# Atividade Computacional - Banco de Dados 2
## Autores: Caio Lauro de Lima e Yuri Daniel Moreira Gomes

## Instruções de Uso
1. [Instale o UV](https://docs.astral.sh/uv/#highlights):
* MacOS ou Linux
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```
* Windows
```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. Instale as dependências do projeto através do UV: 

```
uv sync
```

3. Crie um arquivo `.env` na raíz do projeto, da seguinte forma:
```
DB_HOST=[HOST DO BANCO DE DADOS]
DB_USER=[USUÁRIO DO BANCO DE DADOS]
DB_PASSWORD=[SENHA PARA O USUÁRIO]
DATABASE=atividade_computacional_db
```
Observações:
- Garanta o acesso do usuário `DB_USER` a `atividade_computacional_db`.
- Configure `log_bin_trust_function_creators = 1` no arquivo `my.cfg`:
    * Linux: `/etc/my.cnf` ou `/etc/my.cnf.d/mysql-server.cnf`
    * Windows: `C:\ProgramData\MySQL\MySQL Server X.X\my.ini`
    * Então, adicione sob `[mysqld]`:
    ```
    log_bin_trust_function_creators = 1
    ```
    * Depois reinicie o serviço:
        * Linux: `sudo systemctl restart mysqld`
        * Windows: reinicie o serviço "MySQL" pelo Gerenciador de Serviços ou via `services.msc`


4. Inicie o FastAPI usando:

```
uv run fastapi dev src/app.py
```
ou ative o ambiente virtual e inicie:
```
> source .venv/bin/activate
> fastapi dev src/app.py
```

5. Abra o [link da documentação](http://127.0.0.1:8000/docs#/), que contém os métodos e permite realizar as requisições.