
# GestãoBar — Bar do Coelho

Sistema web para gerenciamento de bar, com controle de mercadorias, vendas, pedidos e delivery.

## Funcionalidades

- Login e cadastro de funcionários
- Controle de mercadorias e estoque
- Registro e histórico de vendas
- Pedidos por mesa
- Cardápio digital
- Pedidos públicos de delivery
- Acompanhamento dos pedidos de delivery
- Fechamento de vendas

## Requisitos

- Python
- Dependências listadas em `requirements.txt`

## Executar localmente no Windows

1. Abra o terminal na pasta do projeto.
2. Ative o ambiente virtual:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. Instale as dependências:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Inicie o sistema:

   ```powershell
   python run.py
   ```

5. Abra `http://127.0.0.1:5000` no navegador.

## Observações

- O banco de dados local não deve ser enviado ao GitHub.
- Configure uma chave secreta própria antes de publicar o sistema.
- A hospedagem precisa de uma estratégia de banco de dados persistente para preservar vendas, usuários e estoque.
- O funcionamento completo do delivery deve ser testado antes de utilizar o sistema em produção.
