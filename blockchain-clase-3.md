# Blockchain · Clase 3 — Frontend + integración + onramp testnet

> **Objetivo de la clase**: que al final de las 4 hs tengan **una dApp completa funcionando** — Next.js + wagmi + RainbowKit conectada al `PaymentGateway` que escribieron en clase 2, deployada en Sepolia. Al cierre van a poder hacer **pagos reales en USDC testnet desde el browser**, ver los eventos `Paid` en vivo, y tener un **onramp testnet propio** (`TestnetOnramp.sol`) que mintea USDC fake cuando el usuario "paga con tarjeta".

> **Pre-requisito**: clase 2 completa — su `PaymentGateway.sol` deployado en Sepolia, address conocida, tests pasando.

> **Repo**: hoy creamos un proyecto **separado** del Foundry de clase 1-2. Es un Next.js + wagmi independiente que se conecta al contrato deployado vía RPC. No hay carpeta `src/` compartida.

---

## ¿Qué vamos a hacer hoy?

1. **Refresh** de los **diagramas 2 y 3** del overview — las 3 capas del sistema + pasarela de pago.
2. **Setup** de un proyecto Next.js + wagmi + viem + RainbowKit.
3. **Conectar wallet** (MetaMask) con RainbowKit en una sola línea.
4. **Llamar `pay()`** del PaymentGateway desde el frontend — con el flow `approve` → `pay`.
5. **Mostrar tx hash y receipt** en la UI mientras se confirma.
6. **Escuchar eventos `Paid`** en tiempo real con `useWatchContractEvent`.
7. **Escribir un contrato `TestnetOnramp.sol`** que mintea USDC fake a cambio de ETH.
8. **Botón "comprar 50 USDC con tarjeta"** que simula el card flow y llama al onramp.
9. **Deploy a Vercel** — URL pública para mostrar en la demo del TP final.

Al cierre: cada equipo tiene una dApp en vivo que cualquiera puede usar desde el browser.

---

## Parte 1 — Refresh: dónde encaja el frontend

Antes de teclear, repasemos los **dos diagramas** del overview que matter para hoy.

### Diagrama 2 — Las 3 capas del sistema

