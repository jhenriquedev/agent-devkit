# Regras

- Ler workbook existente sem modificar arquivo de origem.
- Usar `sheet` e `range` quando informados; caso contrario detectar ranges utilizaveis de forma conservadora.
- Preservar tipos, formulas observadas e valores exibidos quando possivel.
- Reportar abas vazias, merged cells e estruturas ambíguas como lacunas.
- Nao tratar workbook como template registrado sem metadados.
- Gerar dados extraidos como artefato separado.
