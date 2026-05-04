# Blockchain · Tarea de clase 4 — Entregable final del módulo

> **Plazo**: antes del cierre del SIP 2026 (la fecha exacta del TP final la define el cronograma del seminario).

> **Pre-requisito**: las [clases 1](blockchain-clase-1.html), [2](blockchain-clase-2.html), [3](blockchain-clase-3.html) y [4](blockchain-clase-4.html) completas. Tienen el stack: `PaymentGateway` + ERC-20 propio + ERC-721 Set Bonus + frontend en Vercel.

---

## Qué hay que entregar

### 1. Repo en GitHub

Estructura mínima:

```
.
├── contracts/        # los 4 contratos
│   ├── PaymentGateway.sol
│   ├── ProjectToken.sol      # tu ERC-20 ($VBK / $DPF / $RNW / $IDEA)
│   ├── SetBonusNFT.sol       # ERC-721 con piezas + rareza
│   └── TierRegistry.sol      # SBT con tier del usuario
├── frontend/         # Next.js + wagmi conectado al stack
├── test/             # tests Foundry
│   ├── PaymentGateway.t.sol
│   ├── SetBonusNFT.t.sol
│   └── …
├── SECURITY.md       # output de Slither + findings aceptados
└── README.md         # addresses en testnet, pasos para correr
```

Requisitos de los tests:

- Coverage ≥ **70%**.
- Al menos **2 fuzz tests**.
- Test de Set Bonus (que se mintea, que la rareza se calcula, que `uniqueSlotsOf` cuenta bien).

### 2. Demo en vivo (5 min en clase)

Tienen que mostrar:

- Conectar wallet desde el frontend deployado en **Vercel**.
- **Pagar con USDC de testnet** → ver que se mintea el ERC-20 + el ticket/share NFT + la pieza Set Bonus.
- Mostrar el evento `Paid` (y los eventos del NFT) en **Etherscan**.
- Mostrar el output de **Slither** limpio (0 findings HIGH).

### 3. Defensa (5 min)

- Por qué eligieron **esa red** para producción (Polygon / Base / Arbitrum / quedarse en Sepolia).
- Qué **riesgos** quedan abiertos (randomness pseudo, slippage de DEX por burn, dependencia de oráculos…).
- Qué falta para llevarlo a **mainnet real**.

---

## Cómo probar que está bien

Checklist de aceptación — usenlo como checklist antes de subir el TP:

### Contratos

- [ ] `forge build` compila sin errores ni warnings (o solo cosméticas justificadas).
- [ ] `forge test -vv` pasa todos los tests.
- [ ] `forge coverage` reporta ≥ 70% line coverage.
- [ ] Hay al menos 2 fuzz tests (`testFuzz_*`).
- [ ] El test del Set Bonus verifica: mint con entropy, rareza dentro de los rangos esperados, `uniqueSlotsOf` correcto.
- [ ] **`_safeMint` no se usa en fuzz tests** — usan `_mint` o filtran `to` con `vm.assume(to.code.length == 0)`.

### Slither

- [ ] `slither --version` responde sin error.
- [ ] `slither . --foundry-out-directory out` corre limpio.
- [ ] **0 findings de severidad HIGH**.
- [ ] Findings MEDIUM están **documentados en `SECURITY.md`** con justificación (acepted-risk).
- [ ] `SECURITY.md` incluye explícitamente la limitación de **pseudo-randomness** del Set Bonus si la usan.

### Deploy

- [ ] `PaymentGateway`, `ProjectToken`, `SetBonusNFT` y `TierRegistry` deployados en **Sepolia** y verificados en Etherscan.
- [ ] El `_onPaid` del `PaymentGateway` realmente plugea con **el stack del proyecto** (mint NFT, mint pieza, refresh tier).
- [ ] `README.md` lista las **addresses** de los 4 contratos.
- [ ] (Bonus) Mismo stack deployado además en una L2 testnet (Base Sepolia / Polygon Amoy / Arbitrum Sepolia).

### Frontend

- [ ] La dApp en Vercel **conecta wallet, paga, mintea NFT, muestra el evento**.
- [ ] La pieza Set Bonus se ve en la UI (al menos `tokenId` + `slot` + `rarity`).
- [ ] El tier del usuario aparece en alguna parte de la UI.
- [ ] `README.md` documenta las env vars `NEXT_PUBLIC_*` necesarias (sin secrets).

### Tokenomics + gamification

- [ ] Tokenomics activa coherente con el proyecto (burn / dividendos / staking / governance, según corresponda).
- [ ] Set Bonus drop con las 4 rarezas (Common 60%, Rare 25%, Epic 12%, Legendary 3%).
- [ ] El `_onPaid` del proyecto codifica `bytes32 action` con la semántica que necesita (`eventId`, `complexId`, `projectId|riskProfile`, etc.).

### Defensa

- [ ] Tienen claro **por qué** la red elegida para producción.
- [ ] Pueden listar al menos **3 riesgos abiertos**.
- [ ] Saben qué falta para mainnet (auditoría externa, seguros, KYC/AML del onramp, etc.).

---

## Criterios de evaluación (alineados con el SIP)

| Criterio | Peso |
|---|---|
| Contratos compilan + pasan tests | 25% |
| Tokenomics coherente con el proyecto + documentada | 20% |
| Frontend conecta y ejecuta el flow completo | 20% |
| Slither limpio + `SECURITY.md` honesto | 15% |
| Set Bonus funcional + visualizable | 10% |
| Demo + defensa | 10% |

---

## Si algo falla

| Síntoma | Probable causa | Fix |
|---|---|---|
| `slither: command not found` | No está en PATH | `pip install --user slither-analyzer` y agregar `~/.local/bin` al PATH |
| `slither` falla con "Source not found" | Foundry layout no detectado | `slither . --foundry-out-directory out` o `slither src/` |
| `solc not installed for 0.8.24` | Versión no instalada | `solc-select install 0.8.24 && solc-select use 0.8.24` |
| `_safeMint` revierte en fuzz tests | Foundry envía a addresses que no implementan `onERC721Received` | Usar `_mint` (sin "safe") o filtrar `to` con `vm.assume(to.code.length == 0)` |
| `nonReentrant` revierte llamadas válidas | Estás llamando dos funciones `nonReentrant` en la misma tx | Mover lógica interna a función `private` (sin guard) |
| El Set Bonus siempre da el mismo slot | `entropy` no incluye `block.prevrandao` o `nonce` | Agregar `block.prevrandao` y un nonce que se incremente |
| Slither marca `unchecked-transfer` en USDT | USDT real no devuelve bool | Usar `SafeERC20.safeTransferFrom` (OpenZeppelin) |
| `forge create` en Polygon Amoy revierte | Faucet de Amoy escaso | Probar https://faucet.polygon.technology o pedir en el foro del campus |
| Frontend no muestra la pieza NFT | El RPC no devolvió `tokenURI` aún (cache) | Esperar 30 s, o invalidar query con `queryClient.invalidateQueries` |
| Dividendos `claim()` devuelve 0 | El distribute fue antes de tu compra | Es correcto — el `accPerShare` solo cuenta hacia adelante. Ese es el patrón. |

Lo demás, foro del campus.

---

## Volver

- [← Material de la clase 4](blockchain-clase-4.html)
- [← Volver al índice](index.html)
- [→ Trabajo final del SIP](practica-2-parte-4.html)