Repasen el diagrama de [las 3 capas](blockchain-overview.html#2--las-3-capas-mapa-global-del-sistema) en el overview. **Lo nuevo de hoy**: el frontend habla con el contrato directamente vía RPC. El backend Web2 sigue ahí (auth opcional, indexer, BD para datos no críticos), pero **no es el broker** del pago. La firma sale de la wallet del usuario.

### Diagrama 3 — Pasarela de pago, dos caminos

| Camino | Flujo | Cuándo aplica |
|---|---|---|
| **A — Crypto-nativo** | usuario tiene USDC → `approve` → `pay` | Demo técnica, usuarios crypto |
| **B — Fiat onramp** | usuario llega con tarjeta → onramp convierte ARS → USDC en wallet → sigue camino A | Producción real, usuarios sin USDC |

> **Hoy**: armamos camino A (real, hablando con el `PaymentGateway`) y camino B **simulado** con un `TestnetOnramp` propio. En producción el camino B sería Lemon, MoonPay, Buenbit. En testnet **no existen onramps** — los simulamos con un contrato que mintea USDC fake.

---

## Parte 2 — Setup del proyecto Next.js

### 2.1 Crear el proyecto

```bash
npx create-next-app@latest paygw-dapp --typescript --tailwind --app --no-src-dir
cd paygw-dapp
```

Aceptá los defaults (eslint sí, alias `@/*` sí).

### 2.2 Instalar las deps de Web3

```bash
npm install wagmi viem @tanstack/react-query @rainbow-me/rainbowkit
```

| Lib | Para qué |
|---|---|
| `wagmi` | React hooks para Ethereum (`useAccount`, `useReadContract`, `useWriteContract`) |
| `viem` | Cliente de bajo nivel — encoding ABIs, parsing de tipos, formateo de unidades |
| `@tanstack/react-query` | Cache + refetch de las llamadas a la chain (lo usa wagmi por debajo) |
| `@rainbow-me/rainbowkit` | UI ya hecha de "Connect Wallet" + modal con todas las wallets |

### 2.3 WalletConnect Project ID

WalletConnect es el protocolo que conecta wallets móviles con la dApp. Necesitás un **Project ID** gratis.

1. Andá a https://cloud.reown.com (antes "WalletConnect Cloud").
2. Login con Google.
3. **Create Project** → nombre "PayGW SIP" → tipo "AppKit".
4. Copiá el **Project ID** (string tipo `a1b2c3...`).

Pegalo en `.env.local`:

```bash
NEXT_PUBLIC_WC_PROJECT_ID=tu_project_id_acá
NEXT_PUBLIC_PAYGW_ADDRESS=0xTuPaymentGatewayDeClase2
NEXT_PUBLIC_USDC_ADDRESS=0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238
```

> La address del USDC es la oficial de Circle en Sepolia. **No la cambien**: es la única que el faucet de Circle reconoce.

### 2.4 Configurar wagmi + RainbowKit

Creá `lib/wagmi.ts`:

```ts
import { getDefaultConfig } from '@rainbow-me/rainbowkit';
import { sepolia } from 'wagmi/chains';

export const config = getDefaultConfig({
  appName: 'PayGW SIP',
  projectId: process.env.NEXT_PUBLIC_WC_PROJECT_ID!,
  chains: [sepolia],
  ssr: true,
});
```

Creá `app/providers.tsx`:

```tsx
'use client';
import '@rainbow-me/rainbowkit/styles.css';
import { RainbowKitProvider } from '@rainbow-me/rainbowkit';
import { WagmiProvider } from 'wagmi';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { config } from '@/lib/wagmi';

const queryClient = new QueryClient();

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider>{children}</RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
}
```

Y envolvé `app/layout.tsx`:

```tsx
import { Providers } from './providers';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
```

---

## Parte 3 — Conectar wallet

Reemplazá el contenido de `app/page.tsx`:

```tsx
'use client';
import { ConnectButton } from '@rainbow-me/rainbowkit';
import { useAccount } from 'wagmi';

export default function Home() {
  const { address, isConnected } = useAccount();

  return (
    <main className="p-8 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">PayGW · Pasarela de pago</h1>
      <ConnectButton />
      {isConnected && (
        <p className="mt-4 text-sm text-gray-600">Conectado como {address}</p>
      )}
    </main>
  );
}
```

Corré:

```bash
npm run dev
```

Abrí http://localhost:3000 → click en "Connect Wallet" → MetaMask → aprobá.

**Importante**: la wallet tiene que estar en **Sepolia**. Si no, RainbowKit te muestra un botón rojo "Wrong network" que cambia con un click.

---

## Parte 4 — Llamar `pay()` desde el frontend

Acá está el corazón de la clase. Vamos por partes.

### 4.1 Definir los ABIs

Creá `lib/abis.ts`:

```ts
export const PAYGW_ABI = [
  {
    type: 'function',
    name: 'pay',
    stateMutability: 'nonpayable',
    inputs: [
      { name: 'amount', type: 'uint256' },
      { name: 'action', type: 'bytes32' },
    ],
    outputs: [],
  },
  {
    type: 'event',
    name: 'Paid',
    inputs: [
      { name: 'payer', type: 'address', indexed: true },
      { name: 'amount', type: 'uint256', indexed: false },
      { name: 'action', type: 'bytes32', indexed: true },
    ],
  },
] as const;

export const ERC20_ABI = [
  {
    type: 'function',
    name: 'approve',
    stateMutability: 'nonpayable',
    inputs: [
      { name: 'spender', type: 'address' },
      { name: 'amount', type: 'uint256' },
    ],
    outputs: [{ type: 'bool' }],
  },
  {
    type: 'function',
    name: 'allowance',
    stateMutability: 'view',
    inputs: [
      { name: 'owner', type: 'address' },
      { name: 'spender', type: 'address' },
    ],
    outputs: [{ type: 'uint256' }],
  },
  {
    type: 'function',
    name: 'balanceOf',
    stateMutability: 'view',
    inputs: [{ name: 'account', type: 'address' }],
    outputs: [{ type: 'uint256' }],
  },
] as const;
```

### 4.2 El flow conceptual — approve + pay

ERC-20 usa el patrón **approve + pull**. El `PaymentGateway` no puede tomar USDC directamente del usuario — primero el usuario tiene que **autorizar al contrato** a tomar X USDC. Después el contrato los "tira" hacia sí mismo con `transferFrom`.

```
Usuario          USDC (ERC-20)         PaymentGateway
   │                 │                       │
   │── approve(PGW, 10) ──▶                  │
   │                 │  (allowance = 10)     │
   │                 │                       │
   │── pay(10, "X") ─────────────────────▶   │
   │                 │ ◀── transferFrom(usr, treasury, 10) ─
   │                 │                       │── emit Paid
```

**Dos transacciones, dos firmas en MetaMask**. Lo veremos en pantalla.

### 4.3 Componente `PayForm.tsx`

Creá `app/components/PayForm.tsx`:

```tsx
'use client';
import { useState } from 'react';
import { useAccount, useReadContract, useWriteContract, useWaitForTransactionReceipt } from 'wagmi';
import { parseUnits, keccak256, toHex } from 'viem';
import { PAYGW_ABI, ERC20_ABI } from '@/lib/abis';

const PAYGW = process.env.NEXT_PUBLIC_PAYGW_ADDRESS as `0x${string}`;
const USDC = process.env.NEXT_PUBLIC_USDC_ADDRESS as `0x${string}`;

export function PayForm() {
  const { address } = useAccount();
  const [amount, setAmount] = useState('1');
  const [action, setAction] = useState('VIBE_TICKET');

  const amountWei = parseUnits(amount || '0', 6); // USDC tiene 6 decimales
  const actionBytes = keccak256(toHex(action));

  // Lectura: balance USDC + allowance actual
  const { data: balance } = useReadContract({
    address: USDC, abi: ERC20_ABI, functionName: 'balanceOf',
    args: address ? [address] : undefined,
  });
  const { data: allowance } = useReadContract({
    address: USDC, abi: ERC20_ABI, functionName: 'allowance',
    args: address ? [address, PAYGW] : undefined,
  });

  const needsApprove = (allowance ?? 0n) < amountWei;

  // Escritura: approve y pay (separadas)
  const { writeContract: writeApprove, data: approveHash, isPending: approvePending } = useWriteContract();
  const { writeContract: writePay, data: payHash, isPending: payPending } = useWriteContract();

  const { isLoading: approveConfirming, isSuccess: approveDone } = useWaitForTransactionReceipt({ hash: approveHash });
  const { isLoading: payConfirming, isSuccess: payDone } = useWaitForTransactionReceipt({ hash: payHash });

  function handleApprove() {
    writeApprove({
      address: USDC, abi: ERC20_ABI, functionName: 'approve',
      args: [PAYGW, amountWei],
    });
  }

  function handlePay() {
    writePay({
      address: PAYGW, abi: PAYGW_ABI, functionName: 'pay',
      args: [amountWei, actionBytes],
    });
  }

  return (
    <div className="border rounded-lg p-4 mt-6 space-y-3">
      <h2 className="text-xl font-semibold">Pagar con USDC</h2>
      <p className="text-sm">Balance: {balance ? Number(balance) / 1e6 : 0} USDC</p>

      <input
        className="border p-2 w-full" type="number" value={amount}
        onChange={(e) => setAmount(e.target.value)} placeholder="USDC a pagar"
      />
      <input
        className="border p-2 w-full" value={action}
        onChange={(e) => setAction(e.target.value)} placeholder="action (ej. VIBE_TICKET)"
      />

      {needsApprove ? (
        <button
          onClick={handleApprove} disabled={approvePending || approveConfirming}
          className="bg-blue-600 text-white px-4 py-2 rounded w-full"
        >
          {approvePending ? 'Confirmá en wallet…' : approveConfirming ? 'Esperando bloque…' : `1) Approve ${amount} USDC`}
        </button>
      ) : (
        <button
          onClick={handlePay} disabled={payPending || payConfirming}
          className="bg-green-600 text-white px-4 py-2 rounded w-full"
        >
          {payPending ? 'Confirmá en wallet…' : payConfirming ? 'Esperando bloque…' : `2) Pay ${amount} USDC`}
        </button>
      )}

      {approveHash && (
        <p className="text-xs">approve tx: <a className="underline" target="_blank" href={`https://sepolia.etherscan.io/tx/${approveHash}`}>{approveHash.slice(0, 10)}…</a></p>
      )}
      {payHash && (
        <p className="text-xs">pay tx: <a className="underline" target="_blank" href={`https://sepolia.etherscan.io/tx/${payHash}`}>{payHash.slice(0, 10)}…</a></p>
      )}
      {payDone && <p className="text-green-700">✅ Pago confirmado</p>}
    </div>
  );
}
```

Importalo en `app/page.tsx`:

```tsx
import { PayForm } from './components/PayForm';
// ...dentro del main:
{isConnected && <PayForm />}
```

### 4.4 Estados de la transacción — qué mostrar

| Estado wagmi | Significado | UI |
|---|---|---|
| `isPending` | Esperando que el usuario confirme en MetaMask | "Confirmá en wallet…" |
| `isLoading` (de `useWaitForTransactionReceipt`) | Ya firmó, esperando minería | "Esperando bloque…" |
| `isSuccess` | Confirmada en bloque | "✅ Listo" + link a Etherscan |
| `error` | Revert / sin gas / rechazada | Mensaje rojo |

> **Truco UX**: nunca dejes al usuario sin feedback. Cada click tiene que producir algo en pantalla en menos de 200ms (el spinner). Si el usuario no ve nada, vuelve a apretar el botón y manda 2 txs.

---

## Parte 5 — Escuchar eventos `Paid` en tiempo real

Cada `pay()` exitoso emite `Paid(payer, amount, action)`. Vamos a leerlos en vivo.

Creá `app/components/PaymentFeed.tsx`:

```tsx
'use client';
import { useState } from 'react';
import { useWatchContractEvent } from 'wagmi';
import { formatUnits } from 'viem';
import { PAYGW_ABI } from '@/lib/abis';

