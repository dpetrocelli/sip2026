# Blockchain · Clase 4 — NFTs gamificados (Set Bonus) + tokenomics + Slither

> **Objetivo de la clase**: cerrar el módulo. Que al final de las 4 hs tengan **el stack completo plugado a su proyecto** (VibeCheck / DepFund / RNW / IDEAFY): `PaymentGateway` (clase 2) + ERC-20 (clase 2) + ERC-721 con **Set Bonus** (hoy) + frontend (clase 3) + análisis estático con **Slither**. El entregable del TP final cae naturalmente de acá.

> **Pre-requisitos**: clases 1, 2 y 3 hechas. Tienen `PaymentGateway` deployado en Sepolia, su token ERC-20 (`$VBK` / `$DPF` / `$RNW` / `$IDEA`), y un frontend con MetaMask conectado. **Si algo de eso no está, paren y completen primero** — sin esa base la clase de hoy no tiene dónde apoyarse.

> **Repo**: hoy seguimos en el mismo proyecto Foundry de clase 1-2 ([sip2026-blockchain-clase1](https://github.com/dpetrocelli/sip2026-blockchain-clase1)). Agregamos `BadgeNFT.sol` y los contratos de tokenomics al directorio `src/`.

> 🎯 **Lo que te vas a llevar al final de hoy** (cierre del módulo):
> - [ ] `BadgeNFT.sol` (ERC-721 con Set Bonus pattern) deployado en Sepolia
> - [ ] Tokenomics elegida y argumentada para tu proyecto (burn / dividendos / staking)
> - [ ] El stack completo funcionando: `PaymentGateway` + ERC-20 + ERC-721 + frontend
> - [ ] Análisis de Slither corrido con `SECURITY.md` documentando hallazgos
> - [ ] Tu proyecto (VibeCheck / DepFund / RNW / IDEAFY) con su lógica enchufada al hook `_onPaid`
> - [ ] Roadmap claro para el TP final — sabés qué falta y dónde van a buscar

---

## ¿Qué vamos a hacer hoy?

1. **ERC-721 base** — qué es un NFT y por qué es el estándar correcto para tickets, shares, coleccionables.
2. **Set Bonus pattern** — figuritas con piezas que combinan en sets (tipo Diablo / álbum Panini). El truco es la **gamification on-chain**.
3. **Tokenomics básica** — burn por transacción, dividendos en USDT, staking, governance, niveles de fan/inversor.
4. **Análisis estático con Slither** — correrlo sobre su `PaymentGateway` y arreglar las warnings que aparezcan.
5. **Plugar el stack a su proyecto** — exactamente qué cambia para VibeCheck vs DepFund vs RNW vs IDEAFY.
6. **Decisión de red** — Sepolia (testnet) vs Polygon vs Base vs Arbitrum (L2 de mainnet) para producción.
7. **Demo final del módulo** — qué se llevan al cerrar las 4 clases.
8. **Tarea final del TP** — el entregable.

Al cierre: cada equipo tiene el contrato completo del módulo enchufado a su proyecto, con su tokenomics propia y auditado por Slither.

---

## Parte 1 — ERC-721 base (qué es un NFT)

ERC-20 (clase 2) representa **dinero**: 100 unidades de `$VBK` son intercambiables, no tienen identidad. ERC-721 representa **ítems únicos**: cada token tiene un `tokenId` distinto, su propio dueño, su propia metadata.

| | ERC-20 (clase 2) | ERC-721 (hoy) |
|---|---|---|
| Identidad | No tiene — es un saldo | Cada token es único (`tokenId`) |
| Operaciones | `transfer`, `approve` | `transferFrom(from,to,tokenId)`, `ownerOf(tokenId)` |
| Caso de uso | Moneda interna, dividendos | Ticket, share, badge, coleccionable |
| Storage | `mapping(address => uint256) balances` | `mapping(uint256 => address) owners` |
| Metadata | symbol + name | URI por token (`tokenURI(tokenId)`) que apunta a JSON con foto, atributos, etc. |

**Cada NFT tiene:**

- Un `tokenId` (uint256 único).
- Un `ownerOf(tokenId)` (la wallet dueña).
- Un `tokenURI(tokenId)` (link a metadata, usualmente IPFS).

### El esqueleto con OpenZeppelin

No escribimos ERC-721 desde cero. Heredamos de OpenZeppelin (auditado por miles de proyectos productivos):

```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {ERC721URIStorage} from "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

contract VibeTicket is ERC721URIStorage, Ownable {
    uint256 private _nextId;

    constructor() ERC721("VibeCheck Ticket", "VIBE") Ownable(msg.sender) {}

    function mint(address to, string calldata uri) external onlyOwner returns (uint256) {
        uint256 id = ++_nextId;
        _mint(to, id);
        _setTokenURI(id, uri);
        return id;
    }

    function burn(uint256 id) external {
        require(ownerOf(id) == msg.sender, "not owner");
        _burn(id);
    }
}
```

**Línea por línea** (lo que importa):

| Pieza | Por qué |
|---|---|
| `ERC721URIStorage` | Te da `tokenURI` por token (no una URI global). |
| `Ownable` | Solo el deployer puede llamar `mint` (o quien le transfieran ownership). |
| `_mint(to, id)` | Crea el NFT y se lo asigna a `to`. **Usamos `_mint`, no `_safeMint`** — `_safeMint` rompe en fuzz tests porque chequea si `to` es contrato. |
| `_setTokenURI(id, uri)` | Guarda la metadata por token. |
| `_burn(id)` | Destruye el NFT. `ownerOf(id)` revierte después. |

> ⚡ **Soulbound = NFT que no se transfiere**. Para tickets que NO se deberían revender (fraude, reventa abusiva), se override `_update` para revertir transfers. Lo necesitan según el caso de uso (VibeCheck **sí** quiere reventa controlada, DepFund **no** quiere que el token de gobierno migre sin más).

---

## Parte 2 — Set Bonus NFT pattern (figuritas con piezas)

Acá viene la diferencia clave entre "un NFT cualquiera" y **gamification de verdad**. El patrón Set Bonus es lo que mantiene a los usuarios volviendo: **piezas random que combinan en sets más valiosos**.

**Analogía rápida**: el álbum Panini del Mundial. Tenés 18 figuritas de un equipo. Si las juntás todas, valen más que la suma de las partes. Si te falta una, vas a tradear con un amigo. Eso es Set Bonus.

### El concepto

Cada compra/inversión en su sistema mintea **una pieza random** de un grid:

- **VibeCheck**: pieza del cartel del evento (escenario, DJ, público, etc).
- **DepFund**: pieza del plano del complejo (cancha, bar, vestuarios, gym).
- **RNW**: pieza de la grilla solar/eólica (panel, inversor, batería).
- **IDEAFY**: pieza del portfolio del creador (proyecto A, B, C).

**Las piezas contiguas suman un bonus en tokenomics**:

| Piezas contiguas | Bonus típico | Ejemplo (DepFund) |
|---|---|---|
| 3 | +0.5% dividendos | "Cancha" |
| 5 | +1% dividendos + badge bronce | "Ala deportiva" |
| 8 | +2% dividendos + governance x2 | "Sector completo" |
| 12+ | NFT exclusivo + tier máximo | "Complejo fundador" |

**Rareza en cada drop**:

| Tier | Probabilidad | Qué hace |
|---|---|---|
| Común | 60% | Pieza normal |
| Rara | 25% | Pieza especial (cuenta como 1.5) |
| Épica | 12% | Wildcard parcial (encaja en cualquier slot adyacente) |
| Legendaria | 3% | Wildcard total (encaja en cualquier slot del grid) |

### Implementación mínima

```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

contract SetBonusNFT is ERC721, Ownable {
    enum Rarity { Common, Rare, Epic, Legendary }

    struct Piece {
        uint8 slot;       // 0..N — qué pieza del grid es
        Rarity rarity;
    }

    mapping(uint256 => Piece) public pieces;
    uint256 private _nextId;

    event PieceMinted(address indexed to, uint256 indexed tokenId, uint8 slot, Rarity rarity);

    constructor() ERC721("VibeCheck Pieces", "VIBE-P") Ownable(msg.sender) {}

    /// Llamado por el PaymentGateway cuando alguien paga.
    function mintRandom(address to, bytes32 entropy) external onlyOwner returns (uint256) {
        uint256 id = ++_nextId;
        uint8 slot = uint8(uint256(entropy) % 12);     // 12 slots en el grid
        Rarity rarity = _rollRarity(entropy);

        pieces[id] = Piece(slot, rarity);
        _mint(to, id);
        emit PieceMinted(to, id, slot, rarity);
        return id;
    }

    function _rollRarity(bytes32 entropy) private pure returns (Rarity) {
        uint256 r = uint256(keccak256(abi.encode(entropy, "rarity"))) % 100;
        if (r < 60) return Rarity.Common;
        if (r < 85) return Rarity.Rare;
        if (r < 97) return Rarity.Epic;
        return Rarity.Legendary;
    }

    /// Cuenta cuántos slots únicos posee `holder`.
    /// El cálculo del bonus real (off-chain o en otro contrato) usa esto.
    function uniqueSlotsOf(address holder, uint256[] calldata ids) external view returns (uint8) {
        uint16 mask;
        for (uint256 i = 0; i < ids.length; i++) {
            require(ownerOf(ids[i]) == holder, "not owner");
            mask |= uint16(1) << pieces[ids[i]].slot;
        }
        // popcount: cuántos bits están en 1
        uint8 count;
        while (mask != 0) { count += uint8(mask & 1); mask >>= 1; }
        return count;
    }
}
```

> ⚠️ **Aviso de seguridad**: `block.timestamp`/`block.prevrandao` **no son aleatorios reales**. Para producción real con dinero serio se usa **Chainlink VRF** (oracle que da randomness verificable). En la testnet del TP final, `keccak256(blockhash, sender, nonce)` alcanza para la nota — pero declarenlo explícitamente en `SECURITY.md` como riesgo conocido.

### Cómo se conecta al PaymentGateway

Cada vez que el `PaymentGateway` recibe un pago, mintea una pieza random al pagador. Es la versión "real" del `_onPaid` que dejamos como hook abstracto en clase 2:

```solidity
function _onPaid(address payer, uint256 amount, bytes32 action) internal override {
    // mintea pieza random como "loot box" cada vez que pagan
    bytes32 entropy = keccak256(abi.encode(payer, amount, block.prevrandao, action));
    setBonusNFT.mintRandom(payer, entropy);
}
```

**El loop es**: pagar → recibir pieza random → ver el grid en el frontend → si están cerca de un combo, comprar otro ticket o tradear con un amigo. El sistema crea su propia demanda.

---

## Parte 3 — Tokenomics básica

Ahora que tienen ERC-20 + ERC-721 + Set Bonus + PaymentGateway, falta atar todo con una **tokenomics que cierre**: por qué alguien compra el token, cómo se gana, cómo se gasta, cómo se sostiene en el tiempo.

### Los 4 mecanismos clásicos

| Mecanismo | Qué hace | Cuándo usarlo |
|---|---|---|
| **Burn** (1% / tx) | Quema parte del token en cada transferencia → supply baja → precio sube | $VBK, $IDEA. **Tokens utility con muchas tx.** |
| **Dividendos USDT** (mensual) | Smart contract distribuye USDT a holders proporcionalmente | $DPF, $RNW. **Tokens security con activo real detrás.** |
| **Staking** (bloquear N días) | Lockear tokens → APY extra + voto x2 | Los 4 — incentiva no vender. |
| **Governance** | Holders votan decisiones (qué proyecto se financia, ampliación, operador) | Los 4 — alinea inversor con plataforma. |

### Burn por transacción (1% / tx)

```solidity
// extiende ERC20
function _update(address from, address to, uint256 value) internal override {
    if (from != address(0) && to != address(0)) {
        uint256 burnAmount = value / 100;          // 1%
        super._update(from, address(0), burnAmount); // burn
        super._update(from, to, value - burnAmount); // resto
    } else {
        super._update(from, to, value);             // mint o burn directo
    }
}
```

> ⚠️ **Cuidado**: si una DEX (Uniswap) calcula slippage sin saber del burn, las swaps fallan. Para listing público se usa **whitelist** (la DEX queda exenta del burn). En testnet ignorenlo.

### Dividendos en USDT (DepFund / RNW / IDEAFY)

El contrato del proyecto recibe USDT mensual y lo reparte a los holders del sub-token según su balance:

```solidity
function distribute(uint256 amount) external onlyOperator {
    require(usdt.transferFrom(msg.sender, address(this), amount), "transfer failed");
    uint256 supply = totalSupply();
    accPerShare += (amount * 1e18) / supply;       // acumulador escalado
    emit Distributed(amount, supply);
}

function claim() external nonReentrant {
    uint256 owed = (balanceOf(msg.sender) * accPerShare / 1e18) - claimed[msg.sender];
    claimed[msg.sender] += owed;
    require(usdt.transfer(msg.sender, owed), "claim failed");
    emit Claimed(msg.sender, owed);
}
```

**Patrón "pull payments"**: el contrato no manda USDT a 10.000 holders (eso costaría miles en gas). Cada holder llama `claim()` cuando quiere — barato y escalable.

### Niveles de fan / inversor (gamification del holding)

| | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|---|---|---|---|---|
| **VibeCheck** | Bronce (1+ evento) | Plata (5+) | Oro (15+) | Diamante (50+) |
| **DepFund** | Seed | Growth (+$500K) | Gold (+$2M) | Whale (+$5M) |
| **RNW** | Explorer | Builder (+$1K) | Pioneer (+$10K) | Founder (+$50K) |
| **IDEAFY** | Starter (1 proyecto) | Backer (3+) | Angel (7+) | Titan (15+) |

El tier se calcula en el contrato a partir de balance + antigüedad + governance activa. Y se materializa como un **SBT (Soulbound Token)** — un NFT no transferible que es la "credencial" del usuario.

```solidity
function tierOf(address user) public view returns (uint8) {
    uint256 bal = balanceOf(user);
    uint256 stakedDays = stakingDays[user];
    if (bal >= 50_000e18 && stakedDays >= 365) return 4;  // Whale / Diamante / Founder / Titan
    if (bal >= 10_000e18 && stakedDays >= 180) return 3;
    if (bal >= 1_000e18  && stakedDays >= 90)  return 2;
    return 1;
}
```

---

## Parte 4 — Análisis estático con Slither

Antes de pasar de testnet a producción, **Slither es obligatorio**. Lee tu Solidity sin ejecutarlo y te marca vulnerabilidades automáticamente.

### Instalación

```bash
pip install slither-analyzer
slither --version
# debe responder: 0.10.x o superior
```

> Necesitás Python 3.8+. Si fallan los imports de `solc`, instalá `solc-select`: `pip install solc-select && solc-select install 0.8.24 && solc-select use 0.8.24`.

### Correrlo sobre tu PaymentGateway

Desde la raíz del repo de la clase 2:

```bash
slither . --foundry-out-directory out
```

Output típico (ejemplo de un PaymentGateway sin proteger bien):

```
Reentrancy in PaymentGateway.pay(uint256,bytes32) (src/PaymentGateway.sol#21-29):
    External calls:
    - usdc.transferFrom(msg.sender, treasury, amount)
    State variables written after the call(s):
    - emit Paid(msg.sender, amount, action)
    Severity: HIGH

PaymentGateway.pay() uses unchecked return value:
    - usdc.transferFrom(msg.sender, treasury, amount)   ← deberías usar SafeERC20
    Severity: MEDIUM
```

### Las warnings que probablemente vean (y cómo arreglarlas)

| Detector | Qué dice | Fix |
|---|---|---|
| `reentrancy-eth` / `reentrancy-no-eth` | Estado escrito después de external call | Aplicar **Checks-Effects-Interactions** (estado antes de `transferFrom`) o `nonReentrant` modifier |
| `unchecked-transfer` | Llamaste `transfer` o `transferFrom` sin chequear el return | Usar `SafeERC20.safeTransferFrom` de OpenZeppelin |
| `tx-origin` | Auth con `tx.origin` | Reemplazar por `msg.sender`. `tx.origin` es vulnerable a phishing. |
| `solc-version` | Versión muy vieja o muy nueva | Pinear `pragma solidity 0.8.24;` |
| `pragma` | Wildcard `^` permite versiones futuras | Lo mismo: pinear exacto |
| `naming-convention` | Constants no en UPPER_CASE | Cosmético — opcional |
| `low-level-calls` | Usaste `.call{value: ...}("")` | Si es a propósito (forwardear ETH), agregar comentario `// slither-disable-next-line low-level-calls` |

### Documentar lo que NO arreglás

Si una warning queda como acepted-risk (ej: usar `block.prevrandao` para randomness no crítica), agregalo a `SECURITY.md`:

```markdown
## Findings aceptados

- **Pseudo-randomness en SetBonusNFT.mintRandom**: usamos `keccak256(blockhash, sender)` 
  porque las piezas son cosméticas y el costo de Chainlink VRF no se justifica en testnet.
  En producción se migra a VRF.
- **Burn 1% / tx en el token del proyecto**: warning de slippage en DEX. Mitigación: whitelist de pools.
```

> 🎯 **Lo que el TP final pide**: corrieron Slither, hay 0 findings de severidad HIGH, los MEDIUM están justificados en `SECURITY.md`.

---

## Parte 5 — Cómo plugar el stack a tu proyecto

Esta es la parte donde **cada equipo divergente**. La pieza común son los 4 contratos:

```
PaymentGateway (clase 2)
   ↓ recibe USDC
   ↓ llama _onPaid()
ERC-20 del proyecto (clase 2)
   ↓ mintea / quema / distribuye
ERC-721 del proyecto (hoy)
   ↓ mintea pieza Set Bonus
Tier / Governance (hoy)
   ↓ recalcula tier del usuario
```

Lo que cambia es **qué dispara cada cosa**. Tabla:

### Mapa proyecto por proyecto

| | **VibeCheck** | **DepFund** | **RNW** | **IDEAFY** |
|---|---|---|---|---|
| **Disparador del pago** | Compra de entrada para evento | Inversión en complejo deportivo | Inversión en parque solar/eólico | Inversión en proyecto del creador |
| **Lo que mintea el `_onPaid`** | Ticket NFT (con `eventId`, fila, asiento) + 10 $VBK | Shares de $DPF proporcionales | $RNW + registro de perfil de riesgo (inicial / consolidado) | Sub-token del proyecto (`$IDEA-CERV`) + 1 pieza |
| **Set Bonus drop** | 1 pieza del cartel del evento | 1 pieza del plano del complejo | 1 pieza de la grilla solar | 1 pieza del portfolio del creador |
| **Tokenomics activa** | Burn 2%/tx + cashback 2% en $VBK | Dividendos USDT mensuales | Dividendos USDT + staking +2% APY | Burn 1%/tx en $IDEA + dividendos USDT en sub-tokens |
| **Governance activa** | Holders votan features de plataforma | Holders votan ampliaciones (pileta, gym, operador) | Holders votan qué proyecto se financia próximo | Holders de $IDEA votan qué proyectos se aprueban |
| **Tier que calcula el SBT** | Bronce → Diamante por asistencia | Seed → Whale por monto + governance | Explorer → Founder por staking | Starter → Titan por proyectos fondeados |

### Esqueleto del `_onPaid` por proyecto

**VibeCheck** — `_onPaid` mintea ticket NFT y reparte $VBK al fan:

```solidity
function _onPaid(address payer, uint256 amount, bytes32 action) internal override {
    // 1. Mintea ticket NFT
    uint256 ticketId = ticketNFT.mint(payer, _eventURI(action));
    // 2. Reparte $VBK como cashback (2%)
    vbk.mint(payer, (amount * 2) / 100);
    // 3. Pieza Set Bonus random
    bytes32 entropy = keccak256(abi.encode(payer, amount, block.prevrandao));
    pieces.mintRandom(payer, entropy);
    // 4. Recalcula tier
    tierRegistry.refresh(payer);
}
```

**DepFund** — `_onPaid` emite shares del complejo:

```solidity
function _onPaid(address payer, uint256 amount, bytes32 action) internal override {
    // amount es el USDC invertido. action codifica el complexId.
    uint256 shares = (amount * 1e18) / pricePerShare;
    dpf.mint(payer, shares);                       // shares del complejo
    pieces.mintRandom(payer, _entropy(payer, action));
    investorRegistry.recordInvestment(payer, action, amount);
}
```

**RNW** — `_onPaid` registra inversor con su perfil de riesgo:

```solidity
function _onPaid(address payer, uint256 amount, bytes32 action) internal override {
    // action codifica projectId + perfil (inicial / consolidado)
    (bytes32 projectId, uint8 riskProfile) = _decode(action);
    uint256 tokens = (amount * 1e18) / pricePerToken[projectId];
    rnw.mint(payer, tokens);
    riskProfiles[payer][projectId] = riskProfile; // Inicial = 0, Consolidado = 1
    pieces.mintRandom(payer, _entropy(payer, action));
}
```

**IDEAFY** — `_onPaid` rutea al sub-token del proyecto:

```solidity
function _onPaid(address payer, uint256 amount, bytes32 action) internal override {
    bytes32 projectId = action;                    // ej: keccak256("CERV")
    SubToken sub = subTokens[projectId];
    require(address(sub) != address(0), "unknown project");
    uint256 amt = (amount * 1e18) / sub.pricePerToken();
    sub.mint(payer, amt);                          // $IDEA-CERV, $IDEA-PIZZA, etc.
    pieces.mintRandom(payer, _entropy(payer, action));
}
```

> 💡 **El truco está en `bytes32 action`**. Es 32 bytes libres que cada equipo usa para codificar **lo que su proyecto necesita**: para VibeCheck es `eventId`, para DepFund es `complexId`, para RNW es `projectId | riskProfile`, para IDEAFY es `projectId`. Mismo `PaymentGateway`, semántica distinta.

---

## Parte 6 — Decisiones de arquitectura: qué red usar para producción

Hasta acá deployamos todo en **Sepolia** (testnet de Ethereum L1). Para producción, **L1 mainnet sale carísimo** — un mint cuesta $5-20 USD en gas. Para sus proyectos van a usar una **L2** (rollup que hereda seguridad de Ethereum pero ejecuta más barato).

### Comparativa rápida

| | Ethereum L1 | **Polygon** | **Base** | **Arbitrum** |
|---|---|---|---|---|
| Costo / tx | ~$2-20 USD | ~$0.001 | ~$0.01 | ~$0.05 |
| Tiempo bloque | 12 s | 2 s | 2 s | 0.25 s |
| EVM compat | Nativo | 100% | 100% (es OP rollup) | 100% (es OP rollup) |
| Quién está atrás | Ethereum Foundation | Polygon Labs | Coinbase | Offchain Labs |
| Stablecoins nativas | USDC, USDT | USDC, USDT, DAI | USDC oficial | USDC, USDT |
| Wallet support | MetaMask out of the box | MetaMask + 1 click | MetaMask + 1 click | MetaMask + 1 click |
| Adopción Argentina | Bombo, Lemon, Belo | Lemon, Buenbit (transfer) | Coinbase users | Mercado DeFi-fi |

### Cuál elegir según el proyecto

| Si tu proyecto es… | Recomendación | Por qué |
|---|---|---|
| **VibeCheck** (muchas tx chicas, fans casuales) | **Polygon** | Costo ínfimo. 5.000 tickets / mes = $5 USD total en gas. |
| **DepFund** (pocas tx, montos grandes) | **Base** | Coinbase ecosystem, USDC nativa, regulatorio más prolijo. |
| **RNW** (oracle de IoT, datos kWh) | **Polygon** o **Arbitrum** | Ambos tienen Chainlink stable. Polygon es más barato. |
| **IDEAFY** (multi-rubro, sub-tokens) | **Base** | Mejor stack de DeFi para liquidity de sub-tokens. |

> 🎯 **Para el TP**: Sepolia es obligatorio (gratis). Si **además** deployan en Polygon/Base/Arbitrum testnet (Mumbai, Base Sepolia, Arbitrum Sepolia respectivamente), suma puntos. Mainnet **NO** es obligatorio — no quiero que alguien queme USD reales por error.

### Lo que cambia para mover Sepolia → otra red

**Foundry**: solo cambia `--rpc-url` y la API key del explorer:

```bash
# Sepolia
forge create ... --rpc-url https://ethereum-sepolia-rpc.publicnode.com --account dev

# Base Sepolia
forge create ... --rpc-url https://sepolia.base.org --account dev

# Polygon Amoy (testnet)
forge create ... --rpc-url https://rpc-amoy.polygon.technology --account dev

# Arbitrum Sepolia
forge create ... --rpc-url https://sepolia-rollup.arbitrum.io/rpc --account dev
```

**Frontend (wagmi)**: cambia 1 import:

```ts
import { sepolia, baseSepolia, polygonAmoy, arbitrumSepolia } from 'wagmi/chains';

export const config = getDefaultConfig({
  appName: 'TuProyecto',
  projectId: 'tu_walletconnect_id',
  chains: [sepolia, baseSepolia],   // multi-chain si querés
  ssr: true,
});
```

**MetaMask**: la primera vez te pide aprobar la red nueva. Aceptar.

---

## Parte 7 — Demo final del módulo (qué se llevan)

Después de las 4 clases, cada equipo tiene en producción (testnet):

- [ ] **`PaymentGateway`** que cobra USDC + emite evento `Paid` + protección reentrancy (clase 2).
- [ ] **ERC-20** propio del proyecto (`$VBK` / `$DPF` / `$RNW` / `$IDEA`) con burn / dividendos / staking según corresponda.
- [ ] **ERC-721 Set Bonus** que mintea piezas random con rareza (hoy).
- [ ] **Frontend Next.js** con wagmi + RainbowKit, conectado a su contrato (clase 3).
- [ ] **Análisis Slither** con 0 findings HIGH y `SECURITY.md` que documenta los MEDIUM (hoy).
- [ ] Todo deployado en Sepolia (mínimo) o además en Base/Polygon/Arbitrum testnet.
- [ ] Verificado en Etherscan / Basescan.

> 🎉 Cada equipo tiene **su pasarela de pago Web3 corriendo end-to-end**, con su tokenomics, su gamification, y su frontend público. El módulo blockchain del SIP cierra acá.

---

## Cierre — qué nos llevamos del módulo

Cuatro clases. Empezamos con MetaMask y un `SimpleStorage` trivial. Cerramos con **un sistema Web3 productivo** plugado a su proyecto del SIP, con tokenomics, gamification y auditoría.

> **El contrato es una pieza más del sistema**, no es todo. Su backend Web2 sigue ahí. Su frontend sigue ahí. Su observabilidad de TP2 sigue ahí. Lo que reemplazaron fue **MercadoPago por un smart contract que ustedes escribieron, controlan, y pueden auditar línea por línea**. Eso es lo que diferencia su TP final del SIP de un proyecto Web2 más.

---

## Tarea para próxima clase

La tarea va en una página aparte: [Tarea de clase 4](blockchain-clase-4-tarea.html).
