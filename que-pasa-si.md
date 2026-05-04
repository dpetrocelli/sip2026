# Qué pasa si... — escenarios reales que vas a encontrar

> Esta página es una **referencia de realidad**: cosas que vas a vivir mientras desarrollás (y cosas que vivirías si esto fuera mainnet). Ordenado por momento del flujo: setup → desarrollo → producción → casos límite → caso real consolidado.

> No es lectura lineal. Hacé `ctrl-F` cuando algo te explote.

---

## Bloque 1 · Setup y primeros pasos

### ¿Qué pasa si... el faucet de Sepolia no me da ETH?

Los faucets racionan: te dan 0.5 ETH cada 24 hs y a veces directamente niegan IPs sospechosas, redes universitarias o VPNs. Probá en orden: [Google Cloud Web3 Faucet](https://cloud.google.com/application/web3/faucet/ethereum/sepolia) (el más generoso, pide login Google), [Alchemy Sepolia Faucet](https://www.alchemy.com/faucets/ethereum-sepolia) (pide cuenta gratis), [Infura](https://www.infura.io/faucet/sepolia) y [PoW Faucet](https://sepolia-faucet.pk910.de/) (te hace minar localmente — funciona cuando todo lo demás falla). Si nada anda, el camino más rápido es pedirle a un compañero del equipo que te transfiera 0.05 ETH desde su wallet — no necesitás más para deployar todo el TP.

### ¿Qué pasa si... `forge install` falla por timeout?

Foundry clona dependencias desde GitHub con submódulos. Si estás detrás de VPN, en una red universitaria con proxy, o el CDN te llega lento, te tira `error: failed to clone` después de 30-60s. Plan B:

```bash
git clone https://github.com/OpenZeppelin/openzeppelin-contracts.git \
  lib/openzeppelin-contracts --depth 1
forge install --no-git OpenZeppelin/openzeppelin-contracts
```

Si seguís igual, configurá git para usar HTTPS en lugar de SSH (`git config --global url."https://github.com/".insteadOf git@github.com:`) y reintentá.

### ¿Qué pasa si... importo la PK de mi cuenta personal de MetaMask en Foundry?

**No lo hagas.** Esa PK probablemente esté asociada a tu cuenta de mainnet, NFTs reales, ENS, o histórico que no querés exponer. Si por error pegás esa PK en `cast wallet import` y después subís el `.env` a git con un RPC URL, cualquiera con acceso al repo puede ver el address y empezar a investigarte. **Regla**: creá una **cuenta nueva en MetaMask** ("+ Add account") exclusiva para dev, fondeala con faucet, y solo esa la importás a Foundry. Si te equivocaste y ya pegaste la PK personal, asumí que está comprometida y movete a una wallet nueva ya.

### ¿Qué pasa si... pierdo la frase BIP-39 de mi wallet de dev?

No hay recovery. Esas 12 palabras son la **única** forma de regenerar las private keys. Si las perdiste y todavía tenés MetaMask desbloqueado en una computadora, exportá cada PK ya (`⋮ → Account details → Show private key`) antes de que se cierre la sesión. Si ya no tenés acceso, los fondos y los contratos quedan bajo una wallet a la que no podés volver — la solución pragmática para el TP es **crear una wallet nueva, redeployar los contratos y actualizar las addresses en el frontend**. En testnet no perdiste plata real; en mainnet sería fatal.

---

## Bloque 2 · Mientras desarrollás (clase 2 - 3)

### ¿Qué pasa si... me olvido del `approve` antes del `pay()`?

Esto pasa al **80%** de los equipos en clase 2 y 3. Llamás `gateway.pay(50_000_000, ...)` directo y la tx revierte con `ERC20InsufficientAllowance` (en OZ moderno) o un `TransferFrom failed` genérico (en versiones viejas). El `PaymentGateway` no puede mover tus USDC sin permiso previo. Patrón correcto, siempre dos transacciones:

```bash
cast send $USDC "approve(address,uint256)" $GATEWAY 50000000 --account dev
cast send $GATEWAY "pay(uint256,bytes32)" 50000000 $ACTION --account dev
```

En el frontend, fijate que `PayForm` chequea `allowance < amountWei` antes de mostrar el botón "Pay" — esa lógica existe justamente para no dejarte llamar `pay` sin allowance suficiente.

### ¿Qué pasa si... `forge create` se cuelga 30s?

Es normal. Sepolia mina un bloque cada ~12 segundos y a veces toca esperar 2 bloques + propagación del RPC. Si pasaron 60s y nada, abrí otra terminal y chequeá si la tx ya está en mempool o minada:

```bash
cast tx <tx_hash> --rpc-url $SEPOLIA_RPC_URL
# o, si todavía no tenés el hash, mirá el nonce de tu address:
cast nonce $(cast wallet address --account dev) --rpc-url $SEPOLIA_RPC_URL
```

Si el nonce subió, la tx salió, solo está esperando confirmación. Si no, probablemente el RPC no la propagó — cambiá de RPC y reintentá con el mismo nonce.

### ¿Qué pasa si... MetaMask no muestra mis USDC del contrato?

MetaMask no detecta tokens automáticamente — solo muestra ETH y los tokens que **importaste manualmente**. Andá a la pestaña "Tokens" → "Import tokens" → "Custom token" → pegá la address (`0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238` para USDC oficial Sepolia, o tu MockUSDC si usaste el del onramp de clase 3). MetaMask completa nombre, símbolo y decimales solo. Si te dice "Token not found", probablemente estás en la red equivocada (chequeá que arriba diga "Sepolia").

### ¿Qué pasa si... mi RPC público devuelve 429 / timeout?

`https://ethereum-sepolia-rpc.publicnode.com` es público y gratis pero tiene rate-limit agresivo. Cuando 30 alumnos en la misma clase pegan al mismo endpoint, cae. Fallbacks que funcionan:

```bash
SEPOLIA_RPC_URL=https://sepolia.gateway.tenderly.co
# o
SEPOLIA_RPC_URL=https://ethereum-sepolia.publicnode.com
# o (mejor performance, gratis con cuenta):
SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/<API_KEY>
```

Para producción de verdad, registrate en [Alchemy](https://www.alchemy.com) o [Infura](https://www.infura.io) — el free tier (300M compute units / mes) alcanza para todo el TP y la demo.

### ¿Qué pasa si... viem en el frontend dice `ConnectorNotFoundError`?

Tres causas, en orden de frecuencia:

1. **Falta el `WagmiProvider`** envolviendo a tu componente. Mirá `app/providers.tsx` — tiene que estar en el `layout.tsx`.
2. **`projectId` de WalletConnect vacío o mal copiado** desde [cloud.reown.com](https://cloud.reown.com). Verificá `process.env.NEXT_PUBLIC_WC_PROJECT_ID` en runtime con un `console.log`.
3. **No hay wallet en el browser**. Si abrís `localhost:3000` en Brave/Chrome sin extensión MetaMask instalada, no hay nada a lo que conectarse — RainbowKit te muestra el modal pero al clickear "MetaMask" tira el error.

Checklist: `chains: [sepolia]` declarado, `ssr: true` para Next.js App Router, `projectId` no vacío, MetaMask instalada y desbloqueada.

### ¿Qué pasa si... wagmi me dice "user rejected request"?

El usuario clickeó "Reject" en el popup de MetaMask. Es un caso normal, no un bug — manejá el error en la UI y mostrá algo como "Cancelaste la firma. Volvé a intentar cuando quieras":

```ts
const { writeContract, error } = useWriteContract();

if (error?.message.includes('User rejected')) {
  return <p className="text-yellow-700">Firma cancelada. Reintentá.</p>;
}
```

No relances la tx automáticamente — eso abre un loop infinito de popups y los usuarios odian eso.

---

## Bloque 3 · Producción real (lo que pasa si fuera mainnet)

### ¿Qué pasa si... alguien hace front-running de mi tx? — MEV ⚡

**MEV** (Maximal Extractable Value) es el negocio de bots searchers que escuchan el mempool público de Ethereum, detectan transacciones rentables (típicamente swaps grandes en Uniswap), y mandan la suya con **gas más alto** para entrar antes en el bloque. El validador prioriza por gas → el bot gana, vos perdés.

Para una pasarela de pago como `PaymentGateway.pay(amount, action)` el impacto es **bajo**: nadie gana plata adelantándose a que pagues USDC al treasury. Donde el MEV duele de verdad es en **AMMs** (Uniswap, Curve), liquidaciones de Aave/Compound, y mints de NFTs hot. Mitigaciones reales:

- **Flashbots Protect RPC** ([rpc.flashbots.net](https://rpc.flashbots.net)) — manda tu tx por mempool privado.
- **MEV Blocker** ([rpc.mevblocker.io](https://rpc.mevblocker.io)) — alternativa gratuita que además te paga rebates.
- **Slippage tolerances** ajustados (ver siguiente entrada).

### ¿Qué pasa si... el precio se mueve entre que firmo y se confirma? — Slippage

Entre que firmás `swap(100 USDC → DPF)` y el bloque te confirma pasaron 12 segundos, en los que el precio del par puede haberse movido. Si el contrato no chequea, recibís menos tokens de los esperados.

Para `PaymentGateway` con USDC esto es **irrelevante** — USDC es estable y `pay(50_000_000, action)` te cobra exactamente 50 USDC, no hay margen. Pero si tu `_onPaid` calcula shares con un `pricePerShare` dinámico (DepFund: `shares = amount / pricePerShare`), el patrón estándar es exigir un `minOutputAmount` del cliente:

```solidity
function pay(uint256 amount, bytes32 action, uint256 minShares) external nonReentrant {
    usdc.safeTransferFrom(msg.sender, treasury, amount);
    uint256 shares = (amount * 1e18) / pricePerShare;
    require(shares >= minShares, "slippage");
    dpf.mint(msg.sender, shares);
}
```

Uniswap, 1inch y Cowswap usan esta forma exacta — el frontend calcula `minShares = expectedShares * 0.99` (1% slippage) y lo manda como parámetro.

### ¿Qué pasa si... la red se congestiona y mi tx queda pending? — Gas escalation

Cuando hay un mint de NFT viral, un airdrop de un token nuevo, o una liquidación masiva, el gas price se va al techo y tu tx con `priority_fee=1 gwei` queda en mempool una hora. Dos opciones:

```bash
# 1. Bumpear la misma tx (mismo nonce, más gas):
cast send $GATEWAY "pay(uint256,bytes32)" 50000000 $ACTION \
  --nonce 42 \
  --priority-gas-price 5gwei \
  --gas-price 50gwei \
  --account dev

# 2. Cancelarla mandando una tx vacía a vos mismo con el mismo nonce + gas mayor:
cast send $(cast wallet address --account dev) \
  --value 0 --nonce 42 \
  --priority-gas-price 5gwei --account dev
```

En MetaMask UI hay un botón "Speed up" / "Cancel" que hace lo mismo.

### ¿Qué pasa si... `block.timestamp` se manipula? — Time/oracle attacks

Los validadores tienen ~12 segundos de margen para ajustar `block.timestamp` (post-Merge el rango es estricto, pre-Merge era ±15s). Esto **no es aleatorio confiable** ni una fuente de entropía decente — para `SetBonusNFT.mintRandom` lo aceptamos solo porque las piezas son cosméticas (lo declaramos en `SECURITY.md`). Reglas de oro:

- **Nunca** uses `block.timestamp` para randomness con dinero real → usá [Chainlink VRF](https://docs.chain.link/vrf).
- **Nunca** uses `block.timestamp` para ventanas cortas (segundos / minutos) — un validador hostil te manipula el orden.
- **Sí podés** usarlo para ventanas largas (días/semanas) — un drift de 15s sobre 30 días es ruido.

Para los dividendos mensuales de DepFund, `require(block.timestamp >= lastDistribution + 30 days)` está bien.

### ¿Qué pasa si... pierdo el archivo del IPFS hash que apunta el NFT? — Pinning 📌

IPFS **no garantiza disponibilidad por sí solo**. Un CID (`ipfs://Qm...`) apunta a un blob, pero si ningún nodo lo "pinea" (lo guarda activamente), eventualmente es garbage-collected. Tu NFT sigue existiendo on-chain pero `tokenURI(id)` apunta a un 404 — OpenSea muestra "Image not available" y tu coleccionable queda en limbo.

Mitigación obligatoria para producción:

- **[Pinata](https://www.pinata.cloud)** — 1 GB gratis, muy usado por proyectos NFT.
- **[web3.storage](https://web3.storage)** — Filecoin-backed, gratis hasta cierto volumen.
- **[NFT.Storage](https://nft.storage)** — específicamente para metadata + assets de NFTs.
- **Tu propio nodo IPFS** corriendo en k3s con `ipfs daemon` y `ipfs pin add <CID>`.

Patrón seguro: subís a Pinata + tu propio nodo. Dos copias activas. Nunca confíes en un solo pinner.

### ¿Qué pasa si... el contrato es hackeado después del deploy?

La inmutabilidad corta para los dos lados: nadie puede censurarte, pero si tenés un bug, tampoco podés parchear. Mitigaciones que aplican capas:

- **Función `pause()`** con `onlyOwner` (heredá de OZ `Pausable`) — no detiene el bug pero detiene los pagos hasta que respondas.
- **Upgradability con proxies** (UUPS o Transparent de OZ) — el storage queda fijo, pero la lógica se reemplaza. Cuesta complejidad: el bug puede estar en el proxy mismo.
- **Multisig admin con [Gnosis Safe](https://safe.global)** — la owner key no es una sola persona, son N firmas de M. En DepFund el rector + tesorero + auditor firman juntos cualquier upgrade.
- **Bug bounty** público en [Immunefi](https://immunefi.com) — pagar $50K a quien encuentre un bug es mucho más barato que perder $5M.

Post-incident: forensic on-chain con [Tenderly](https://tenderly.co) para reconstruir cómo entró el atacante, contactar exchanges centralizados (Binance, Coinbase) para freezear si los fondos pasaron por ahí, comunicar a holders por canal oficial (Discord/Twitter) — silencio es lo peor.

### ¿Qué pasa si... un usuario pide refund?

La blockchain es irreversible. Una vez que `Paid(user, 100, action)` está minado, **no hay forma de "deshacer" la tx**. El refund se hace **off-chain por tu lógica**: el usuario abre un ticket en tu backend Web2, validás el caso, y desde tu wallet de owner mandás manualmente:

```solidity
function refund(address to, uint256 amount, bytes32 originalAction) external onlyOwner {
    usdc.safeTransfer(to, amount);
    emit Refunded(to, amount, originalAction);
}
```

Implicaciones que tenés que documentar antes de la demo:

- **Legales**: tu plataforma asume el riesgo del refund — el contrato no te obliga a nada, vos sí estás obligado por el TOS que firmaste con el usuario.
- **UX**: explicale al usuario que el refund "tarda hasta 24 hs" mientras vos lo procesás. No es instantáneo como una tarjeta de crédito.
- **Contabilidad**: el evento `Refunded` aparece on-chain — alguien puede verlo y construir métricas. Sé prolijo.

### ¿Qué pasa si... el contrato muere por un bug y los fondos quedan trabados?

Caso real: **Parity multisig 2017** — un usuario llamó accidentalmente la función `kill()` del contrato library compartido y dejó **$300M en ETH congelados para siempre** (~513.000 ETH). No había forma de recuperarlos sin un hard fork de Ethereum (que no se hizo). El contrato sigue ahí, mirando los fondos sin tocarlos, en 2026.

Patrón defensivo: siempre tené una **función de salida de emergencia** restringida y con timelock:

```solidity
function emergencyWithdraw(address token, uint256 amount) external onlyOwner {
    require(emergencyTimelock != 0 && block.timestamp >= emergencyTimelock, "wait");
    IERC20(token).transfer(owner(), amount);
    emit EmergencyWithdraw(token, amount);
}

function startEmergency() external onlyOwner {
    emergencyTimelock = block.timestamp + 7 days; // los users pueden salir antes
    emit EmergencyStarted(emergencyTimelock);
}
```

El timelock de 7 días le da a los usuarios la chance de retirar sus fondos antes de que el owner los toque — alinea incentivos. Para tu TP no es obligatorio, pero declaralo en `SECURITY.md` como decisión consciente.

---

## Bloque 4 · Caso real consolidado · Un día en producción de DepFund

Imaginate que el TP final ya está en producción. La cátedra cerró el cuatrimestre, el equipo de DepFund decidió no abandonar el proyecto y siguen iterando. Es martes 14:32 y un nuevo inversor abre `depfund.dev` en su celular.

**Paso 1.** El usuario llega a `depfund.dev`, una URL de Vercel que sirve el bundle estático de Next.js desde el edge global de Cloudflare. La página carga en 800 ms en Buenos Aires; los assets vienen del CDN de Vercel y el framework hidrata. Click en "Connect Wallet" → RainbowKit abre el modal → MetaMask Mobile detecta el `wc:` deeplink → el usuario aprueba la conexión a Sepolia.

**Paso 2.** Apenas conecta, el frontend dispara cuatro `useReadContract` en paralelo contra el RPC de Alchemy: `gateway.usdc()`, `gateway.treasury()`, `dpf.balanceOf(user)`, y un getter custom `activeRound()` que devuelve la ronda de financiación abierta. Las cuatro llamadas son `view` puras, no firman nada, no cuestan gas, vuelven en ~200 ms desde el nodo de Alchemy en us-east. La UI se hidrata mostrando "Ronda 3 abierta · $1.2M / $2M financiados · 47 días restantes".

**Paso 3.** El usuario teclea `100` en el campo USDC. El frontend hace el cálculo on-the-fly: con `pricePerShare = 0.5 USDC`, recibirá 200 $DPF. Como todavía no tiene allowance al gateway, el botón muestra "1) Approve 100 USDC". Internamente `useReadContract({ functionName: 'allowance' })` devuelve `0n`, así que el flow de dos pasos se activa.

**Paso 4.** Click en Approve → wagmi llama `usdc.approve(PaymentGateway, 100_000_000)` → MetaMask abre el popup de firma → el usuario revisa "Spending limit: 100 USDC" → confirma. La tx sale del mobile a través del provider Infura/Alchemy embebido y entra al mempool público de Sepolia. El frontend muestra "Esperando bloque..." con el spinner de `useWaitForTransactionReceipt`.

**Paso 5.** Doce segundos después, un validador de Sepolia mina el bloque número 4.832.157 que incluye el approve. El receipt vuelve por el RPC, `isSuccess` se vuelve `true`, la UI ahora muestra el botón verde "2) Pay 100 USDC". El allowance on-chain pasó de 0 a 100.000.000 (USDC tiene 6 decimales).

**Paso 6.** Click en Pay → wagmi llama `gateway.pay(100_000_000, keccak256("round-3"))` → segundo popup de MetaMask con gas estimado de 0.0002 ETH → confirma. La tx entra al mempool. Esta vez es más pesada que el approve porque ejecuta `transferFrom` + emit + `_onPaid` con mint de $DPF + mint de pieza Set Bonus.

**Paso 7.** Doce segundos más tarde, bloque 4.832.158 incluye la tx. Dentro del EVM, en orden: `usdc.safeTransferFrom(user, treasury, 100_000_000)` mueve los USDC del usuario al treasury (un Gnosis Safe 3-of-5 que controlan rector + tesorero + auditor + dos del equipo); `nonReentrant` libera el guard; `emit Paid(user, 100_000_000, "round-3")` escribe el log indexable; `_onPaid` se dispara como hook.

**Paso 8.** Adentro de `_onPaid`, el contrato calcula `shares = 100e6 * 1e18 / pricePerShare` y llama `dpf.mint(user, 200e18)` — el usuario ahora tiene 200 $DPF. Después computa `entropy = keccak256(user, amount, block.prevrandao, action)` y llama `pieces.mintRandom(user, entropy)` — sale una pieza Rare del slot 7 (el "vestuario norte" del complejo). El usuario está a una pieza de completar el "Ala deportiva" y ganarse un +1% de dividendos permanente. El contrato cierra emitiendo `PieceMinted(user, tokenId=4521, slot=7, rarity=Rare)`.

**Paso 9.** En paralelo, en el cluster k3s del equipo (3 nodos en Hetzner, $20/mes), un pod indexador escucha eventos. Está corriendo Node.js + viem con `client.watchEvent({ address: PAYGW, event: PaidAbi, onLogs })`. La línea `Paid(user, 100_000_000, "round-3")` llega al callback ~200 ms después del bloque. El indexer hace `INSERT INTO payments(payer, amount, action, tx_hash, block_number, ts) VALUES (...)` en Postgres. Otra rama del callback también captura `PieceMinted` y popula la tabla `nft_pieces`.

**Paso 10.** Una API REST en Node consume cambios de la tabla via Postgres `LISTEN/NOTIFY`. Detecta el INSERT y dispara un webhook al canal `#sales-realtime` de Slack del equipo: "Nuevo inversor en ronda-3: 100 USDC → 200 $DPF · pieza Rare slot 7". El community manager lo ve, postea un GIF, sigue con su día. La API también dispara un email transaccional via SES al usuario: "Bienvenido a DepFund · tus 200 $DPF están en tu wallet".

**Paso 11.** Mientras todo esto pasa, el indexer está logueando todo a stdout. Promtail (sidecar en k3s) levanta esos logs y los manda a Loki. Una dashboard de Grafana grafica TPS por minuto, distribución de monto por pago, y un panel especial que correlaciona `block.number` del evento con el `traceId` del request HTTP que lo originó (lo que aprendieron en TP2). Si más adelante alguien reporta "no me llegó la confirmación", el equipo busca en Loki por `payer:0x...` y reconstruye toda la cadena: tx → indexer → API → email.

**Paso 12.** Pasan 30 días. El parque deportivo del complejo factura $50.000 USDC en alquileres y eventos. El rector entra a `depfund.dev/admin`, conecta su wallet del Gnosis Safe, y firma la tx multisig `gateway.distributeDividends(50_000_000_000)`. Los otros dos firmantes confirman desde sus celulares. Cuando se junta el quorum 3-of-5, la tx se ejecuta: el contrato suma $50.000 al `accPerShare` global. El usuario del paso 1 ya no necesita firmar nada — cuando quiera, abre la app y clickea "Claim" → recibe `200 / totalSupply * 50_000 USDC` en su wallet, pull-payment style. El loop cerró.

> Cada pieza de este flujo es una capa concreta del stack del módulo: edge (Vercel + Cloudflare), web2 en k3s (indexer + Postgres + API + Loki + Grafana), on-chain en Sepolia (PaymentGateway + DPF + SetBonusNFT + Gnosis Safe). Lo que aprendieron en TP0, TP1 y TP2 sigue ahí; el módulo blockchain agregó la capa de pago y propiedad sin reemplazar nada de lo demás.

---

## Volver

> Volver al [material del Seminario](index.html)