const PAYGW = process.env.NEXT_PUBLIC_PAYGW_ADDRESS as `0x${string}`;

type PaidLog = { payer: string; amount: bigint; action: string; tx: string };

export function PaymentFeed() {
  const [logs, setLogs] = useState<PaidLog[]>([]);

  useWatchContractEvent({
    address: PAYGW,
    abi: PAYGW_ABI,
    eventName: 'Paid',
    onLogs(events) {
      const next = events.map((e: any) => ({
        payer: e.args.payer,
        amount: e.args.amount,
        action: e.args.action,
        tx: e.transactionHash,
      }));
      setLogs((prev) => [...next, ...prev].slice(0, 20));
    },
  });

  return (
    <div className="border rounded-lg p-4 mt-6">
      <h2 className="text-xl font-semibold mb-2">Pagos recientes</h2>
      {logs.length === 0 && <p className="text-sm text-gray-500">Esperando eventos…</p>}
      <ul className="space-y-1">
        {logs.map((l) => (
          <li key={l.tx} className="text-xs font-mono">
            {l.payer.slice(0, 8)}… → {formatUnits(l.amount, 6)} USDC ({l.action.slice(0, 10)}…)
          </li>
        ))}
      </ul>
    </div>
  );
}
```

Pegalo abajo del `PayForm`. **Pedile a un compañero que pague desde su frontend** — vas a ver el evento aparecer en tu UI sin recargar.

> **Esto es Web3**: no hay un WebSocket de "tu backend te avisa". El RPC node hace polling de los logs por nosotros, wagmi lo abstrae. **Cualquier dApp del mundo** que escuche este evento lo recibe.

---

## Parte 6 — `TestnetOnramp.sol` — el onramp simulado

En testnet no hay forma de comprar USDC con tarjeta (Circle no convierte ARS → USDC test). Lo simulamos con un contrato propio: **mandás ETH testnet, te devuelve USDC fake**.

> **Importante**: este onramp **no usa el USDC oficial de Circle** (no podemos mintearlo nosotros). Usa un USDC mock que controla nuestro contrato. Para la dApp del TP final lo conveniente es que el `PaymentGateway` apunte al **mock USDC del onramp**, no al de Circle. Así el ciclo "comprar → pagar" cierra sin pedir al usuario que vaya a un faucet externo.

### 6.1 El contrato

En tu repo de Foundry de clase 2, creá `src/TestnetOnramp.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/// @notice USDC fake que vive en Sepolia. 6 decimales como el real.
contract MockUSDC is ERC20, Ownable {
    constructor() ERC20("Mock USDC", "mUSDC") Ownable(msg.sender) {}

    function decimals() public pure override returns (uint8) { return 6; }

    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
}

