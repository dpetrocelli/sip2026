# Blockchain · Clase 1 — Fundamentos + setup + tu primer contrato

> **Objetivo de la clase**: que al final de las 4 hs tengan **un contrato propio deployado en Sepolia** (testnet pública de Ethereum), interactúen con él desde la terminal y lo vean en Etherscan. Es la base sobre la que en clase 2 vamos a montar la pasarela de pago.

> **Pre-requisito**: las TPs anteriores (k3s, Selenium, observabilidad) ya las tienen. **No asumimos nada de Solidity ni blockchain previo**.

> 🎯 **Lo que te vas a llevar al final de hoy**:
> - [ ] MetaMask con wallet de dev + Sepolia activa + ETH de faucet
> - [ ] Foundry instalado (`forge`, `cast`, `anvil`) y verificado
> - [ ] Un contrato `SimpleStorage` deployado en Sepolia con address propia
> - [ ] Sabés interactuar con él desde `cast` (lectura + escritura)
> - [ ] El código fuente verificado y público en Etherscan

---

## ¿Qué vamos a hacer hoy?

1. **Web2 vs Web3** en 10 minutos (qué cambia, qué no — la analogía con MercadoPago).
2. **Setup MetaMask** + red **Sepolia** + ETH de faucet.
3. **Instalar Foundry** (`forge`, `cast`, `anvil`).
4. **Clonar el repo de la clase** con un contrato `SimpleStorage` listo.
5. **Caminar el contrato** línea por línea para entender Solidity básico.
6. **Correr los tests** con `forge test`.
7. **Deployar a Sepolia** y firmar la transacción con MetaMask.
8. **Interactuar con el contrato** desde la terminal (`cast call`, `cast send`).
9. **Verificar en Etherscan** para que cualquiera pueda ver el código fuente.

Al cierre: cada uno tiene un contrato suyo, vivo, en una blockchain pública.

---

## Parte 1 — ¿Qué cambia entre Web2 y Web3?

Ya saben armar sistemas con backend Node/Python + DB + frontend. Web3 **no reemplaza** eso — augmenta. La única pieza que cambia para nuestro caso (pasarela de pago) es:

| En Web2 (lo que ya saben) | En Web3 (lo que vamos a hacer) |
|---|---|
| Frontend + API + DB | **Igual** |
| Auth con JWT/sesiones | **Firma criptográfica** de la wallet |
| Procesar pago con MercadoPago | **Smart contract** que recibe USDC en Sepolia |
| Logs en Loki | Logs en Loki **+ eventos on-chain** que cualquiera puede leer |
| Despliegue en k8s | **Igual** (frontend), el contrato vive en Ethereum |

**Analogía**: piensen su sistema como una app que hoy usaría MercadoPago. Lo que vamos a hacer es **reemplazar el "MercadoPago.charge(amount)"** por un `usdc.transferFrom(buyer, treasury, amount)` que ejecuta un contrato suyo en Sepolia. El resto del sistema queda igual.

### Conceptos que aparecen y vamos a explicar a medida que los necesiten

- **Wallet** (billetera): guarda la **private key** del usuario. MetaMask es la más popular.
- **Address** (dirección): identificador público de cada usuario o contrato. Empieza con `0x...`.
- **Transaction** (tx): operación firmada con la PK que cambia el estado de la chain.
- **Smart contract**: programa que vive en la blockchain. Una vez deployado, su código no cambia.
- **Gas**: costo en ETH de cada transacción (en testnet es gratis pero usa "ETH falso").
- **Sepolia**: la **testnet** de Ethereum donde vamos a trabajar todo el módulo. Misma tecnología que mainnet, pero con ETH de juguete.
- **USDC**: stablecoin (1 USDC ≈ 1 USD). Lo vamos a usar en clase 2 como el "peso" de la pasarela.

> Si quieren profundizar antes de la clase 2: lean los **diagramas 1, 2 y 3** del [overview](blockchain-overview.html). Son 5 minutos.

---

## Parte 2 — Setup MetaMask + Sepolia

### 2.1 Instalar MetaMask

