# Blockchain · Tarea de clase 1 — SimpleStorage en Sepolia

> **Plazo**: antes de clase 2 (sábado 16/05).

> **Pre-requisito**: la [clase 1 completa](blockchain-clase-1.html) — MetaMask + Sepolia + Foundry + el repo de la clase clonado.

---

## Qué hay que entregar

Antes del próximo sábado, en el campus:

1. Tu contrato `SimpleStorage` **deployado y verificado en Sepolia**.
   - Entregable: la URL `https://sepolia.etherscan.io/address/<TU_ADDR>#code` donde se vea el source.
2. **Llamaste `set(N)` al menos una vez** con un número significativo para vos. Lo van a poder ver en la pestaña **Events** del contrato en Etherscan.
3. Leyeron el [overview de blockchain](blockchain-overview.html), prestando atención especialmente a los **5 diagramas**.

---

## Cómo probar que está bien

Checklist de aceptación — si todos los items dan ✅, está listo para entregar:

- [ ] MetaMask tiene la red **Sepolia** activa y al menos `~0.1 ETH` de faucet.
- [ ] `forge --version` responde sin error en tu terminal.
- [ ] El repo de la clase compila: `forge build` termina con `Compiler run successful!`.
- [ ] Los tests pasan: `forge test -vv` muestra 3 tests en verde.
- [ ] Importaste tu wallet a Foundry con `cast wallet import dev --interactive` (queda en `~/.foundry/keystores/dev`).
- [ ] El deploy con `forge create ... --account dev --broadcast` te devolvió un `Deployed to: 0x...`.
- [ ] `cast call $ADDR "get()(uint256)"` te devuelve el valor que seteaste.
- [ ] Etherscan muestra el **source verificado** (pestaña "Contract" con el código `.sol`, no solo bytecode).
- [ ] La pestaña **"Events"** lista al menos un `ValueChanged(address,uint256)` con tu address y tu número.

---

## Si algo falla

| Síntoma | Probable causa | Fix |
|---|---|---|
| `forge: command not found` | Foundry no está en el PATH | Reabrí terminal o `source ~/.bashrc` después de instalar |
| `Error: insufficient funds` | No tenés ETH en Sepolia | Volvé al faucet (paso 2.3 de la clase) |
| `Error: nonce too high/low` | MetaMask y Foundry desfasados | En MetaMask: Settings → Advanced → Reset Account |
| `Error: failed to verify` | API key de Etherscan mal pegada | Verificá `echo $ETHERSCAN_API_KEY` |
| MetaMask no muestra Sepolia | Test networks ocultas | Settings → Advanced → Show test networks |

---

## Volver

- [← Material de la clase 1](blockchain-clase-1.html)
- [← Volver al índice](index.html)
- [→ Clase 2 — ERC-20 + PaymentGateway](blockchain-clase-2.html)