/// @notice Simula un onramp tipo MoonPay: recibe ETH, mintea USDC fake.
///         Tasa fija: 1 ETH testnet = 1000 mUSDC (irreal a propósito,
///         hace que con poca ETH del faucet se compre suficiente para demos).
contract TestnetOnramp is Ownable {
    MockUSDC public immutable usdc;
    uint256 public constant RATE = 1000; // 1 ETH = 1000 mUSDC

    event Onramped(address indexed buyer, uint256 ethIn, uint256 usdcOut);

    constructor(MockUSDC _usdc) Ownable(msg.sender) {
        usdc = _usdc;
    }

    /// @notice Llamada por el front cuando el usuario "paga con tarjeta".
    ///         En realidad recibe ETH testnet y mintea USDC al sender.
    function buyWithCard() external payable {
        require(msg.value > 0, "no eth");
        // msg.value en wei (18 dec). USDC tiene 6 dec.
        // out = (ethIn * RATE * 1e6) / 1e18 = ethIn * RATE / 1e12
        uint256 usdcOut = (msg.value * RATE) / 1e12;
        usdc.mint(msg.sender, usdcOut);
        emit Onramped(msg.sender, msg.value, usdcOut);
    }

    /// @notice El owner retira el ETH acumulado (en testnet no importa, pero queda como pattern).
    function withdraw() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }
}
```

### 6.2 Deploy

Creá `script/DeployOnramp.s.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {Script} from "forge-std/Script.sol";
import {MockUSDC, TestnetOnramp} from "../src/TestnetOnramp.sol";