1. Bajar la extensión desde https://metamask.io/download/ — soporta Chrome, Brave, Firefox, Edge.
2. Crear una **wallet nueva** (botón "Create a new wallet").
3. Te muestra una **frase de recuperación de 12 palabras**: anotala en papel, guardala. **No le saques foto, no la mandes por chat, no la subas a git.** Quien tenga esa frase tiene tu wallet (y todos tus fondos si llega a haberlos).
4. Elegí una contraseña local (es solo para desbloquear la extensión en tu compu).

### 2.2 Activar la red Sepolia

MetaMask viene con mainnet por defecto. Tenemos que activar Sepolia.

1. Abrí MetaMask → click en el selector de redes (arriba a la izquierda, dice "Ethereum Mainnet").
2. Click en **"Show test networks"** → activá el toggle.
3. Seleccioná **Sepolia**. La barra superior debería decir "Sepolia" en violeta.

> **¿Por qué Sepolia y no mainnet?** Mainnet es la red real, las txs cuestan ETH real (~$2-5 USD por tx). Sepolia es testnet — mismas reglas, tecnología y herramientas, pero el ETH es gratis (lo pedís a un faucet). Para todo el módulo y el TP final usamos Sepolia.

### 2.3 Pedir ETH a un faucet

Necesitamos un poco de ETH de Sepolia para pagar gas. Lo pedimos gratis a un faucet:

1. Andá a https://www.alchemy.com/faucets/ethereum-sepolia (o https://sepoliafaucet.com).
2. Copiá tu address de MetaMask (click en el nombre de la cuenta arriba → copia automáticamente).
3. Pegala en el faucet. Confirmá. Tarda 10-30 segundos.
4. Refrescá MetaMask. Tenés que ver `~0.5 SepoliaETH`.

> Si el faucet pide login con email/Google, hacelo. Es para evitar bots.

### 2.4 Verificar tu address en Etherscan

Etherscan es el explorador público de Ethereum (también funciona para Sepolia).

```
https://sepolia.etherscan.io/address/<TU_ADDRESS>
```

Reemplazá `<TU_ADDRESS>` por la tuya (algo tipo `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1`).

Vas a ver:
- Tu balance: `0.5 ETH` (más o menos lo que te dio el faucet).
- "Transactions": una sola tx, que es la del faucet mandándote ETH.

🎯 **A partir de acá tenés una wallet funcional en una blockchain pública.** Cualquiera con tu address puede ver tu balance y txs.

---

## Parte 3 — Instalar Foundry

**Foundry** es el toolkit estándar para desarrollar smart contracts. Lo usan Uniswap, OpenSea, Paradigm. Trae 3 herramientas:

| Herramienta | Para qué |
|---|---|
| `forge` | Compilar contratos, correr tests, deployar |
| `cast` | Hablar con la blockchain desde la terminal (leer estado, mandar txs) |
| `anvil` | Blockchain local para desarrollo (no la vamos a usar mucho — preferimos Sepolia) |

### 3.1 Instalación

```bash
curl -L https://foundry.paradigm.xyz | bash
source ~/.bashrc      # o ~/.zshrc si usás zsh
foundryup
```

`foundryup` baja los binarios. Tarda menos de un minuto.

### 3.2 Verificar

```bash
forge --version
# debe responder: forge Version: 1.x.x ...
```

> ⚠️ **Si estás en Windows sin WSL**, esto va a fallar. Instalá WSL2 (Ubuntu) y corré todo desde ahí.

### 3.3 Extensión Solidity para VS Code

```bash
code --install-extension juanblanco.solidity
```

Te da highlighting, autocompletado y errores inline.

---

## Parte 4 — Clonar el repo de la clase

Armé un repo con todo listo. Lo clonan, compilan, testean.

```bash
git clone https://github.com/dpetrocelli/sip2026-blockchain-clase1.git
cd sip2026-blockchain-clase1
forge install                # baja deps (forge-std)
forge build                  # compila
```

Esperás ver `Solc 0.8.24 finished... Compiler run successful!`.

> Si el repo todavía no está publicado, los archivos están en el campus virtual; descomprímilos y posicionate en la carpeta antes del `forge build`.

---

## Parte 5 — Tour del contrato `SimpleStorage`

Abrí `src/SimpleStorage.sol` en VS Code:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

