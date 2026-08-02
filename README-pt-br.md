[English version](README.md)

[English version](README.md)

# 📬 Sistema de Automação de E-mails

Um sistema abrangente de automação de e-mails desenvolvido em Python para enviar relatórios, notificações e e-mails agendados automaticamente.

## ✨ Funcionalidades

- **📧 Envio de E-mails**: Envie e-mails simples ou em HTML com anexos
- **📊 Geração de Relatórios**: Gere e envie relatórios nos formatos HTML, CSV ou JSON
- **🔔 Notificações**: Envie notificações instantâneas com níveis de prioridade e tipos
- **⏰ Agendamento de E-mails**: Agende e-mails usando expressões cron ou intervalos predefinidos
- **🔒 Configuração Segura**: Configuração baseada em variáveis de ambiente para dados sensíveis

## 📁 Estrutura do Projeto

```
AutEmails/
├── main.py              # Ponto de entrada principal
├── config.py            # Definições de configuração
├── email_sender.py      # Funcionalidade principal de envio de e-mails
├── reports.py           # Geração e envio de relatórios
├── notifications.py     # Sistema de notificações
├── scheduler.py         # Sistema de agendamento de e-mails
├── requirements.txt     # Dependências do Python
├── .env.example         # Modelo de variáveis de ambiente
└── README.md            # Este arquivo
```

## 🚀 Início Rápido

### 1. Instalação

```bash
# Clone o repositório
git clone https://github.com/ChristopherDond/AutEmails.git
cd AutEmails

# Instale as dependências
pip install -r requirements.txt
```

### 2. Configuração

```bash
# Copie o arquivo de ambiente de exemplo
cp .env.example .env

# Edite o .env com suas configurações de SMTP
```

### 3. Executar

```bash
# Execute a demonstração
python main.py demo

# Execute o serviço de agendamento
python main.py service
```

## 📖 Uso

### Enviando um E-mail Simples

```python
from email_sender import send_quick_email

send_quick_email(
    to="recipient@example.com",
    subject="Hello!",
    body="This is a test email."
)
```

### Enviando um E-mail em HTML com Anexos

```python
from email_sender import EmailSender

with EmailSender() as sender:
    sender.send_email(
        to=["user1@example.com", "user2@example.com"],
        subject="Monthly Report",
        body="<h1>Report</h1><p>Please see attached.</p>",
        html=True,
        attachments=["report.pdf", "data.csv"]
    )
```

### Gerando e Enviando Relatórios

```python
from reports import ReportGenerator, send_report

# Dados de exemplo
data = [
    {"Name": "John", "Sales": 150},
    {"Name": "Jane", "Sales": 230},
]

# Envio rápido
send_report(
    title="Sales Report",
    data=data,
    recipients=["manager@example.com"],
    format="html"
)

# Ou use o gerador diretamente
generator = ReportGenerator()
html = generator.generate_html_report("Sales Report", data)
generator.save_report(html, "sales", "html")
```

### Enviando Notificações

```python
from notifications import (
    send_notification,
    send_alert,
    send_error_notification,
    send_success_notification
)

# Notificação simples
send_notification(
    title="Update Available",
    message="A new version is available.",
    recipients="admin@example.com",
    priority="high",
    notification_type="info"
)

# Notificação de alerta
send_alert(
    title="Server Down",
    message="Production server is not responding.",
    recipients=["admin@example.com", "devops@example.com"],
    server="prod-01",
    downtime="5 minutes"
)

# Notificação de sucesso
send_success_notification(
    title="Deployment Complete",
    message="Version 2.0 deployed successfully.",
    recipients="team@example.com"
)
```

### Agendando E-mails

```python
from scheduler import (
    get_scheduler,
    schedule_email,
    schedule_daily_report,
    ScheduleInterval
)

# Agende usando intervalos predefinidos
schedule_email(
    name="weekly_summary",
    recipients="team@example.com",
    subject="Weekly Summary",
    body_generator=lambda: "Here's your weekly summary...",
    schedule=ScheduleInterval.WEEKLY
)

# Agende usando expressão cron
schedule_email(
    name="morning_greeting",
    recipients="team@example.com",
    subject="Good Morning!",
    body_generator=lambda: "Have a great day!",
    schedule="0 9 * * 1-5"  # 9h, de segunda a sexta
)

# Agende um relatório diário
schedule_daily_report(
    name="daily_metrics",
    recipients="management@example.com",
    subject="Daily Metrics",
    data_generator=lambda: [{"Metric": "Users", "Value": 1000}],
    hour=8
)

# Inicie o agendador
scheduler = get_scheduler()
scheduler.start()
```

## ⚙️ Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-------------|---------|
| `SMTP_SERVER` | Endereço do servidor SMTP | `smtp.gmail.com` |
| `SMTP_PORT` | Porta do servidor SMTP | `587` |
| `SMTP_USERNAME` | Usuário/e-mail do SMTP | - |
| `SMTP_PASSWORD` | Senha do SMTP/senha de app | - |
| `SMTP_USE_TLS` | Usar criptografia TLS | `True` |
| `DEFAULT_SENDER` | E-mail remetente padrão | - |
| `TIMEZONE` | Fuso horário do agendador | `America/Sao_Paulo` |
| `LOG_LEVEL` | Nível de registro de logs | `INFO` |

### Configuração do Gmail

Para o Gmail, você precisa:

1. Ativar a Verificação em Duas Etapas
2. Gerar uma Senha de App:
   - Acesse Conta do Google → Segurança → Senhas de app
   - Gere uma nova senha de app para "Mail"
3. Use a senha de app em `SMTP_PASSWORD`

## 📝 Comandos da CLI

```bash
# Execute todas as demonstrações
python main.py demo

# Envie um e-mail rápido
python main.py send --to recipient@example.com --subject "Test" --body "Hello!"

# Envie e-mail em HTML
python main.py send --to recipient@example.com --subject "Test" --body "<h1>Hello!</h1>" --html

# Demonstração de geração de relatórios
python main.py report

# Demonstração de notificações
python main.py notify

# Demonstração do agendador
python main.py schedule

# Execute como serviço de agendamento
python main.py service
```

## 🔧 Tipos de Notificação e Prioridades

### Tipos de Notificação
- `info` - Informações gerais
- `success` - Mensagens de sucesso
- `warning` - Alertas de aviso
- `error` - Notificações de erro
- `alert` - Alertas críticos

### Níveis de Prioridade
- `low` - Prioridade baixa (cinza)
- `normal` - Prioridade normal (azul)
- `high` - Prioridade alta (amarelo)
- `critical` - Prioridade crítica (vermelho)

## 📅 Formato de Expressão Cron

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday = 0)
│ │ │ │ │
* * * * *
```

### Exemplos

| Expressão | Descrição |
|------------|-------------|
| `* * * * *` | A cada minuto |
| `0 * * * *` | A cada hora |
| `0 9 * * *` | Todos os dias às 9h |
| `0 9 * * 1-5` | Dias úteis às 9h |
| `0 9 1 * *` | Primeiro dia do mês às 9h |
| `*/5 * * * *` | A cada 5 minutos |

## 🤝 Contribuindo

1. Faça um fork do repositório
2. Crie sua branch de funcionalidade (`git checkout -b feature/AmazingFeature`)
3. Faça commit das suas alterações (`git commit -m 'Add some AmazingFeature'`)
4. Envie para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto é open source e está disponível sob a [Licença MIT](LICENSE).

## 👤 Autor

**ChristopherDond**

- GitHub: [@ChristopherDond](https://github.com/ChristopherDond)

---

⭐ Dê uma estrela neste repositório se ele foi útil para você!