contract DeployOnramp is Script {
    function run() external {
        vm.startBroadcast();
        MockUSDC usdc = new MockUSDC();
        TestnetOnramp onramp = new TestnetOnramp(usdc);
        usdc.transferOwnership(address(onramp)); // el onramp es quien mintea
        vm.stopBroadcast();
    }
}
```

Deployá:

```bash
forge script script/DeployOnramp.s.sol \
  --rpc-url $SEPOLIA_RPC_URL \
  --account dev \
  --broadcast \
  --verify --etherscan-api-key $ETHERSCAN_API_KEY
```

Anotá las dos addresses (`MockUSDC` y `TestnetOnramp`).

> **Re-deploy del PaymentGateway**: para cerrar el ciclo, redeployen el `PaymentGateway` apuntando a `MockUSDC` en vez del USDC de Circle. Actualicen `NEXT_PUBLIC_USDC_ADDRESS` y `NEXT_PUBLIC_PAYGW_ADDRESS` en `.env.local`.

---

## Parte 7 — UI del onramp

Creá `app/components/CardOnramp.tsx`:

```tsx
'use client';
import { useState } from 'react';
import { useWriteContract, useWaitForTransactionReceipt } from 'wagmi';
import { parseEther } from 'viem';

const ONRAMP = process.env.NEXT_PUBLIC_ONRAMP_ADDRESS as `0x${string}`;

const ONRAMP_ABI = [
  {
    type: 'function',
    name: 'buyWithCard',
    stateMutability: 'payable',
    inputs: [],
    outputs: [],
  },
] as const;

