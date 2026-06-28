# Regras

- Validar JSON, `project.json`, profile, artefatos obrigatorios e gaps explicitos.
- Tratar `valid:true` com warnings relevantes como conhecimento ainda nao pronto para uso operacional.
- Verificar se `hardening/initial-gaps.json` contem lacunas reais, nao apenas placeholder.
- Sinalizar artefatos de dominio rasos que contenham apenas termos frequentes sem fatos rastreaveis.
- Nao alterar a pasta validada; apenas reportar status e correcoes.
- Reprovar artefatos que exponham segredos brutos ou paths absolutos indevidos.
