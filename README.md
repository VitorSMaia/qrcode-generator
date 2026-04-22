📱 QR Track: Sistema de QR Codes Dinâmicos
Um sistema completo para geração, gerenciamento e rastreio de QR Codes. Com esta aplicação, você pode criar links rastreáveis, monitorar a quantidade de acessos em tempo real e garantir que cada usuário gerencie apenas seus próprios dados através de uma camada de autenticação robusta.

🚀 Funcionalidades
Autenticação Segura: Cadastro e login de usuários via Supabase Auth.

QR Codes Dinâmicos: O link do QR Code não muda, mas o destino pode ser alterado no banco de dados.

Rastreio de Cliques: Contador automático de leituras cada vez que o código é escaneado.

Isolamento de Dados (RLS): Cada usuário visualiza e gerencia exclusivamente os seus próprios QR Codes.

Dashboard Interativo: Interface limpa para monitoramento de performance.

🛠️ Tecnologias
Backend: Python com Flask (Serverless)

Banco de Dados: Supabase (PostgreSQL)

Autenticação: Supabase Auth (JWT)

Frontend: HTML5, Tailwind CSS e JavaScript (Fetch API)

Hospedagem: Vercel

📋 Pré-requisitos
Antes de começar, você precisará de:

Uma conta no Supabase.

Uma conta na Vercel.

Python instalado localmente para testes.

🔧 Configuração do Banco de Dados
No painel do Supabase, execute o seguinte script no SQL Editor para preparar as tabelas e as políticas de segurança (RLS):

SQL
-- Criar a tabela de registros
create table qrcodes (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users not null,
  slug text unique not null,
  conteudo_original text not null,
  contador int default 0,
  created_at timestamp with time zone default now()
);

-- Habilitar Row Level Security
alter table qrcodes enable row level security;

-- Políticas de acesso
create policy "Users can see their own data" on qrcodes
  for select using (auth.uid() = user_id);

create policy "Users can insert their own data" on qrcodes
  for insert with check (auth.uid() = user_id);
💻 Estrutura do Projeto
Plaintext
├── api/
│   └── index.py          # Backend Flask (Serverless Function)
├── public/
│   ├── login.html        # Interface de Auth
│   └── dashboard.html    # Painel de controle do usuário
├── requirements.txt      # Dependências Python
└── vercel.json           # Configuração de roteamento Vercel
🚀 Deploy na Vercel
Variáveis de Ambiente: No painel da Vercel, adicione as seguintes chaves em Settings > Environment Variables:

SUPABASE_URL: URL do seu projeto Supabase.

SUPABASE_ANON_KEY: Sua chave secreta anônima do Supabase.

Comando de Deploy:

Bash
# Se usar a CLI da Vercel
vercel --prod
Ou simplesmente conecte seu repositório do GitHub à Vercel para deploy automático.

📖 Como Usar
Acesse a URL do projeto e crie uma conta na tela de Login.

No Dashboard, insira um "Slug" (um nome curto para o link) e a "URL de Destino".

Gere o link. O sistema fornecerá uma URL no formato seu-app.vercel.app/l/nome-escolhido.

Use qualquer gerador de imagem de QR Code para apontar para essa URL.

Acompanhe: Cada vez que alguém escanear, o contador no seu dashboard subirá instantaneamente!

📝 Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

Desenvolvido por [João Maia] ✨