export function CardOnramp() {
  const [step, setStep] = useState<'idle' | 'card' | 'tx' | 'done'>('idle');
  const { writeContract, data: hash, isPending } = useWriteContract();
  const { isLoading, isSuccess } = useWaitForTransactionReceipt({ hash });

  async function buy50USDC() {
    setStep('card');
    // Simulación de "card flow" — en producción acá llamarías a Stripe/MercadoPago
    await new Promise((r) => setTimeout(r, 1500));
    setStep('tx');
    writeContract({
      address: ONRAMP,
      abi: ONRAMP_ABI,
      functionName: 'buyWithCard',
      value: parseEther('0.05'), // 0.05 ETH * 1000 = 50 mUSDC
    });
  }

  if (isSuccess && step !== 'done') setStep('done');

  return (
    <div className="border rounded-lg p-4 mt-6 bg-yellow-50">
      <h2 className="text-xl font-semibold">Sin USDC? Comprá con tarjeta</h2>
      <p className="text-sm text-gray-600 mb-2">
        (Simulado — en producción esto sería MoonPay/Lemon)
      </p>
      <button
        onClick={buy50USDC}
        disabled={step !== 'idle' && step !== 'done'}
        className="bg-purple-600 text-white px-4 py-2 rounded w-full"
      >
        {step === 'idle' && '💳 Comprar 50 mUSDC con tarjeta'}
        {step === 'card' && 'Procesando tarjeta…'}
        {step === 'tx' && (isPending ? 'Confirmá en wallet…' : 'Esperando bloque…')}
        {step === 'done' && '✅ 50 mUSDC en tu wallet'}
      </button>
      {hash && (
        <p className="text-xs mt-2">
          tx: <a className="underline" target="_blank" href={`https://sepolia.etherscan.io/tx/${hash}`}>{hash.slice(0, 10)}…</a>
        </p>
      )}
    </div>
  );
}
```

Agregá `NEXT_PUBLIC_ONRAMP_ADDRESS=0x...` a `.env.local` y montá el componente arriba del `PayForm`.

**El flow completo desde la dApp**:

1. Usuario conecta wallet (sin USDC, sin nada).
2. Click **"Comprar 50 mUSDC con tarjeta"** → 1.5s de spinner falso → tx al onramp → wallet recibe 50 mUSDC.
3. Click **"Approve 1 mUSDC"** → firma 1.
4. Click **"Pay 1 mUSDC"** → firma 2 → emite `Paid`.
5. Aparece en el feed de eventos.

Eso es **end-to-end onboarding sin USDC previo**. El TP final tiene que contar exactamente esta historia en su demo.

---

## Parte 8 — Deploy a Vercel

Vercel deploya Next.js gratis con `git push`. Es la URL pública que va a evaluar el docente.

### 8.1 Pushear a GitHub

```bash
git init && git add . && git commit -m "feat: paygw dapp"
gh repo create paygw-dapp --public --source=. --push
```

### 8.2 Importar en Vercel

1. https://vercel.com/new → "Import Git Repository" → seleccioná `paygw-dapp`.
2. **Environment Variables** — pegá las 4 vars:
   - `NEXT_PUBLIC_WC_PROJECT_ID`
   - `NEXT_PUBLIC_PAYGW_ADDRESS`
   - `NEXT_PUBLIC_USDC_ADDRESS`
   - `NEXT_PUBLIC_ONRAMP_ADDRESS`
3. Click **Deploy**. Tarda ~1 minuto.

Vercel te da una URL `https://paygw-dapp-xxx.vercel.app`. **Esa URL la abrís desde el celular con MetaMask Mobile** y funciona — eso es lo que demostrás en la presentación.

> **Tip**: cada `git push` redeploya. Empujen branches y los van a tener en URLs preview separadas.

---

## Cierre — qué nos llevamos

- [ ] dApp Next.js + wagmi + RainbowKit funcionando en local
- [ ] Botón Connect Wallet con MetaMask en Sepolia
- [ ] Form de pago con flow `approve` + `pay` y feedback de tx
- [ ] Feed en vivo de eventos `Paid`
- [ ] `TestnetOnramp.sol` + `MockUSDC` deployados y verificados
- [ ] Botón "comprar con tarjeta" simulado, integrado al onramp
- [ ] dApp deployada a Vercel con URL pública

**En clase 4** vamos a:
- Agregar **NFT de bonus** (ERC-721) que el `PaymentGateway` mintea a clientes recurrentes.
- Correr **Slither** para análisis estático de seguridad sobre los contratos.
- Cerrar el TP final mostrando cómo cada equipo (VibeCheck/DepFund/RNW/IDEAFY) plugga su lógica en `_onPaid`.

---

## Tarea para clase 4

Antes del próximo sábado, en su repo:

1. **dApp deployada en Vercel** (URL pública), con:
   - Connect wallet funcionando.
   - Form de pago con approve + pay completos.
   - Feed de eventos `Paid` en vivo.
2. **`TestnetOnramp` + `MockUSDC` deployados y verificados** en Sepolia (links a Etherscan).
3. **`PaymentGateway` redeployado** apuntando al `MockUSDC` (para que el ciclo cierre solo).
4. **Video de 90 segundos** mostrando: connect → comprar 50 mUSDC con tarjeta → approve → pay → ver evento. Súbanlo al campus.

Lo que **no** hace falta esta semana: estilos lindos, mobile responsive, multi-cuenta. Eso lo pulen en la semana de clase 4.

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
