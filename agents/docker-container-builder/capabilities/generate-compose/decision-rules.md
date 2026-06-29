# Decision Rules

- Compose e para desenvolvimento local por padrao.
- Nao gerar `privileged`.
- Nao gerar `network_mode: host`.
- Nao montar `/` ou diretorios sensiveis do host.
- Variaveis devem ser referencias, nao valores secretos.
