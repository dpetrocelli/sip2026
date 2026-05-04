# Blockchain · Tarea de clase 2 — PaymentGateway en Sepolia

> **Plazo**: antes de clase 3 (sábado 23/05).

> **Pre-requisito**: la [clase 2 completa](blockchain-clase-2.html) — `PaymentGateway.sol`, `ProjectToken.sol`, OpenZeppelin instalado, tests pasando.

---

## Qué hay que entregar

Antes del próximo sábado, en el campus:

1. **`PaymentGateway` deployado en Sepolia + verificado en Etherscan**.
   - Entregable: la URL `https://sepolia.etherscan.io/address/<GATEWAY>#code`.
2. **Hicieron al menos 2 pagos desde `cast`** con `action` distintas (por ejemplo `"primera-prueba"` y `"segunda-prueba"`).
   - Entregable: las **2 URLs de tx** en Etherscan (`https://sepolia.etherscan.io/tx/<TX_HASH>`).
3. **Tu address de `treasury` muestra el saldo USDC acumulado** después de los pagos (verificable con `cast call ... balanceOf`).
4. **(Bonus)** Escriban un test que **intente reentrancy** contra `PaymentGateway` y comprueben que falla. Pista: hagan que `_onPaid` haga algo arbitrario en una subclass de prueba que reentre `pay()`.

---

## Cómo probar que está bien

Checklist de aceptación:

- [ ] `forge install OpenZeppelin/openzeppelin-contracts --no-commit` corrió OK y `lib/openzeppelin-contracts` existe.
- [ ] `remappings.txt` incluye `@openzeppelin/contracts/=lib/openzeppelin-contracts/contracts/`.
- [ ] `forge build` compila sin warnings (o solo cosméticas).
- [ ] `forge test -vv` muestra los **5 tests en verde** (incluido el fuzz `testFuzz_PayAnyValidAmount`).
- [ ] El deploy con el script `DeployPaymentGateway.s.sol` te devolvió la address y la guardaste como `$GATEWAY`.
- [ ] `forge verify-contract` terminó con `Pass — Verified`. Etherscan muestra el source completo.
- [ ] Tenés USDC de testnet en tu wallet (faucet de Circle: https://faucet.circle.com).
- [ ] `cast send` de `approve(...)` se confirmó (status: 1).
- [ ] `cast send` de `pay(uint256,bytes32)` se confirmó (status: 1) y el receipt incluye el evento `Paid`.
- [ ] La pestaña **"Events"** del PaymentGateway en Etherscan lista los `Paid(payer, amount, action)` con tu address.
- [ ] `cast call $USDC_SEPOLIA "balanceOf(address)(uint256)" $TREASURY` devuelve la suma de los pagos.
- [ ] Tu `ProjectToken` (`$VBK` / `$DPF` / `$RNW` / `$IDEA`) **también está deployado** — la van a necesitar en clase 4.

---

## Si algo falla

| Síntoma | Causa probable | Fix |
|---|---|---|
| `Error: ERC20: insufficient allowance` | No aprobaste o aprobaste menos que el `pay` | Re-aprobá con la cantidad correcta (paso 8.1 de la clase) |
| `Error: ERC20: transfer amount exceeds balance` | No tenés USDC en tu wallet | Pedí USDC al faucet de Circle |
| `Error: gateway.pay reverted` sin razón clara | El allowance está en 0 (o expiró) | Aprobá de nuevo |
| `forge install` falla | Sin red, o submodules confundidos | `forge install --no-git` o `git submodule update --init --recursive` |
| El test fuzz falla en algún input | Posible bug | Subir el rango con `vm.assume` o revisar lógica |
| `verify-contract` dice "Already Verified" | Está OK, ya lo tenías verificado | Ignorar — lo abrís y está bien |
| Etherscan no muestra el evento | A veces tarda 30-60s | Refrescar después de un minuto |

---

## Volver

- [← Material de la clase 2](blockchain-clase-2.html)
- [← Volver al índice](index.html)
- [→ Clase 3 — Frontend + onramp](blockchain-clase-3.html)
