# Blockchain · Tarea de clase 3 — dApp en Vercel + onramp testnet

> **Plazo**: antes de clase 4 (sábado 30/05).

> **Pre-requisito**: la [clase 3 completa](blockchain-clase-3.html) — proyecto Next.js + wagmi + RainbowKit, `TestnetOnramp.sol` y `MockUSDC.sol` listos.

---

## Qué hay que entregar

Antes del próximo sábado, en el campus, en su repo:

1. **dApp deployada en Vercel** (URL pública), con:
   - Connect wallet funcionando.
   - Form de pago con **`approve` + `pay` completos**.
   - Feed de eventos `Paid` en vivo (`useWatchContractEvent`).
2. **`TestnetOnramp` + `MockUSDC` deployados y verificados en Sepolia** (links a Etherscan de ambos).
3. **`PaymentGateway` redeployado** apuntando al `MockUSDC` (no al de Circle), para que el ciclo cierre solo dentro de la dApp.
4. **Video de 90 segundos** mostrando: connect → comprar 50 mUSDC con tarjeta → approve → pay → ver evento. Súbanlo al campus.

Lo que **no** hace falta esta semana: estilos lindos, mobile responsive, multi-cuenta. Eso lo pulen en la semana de clase 4.

---

## Cómo probar que está bien

Checklist de aceptación:

- [ ] `npm run dev` levanta sin errores en `http://localhost:3000`.
- [ ] El botón **Connect Wallet** abre el modal de RainbowKit y conecta MetaMask.
- [ ] Si la wallet no está en Sepolia, RainbowKit muestra el botón rojo "Wrong network" y el switch funciona.
- [ ] `.env.local` tiene las 4 variables con prefijo `NEXT_PUBLIC_`: `WC_PROJECT_ID`, `PAYGW_ADDRESS`, `USDC_ADDRESS`, `ONRAMP_ADDRESS`.
- [ ] El componente `PayForm` muestra balance USDC del usuario.
- [ ] El flujo de pago alterna correctamente entre **"1) Approve"** y **"2) Pay"** según el `allowance`.
- [ ] Cada tx muestra link a Etherscan (`https://sepolia.etherscan.io/tx/...`).
- [ ] `PaymentFeed` actualiza en vivo cuando otro alumno paga desde su frontend (sin recargar).
- [ ] El botón **"Comprar 50 mUSDC con tarjeta"** del `CardOnramp`:
  - Muestra un spinner falso 1.5s (simulación de card flow).
  - Llama `buyWithCard()` con `value: parseEther('0.05')`.
  - Termina en "✅ 50 mUSDC en tu wallet".
- [ ] `MockUSDC` y `TestnetOnramp` están **verificados** en Etherscan.
- [ ] El `MockUSDC.owner()` es la address del `TestnetOnramp` (transfer de ownership hecho).
- [ ] `PaymentGateway.usdc()` devuelve la address del `MockUSDC` (no la del USDC de Circle).
- [ ] La dApp en Vercel responde en su URL pública y todas las env vars están seteadas en Vercel.
- [ ] El video de 90s está subido al campus.

---

## Si algo falla

| Síntoma | Probable causa | Fix |
|---|---|---|
| `WalletConnect Project ID is not valid` | Variable mal pegada en `.env.local` | Verificá con `echo $NEXT_PUBLIC_WC_PROJECT_ID`, reiniciá `npm run dev` |
| RainbowKit no abre el modal | Falta `import '@rainbow-me/rainbowkit/styles.css'` | Agregalo en `providers.tsx` |
| MetaMask dice "Wrong network" | Wallet en mainnet o Goerli | Click en el botón rojo de RainbowKit → "Switch network" |
| `pay` revierte con `transfer failed` | No hiciste `approve` antes, o approve por menos | El UI tiene que mostrar "Approve" antes que "Pay" |
| `pay` revierte con `amount=0` | `parseUnits` recibió string vacío | Validá `amount > 0` antes del click |
| El feed de eventos no muestra nada | RPC público con rate limit | Cambiá a un RPC de Alchemy (free tier alcanza) |
| Vercel build falla con "process is not defined" | Variable sin prefijo `NEXT_PUBLIC_` | Todas las vars que usa el browser **tienen** que arrancar con `NEXT_PUBLIC_` |
| `parseUnits` da número raro | USDC tiene 6 decimales, no 18 | Usá `parseUnits(x, 6)`, no `parseEther(x)` |
| `useWatchContractEvent` no dispara | Address de contrato mal | Verificá `NEXT_PUBLIC_PAYGW_ADDRESS` y reiniciá |
| Onramp revierte con `OwnableUnauthorizedAccount` | Olvidaste `transferOwnership` del MockUSDC al onramp | Re-deploy con el script que sí lo hace |

---

## Volver

- [← Material de la clase 3](blockchain-clase-3.html)
- [← Volver al índice](index.html)
- [→ Clase 4 — NFTs + Slither](blockchain-clase-4.html)