contract SimpleStorage {
    uint256 private _value;

    event ValueChanged(address indexed by, uint256 newValue);

    function set(uint256 value) external {
        _value = value;
        emit ValueChanged(msg.sender, value);
    }

    function get() external view returns (uint256) {
        return _value;
    }
}
```

**Línea por línea**:

| Línea | Qué dice | Por qué importa |
|---|---|---|
| `// SPDX-License-Identifier: MIT` | Licencia del contrato | Solidity exige declararla. MIT está bien para clase. |
| `pragma solidity 0.8.24;` | Versión del compilador | Pinear la versión evita sorpresas. |
| `contract SimpleStorage { }` | Define el contrato | Como `class` en Java/Python. |
| `uint256 private _value;` | Variable de estado | Vive en el **storage** del contrato (on-chain, persistente). |
| `event ValueChanged(...)` | Declara un evento | Los eventos son los "logs" del contrato. Su backend los puede consumir desde Loki/OpenTelemetry vía un indexer. |
| `function set(uint256 value) external` | Función pública que **modifica estado** | `external` = invocable desde afuera del contrato. Usa gas. |
| `emit ValueChanged(msg.sender, value);` | Dispara el evento | `msg.sender` = quien firmó la tx. |
| `function get() external view returns (uint256)` | Función pública que **solo lee** | `view` = no modifica state, no cuesta gas (si la llamás desde afuera). |

> ⚡ **Este contrato es trivial pero introduce todo**: storage, eventos, funciones que escriben (`set`) vs leen (`get`), `msg.sender`. Todo lo que vamos a usar en clase 2 con el `PaymentGateway` está acá.

---

## Parte 6 — Tests con Foundry

Foundry corre los tests **localmente** (sin tocar Sepolia). Abrí `test/SimpleStorage.t.sol`:

```solidity
import {Test} from "forge-std/Test.sol";
import {SimpleStorage} from "../src/SimpleStorage.sol";

contract SimpleStorageTest is Test {
    SimpleStorage internal storage_;

    function setUp() public {
        storage_ = new SimpleStorage();
    }

    function test_DefaultValueIsZero() public view {
        assertEq(storage_.get(), 0);
    }

    function test_SetUpdatesValue() public {
        storage_.set(42);
        assertEq(storage_.get(), 42);
    }

    function test_EmitsEventOnSet() public {
        vm.expectEmit(true, false, false, true);
        emit SimpleStorage.ValueChanged(address(this), 99);
        storage_.set(99);
    }
}
```

Corré:

```bash
forge test -vv
```

`-vv` te muestra el detalle de cada test. Tienen que pasar los 3.

> Esto se va a ver muy familiar: `setUp` = beforeEach, los `test_*` son tests individuales, `assertEq` = assertion. Foundry incluye **fuzzing** (inputs aleatorios) — más adelante.

---

## Parte 7 — Deploy a Sepolia

Hasta acá todo en local. Ahora vamos a **publicar el contrato** en Sepolia.

### 7.1 Importar tu wallet a Foundry

Foundry no lee MetaMask directamente. Le tenemos que dar la **private key** de la cuenta de MetaMask (en formato encriptado en disco). **Hacelo solo con una cuenta de testnet** que no tenga fondos reales.

```bash
cast wallet import dev --interactive
```

- Te pide la private key. La sacás de MetaMask: `⋮ → Account details → Show private key → poné tu pwd → copiar`.
- Pegala (no se ve en pantalla).
- Te pide una pwd local para encriptarla en disco. Elegí una que recuerdes — la vas a poner cada vez que firmes.

⚠️ **Nunca pegues una private key en git, en chats, en logs.** El cast wallet la guarda encriptada en `~/.foundry/keystores/dev`, eso sí podés versionarlo NO (está fuera del repo).

### 7.2 Configurar variables de entorno

Creá `.env` en el repo:

```bash
SEPOLIA_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
ETHERSCAN_API_KEY=tu_api_key_acá
```

- Ese RPC URL es público y gratis. Si querés más performance: registrate en https://www.alchemy.com (free tier alcanza).
- La API key de Etherscan la sacás en https://etherscan.io/myapikey (registrate, click "+ Add", copialá).

```bash
source .env
```

### 7.3 Deployar

```bash
forge create src/SimpleStorage.sol:SimpleStorage \
  --rpc-url $SEPOLIA_RPC_URL \
  --account dev \
  --broadcast
```

- `--account dev` usa la wallet que importaste antes (te pide la pwd local).
- `--broadcast` envía la tx (sin esto, hace dry-run).

Tarda ~15 segundos (un bloque de Sepolia). Te devuelve algo como:

```
Deployer: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1
Deployed to: 0x5FbDB2315678afecb367f032d93F642f64180aa3
Transaction hash: 0xabc...
```

**Guardá la `Deployed to` address** — es tu contrato.

```bash
export ADDR=0x5FbDB2315678afecb367f032d93F642f64180aa3   # la que te devolvió a vos
```

---

## Parte 8 — Interactuar con `cast`

Ahora hablás con tu contrato desde la terminal.

### 8.1 Leer estado (`cast call` — gratis, instantáneo)

```bash
cast call $ADDR "get()(uint256)" --rpc-url $SEPOLIA_RPC_URL
# 0
```

`0` porque el contrato está recién deployado y nunca llamamos `set`.

### 8.2 Modificar estado (`cast send` — firma + gas)

```bash
cast send $ADDR "set(uint256)" 42 \
  --rpc-url $SEPOLIA_RPC_URL \
  --account dev
```

Tarda 15 segundos. Te devuelve un receipt con `status: 1 (success)`.

### 8.3 Releer

```bash
cast call $ADDR "get()(uint256)" --rpc-url $SEPOLIA_RPC_URL
# 42
```

✅ **Acabás de modificar el estado de una blockchain pública desde la terminal.**

### 8.4 Inspeccionar la tx + el evento

```bash
cast receipt <TX_HASH> --rpc-url $SEPOLIA_RPC_URL
```

Vas a ver `gasUsed`, `status: 1`, y un `logs[0]` con tu evento `ValueChanged(address,uint256)`. **Eso es lo que su backend va a indexar** en clase 3.

---

## Parte 9 — Verificar en Etherscan

Que el bytecode de tu contrato esté en Sepolia no significa que el código fuente sea visible. Para que **cualquiera pueda leer y verificar** lo que hace el contrato, hay que verificarlo en Etherscan.

```bash
forge verify-contract $ADDR \
  src/SimpleStorage.sol:SimpleStorage \
  --chain sepolia \
  --etherscan-api-key $ETHERSCAN_API_KEY \
  --watch
```

`--watch` espera hasta que Etherscan termine de procesar (~30 segundos).

Cuando termina, andá a:

```
https://sepolia.etherscan.io/address/$ADDR#code
```

Vas a ver:
- 📄 **El código fuente Solidity** (sí, el `.sol` que escribiste).
- 🔓 **Read Contract**: tab para llamar `get()` desde el browser, sin tocar nada.
- ✍️ **Write Contract**: tab para llamar `set(uint256)` con MetaMask conectado.

Click en "Connect to Web3" → MetaMask conecta → escribís un valor en `set` → click "Write" → MetaMask abre popup → confirmás → tx → bloque → estado actualizado.

> Eso es **exactamente lo que cualquier usuario va a hacer** con sus contratos cuando los demos del TP final estén corriendo. Sin instalar nada, conectan MetaMask y pagan.

---

## Cierre — qué nos llevamos

Después de esta clase tienen:

- [ ] MetaMask con wallet propia + Sepolia activa + ETH de faucet
- [ ] Foundry instalado (`forge`, `cast`, `anvil`)
- [ ] Un contrato `SimpleStorage` deployado en Sepolia, con address propia
- [ ] Saben modificarlo y leerlo desde `cast`
- [ ] El código fuente verificado y público en Etherscan

**En clase 2** vamos a:
- Reemplazar `SimpleStorage` por un `PaymentGateway` que cobra USDC.
- Aprender ERC-20 (el estándar de tokens fungibles).
- Escribir el ataque clásico de **reentrancy** y cómo defenderse.

---

## Tarea para próxima clase

La tarea va en una página aparte: [Tarea de clase 1](blockchain-clase-1-tarea.html).
