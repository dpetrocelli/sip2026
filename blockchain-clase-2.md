# Blockchain · Clase 2 — ERC-20 + PaymentGateway + Reentrancy

> **Objetivo de la clase**: dejar el `SimpleStorage` atrás y escribir el contrato que su sistema **realmente** va a usar — un `PaymentGateway` que cobra USDC en Sepolia, emite eventos `Paid` que su backend va a consumir, y está protegido contra el ataque clásico de **reentrancy**. Al final tienen el contrato deployado y testeado.

> **Pre-requisito**: la clase 1 cerrada. Tienen MetaMask + Sepolia + Foundry instalado, y un `SimpleStorage` deployado y verificado.

---

## ¿Qué vamos a hacer hoy?

1. **Refresher** del modelo mental: el contrato como "MercadoPago en blockchain" (5 min).
2. **¿Qué es ERC-20?** El estándar de tokens fungibles — la moneda del sistema.
3. **OpenZeppelin** — la librería de contratos battle-tested que vamos a usar.
4. **El contrato `PaymentGateway`** paso a paso.
5. **Tests con Foundry** — happy path + edge cases + protección contra reentrancy.
6. **El ataque de reentrancy** — cómo se rompía el contrato sin protección, y cómo se cierra.
7. **Deploy del PaymentGateway a Sepolia**.
8. **Probar el flow completo**: aprobar USDC → llamar `pay()` → ver el evento `Paid` en Etherscan.

Al cerrar: cada equipo tiene un PaymentGateway suyo deployado. **Ese es el contrato base** que en clase 4 van a extender con la lógica específica de su proyecto (VibeCheck/DepFund/RNW/IDEAFY).

---

## Parte 1 — Refresher rápido

Dijimos que vamos a integrar pagos en blockchain como integraríamos MercadoPago. Recordemos:

| MercadoPago | PaymentGateway en Sepolia |
|---|---|
| `MercadoPago.charge(buyer, amount)` (HTTP API) | `gateway.pay(amount, action)` (tx firmada) |
| Webhook que avisa "el pago se procesó" | Evento `Paid(payer, amount, action)` que su indexer consume |
| Saldo del comprador en pesos | Saldo del comprador en USDC (un ERC-20) |
| MercadoPago como custodio de los pesos | El contrato `treasury` recibe los USDC directamente |
| Comisión de MP (~5%) | Gas (~$0.5 en Sepolia, ~$0.01 en Polygon mainnet) |

> 🎯 **Clave**: si entendieron MercadoPago como integración HTTP-API, esto es **el mismo modelo mental** pero cambiando los rieles. Lo que cambia: cómo se firman las txs y cómo se mueven los activos.

---

## Parte 2 — ERC-20: el estándar de tokens

**ERC-20** es la "interface" de Solidity que todos los tokens fungibles cumplen (USDC, USDT, DAI, su propio token si crean uno). Estandarizar la interface significa que cualquier contrato puede recibir cualquier ERC-20 sin escribir código a medida.

### Las 6 funciones de ERC-20

| Función | Qué hace | Quién la llama |
|---|---|---|
| `totalSupply()` | Total de tokens emitidos | Cualquiera (read) |
| `balanceOf(address)` | Saldo de un usuario | Cualquiera (read) |
| `transfer(to, amount)` | Mover tokens del caller a `to` | El dueño de los tokens |
| `approve(spender, amount)` | "Autorizo a `spender` a gastar hasta `amount` tokens en mi nombre" | El dueño de los tokens |
| `allowance(owner, spender)` | Cuánto le queda autorizado a `spender` | Cualquiera (read) |
| `transferFrom(from, to, amount)` | Si `from` me autorizó, mover `amount` de `from` a `to` | Un contrato (típicamente) |

### El patrón "approve + transferFrom"

Es **el corazón** de cómo cobra un contrato:

1. **El usuario llama `usdc.approve(gateway, 50)`** → "le doy permiso al PaymentGateway de gastar hasta 50 USDC míos".
2. **El usuario llama `gateway.pay(50, ...)`** → el PaymentGateway internamente llama `usdc.transferFrom(user, treasury, 50)` y los USDC se mueven.

Son **dos transacciones**. ¿Por qué? Seguridad: el usuario decide explícitamente cuánto autoriza antes de que el contrato pueda mover sus fondos. Si el contrato es malicioso, sólo puede robar lo aprobado, no todo el saldo.

> **Comparación con MercadoPago**: en MP, le das tu tarjeta una vez y MP puede cobrar lo que quiera (subscripciones, etc.). Acá, cada cobro requiere un `approve` previo del usuario. Más fricción, más seguridad.

---

## Parte 3 — OpenZeppelin: no reinventes la rueda

**OpenZeppelin** es la librería estándar de contratos en Solidity. Su código está auditado, testeado y battle-tested en miles de protocolos. **Nunca escribimos un ERC-20 desde cero** — usamos el de OZ.

```bash
forge install OpenZeppelin/openzeppelin-contracts --no-commit
```

Esto agrega `lib/openzeppelin-contracts` con todos los standards listos: ERC-20, ERC-721, ERC-1155, AccessControl, Ownable, ReentrancyGuard, etc.

En `remappings.txt`:

```
@openzeppelin/contracts/=lib/openzeppelin-contracts/contracts/
```

---

## Parte 4 — El contrato `PaymentGateway`

Abrí `src/PaymentGateway.sol` (lo creamos ahora):

```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title PaymentGateway
 * @notice Recibe pagos en USDC y emite eventos para el backend.
 * @dev Cada proyecto extiende esto sobrescribiendo `_onPaid`.
 */
contract PaymentGateway is ReentrancyGuard {
    using SafeERC20 for IERC20;

    IERC20 public immutable usdc;
    address public immutable treasury;

    event Paid(address indexed payer, uint256 amount, bytes32 indexed action);

    error AmountZero();
    error TreasuryZero();

    constructor(IERC20 _usdc, address _treasury) {
        if (_treasury == address(0)) revert TreasuryZero();
        usdc = _usdc;
        treasury = _treasury;
    }

    /**
     * @notice Recibe un pago de `amount` USDC del caller. Requiere approve previo.
     * @param amount Cantidad en USDC (con sus 6 decimales: 50 USDC = 50_000_000).
     * @param action Identificador opaco de qué se está pagando ("ticket-123", "subscription", etc.).
     */
    function pay(uint256 amount, bytes32 action) external nonReentrant {
        if (amount == 0) revert AmountZero();

        // 1. Mover los USDC del usuario al treasury.
        usdc.safeTransferFrom(msg.sender, treasury, amount);

        // 2. Emitir evento (para que el backend lo consuma).
        emit Paid(msg.sender, amount, action);

        // 3. Hook para que las subclases ejecuten lógica extra (mint NFT, registrar shares, etc.).
        _onPaid(msg.sender, amount, action);
    }

    /// @dev Override en subclases. Por defecto no hace nada.
    function _onPaid(address payer, uint256 amount, bytes32 action) internal virtual {}
}
```

### Por qué cada decisión

| Línea | Por qué |
|---|---|
| `pragma solidity 0.8.24` | Versión moderna con checked arithmetic por default (no overflow silencioso) |
| `import IERC20` | Interface estándar para hablar con USDC |
| `SafeERC20` | Wrapper que revierte si el token no respeta el standard (algunos ERC-20 viejos como USDT no devuelven `bool` en transfer) |
| `ReentrancyGuard` | Mixin de OZ que evita el ataque de reentrancy (próximamente) |
| `immutable` | El valor se setea en el constructor y nunca cambia → más barato en gas (no usa storage) |
| `error AmountZero()` | Custom errors son **más baratos en gas** que `require(...)` con string |
| `nonReentrant` | El modifier de OZ — bloquea llamadas re-entrantes a `pay` |
| `_onPaid` virtual | Hook que las subclases sobrescriben — patrón template method |

---

## Parte 5 — Tests con Foundry

Abrí `test/PaymentGateway.t.sol`. Vamos a usar un **mock de USDC** (no podemos usar el USDC real de Sepolia en tests locales).

```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {Test, console} from "forge-std/Test.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {PaymentGateway} from "../src/PaymentGateway.sol";

/// @dev Token ERC-20 fake con 6 decimales (igual que USDC) para tests.
contract MockUSDC is ERC20 {
    constructor() ERC20("Mock USDC", "mUSDC") {
        _mint(msg.sender, 1_000_000 * 10 ** 6); // 1M USDC
    }

    function decimals() public pure override returns (uint8) {
        return 6;
    }
}

contract PaymentGatewayTest is Test {
    PaymentGateway internal gateway;
    MockUSDC internal usdc;

    address internal alice = makeAddr("alice");
    address internal treasury = makeAddr("treasury");

    function setUp() public {
        usdc = new MockUSDC();
        gateway = new PaymentGateway(usdc, treasury);

        // Damos 1000 USDC a alice para que pueda pagar.
        usdc.transfer(alice, 1000 * 10 ** 6);
    }

    function test_PayMovesUsdcToTreasury() public {
        uint256 amount = 50 * 10 ** 6;

        vm.startPrank(alice);
        usdc.approve(address(gateway), amount);
        gateway.pay(amount, bytes32("test-action"));
        vm.stopPrank();

        assertEq(usdc.balanceOf(treasury), amount);
        assertEq(usdc.balanceOf(alice), (1000 * 10 ** 6) - amount);
    }

    function test_PayEmitsEvent() public {
        uint256 amount = 100 * 10 ** 6;

        vm.startPrank(alice);
        usdc.approve(address(gateway), amount);

        vm.expectEmit(true, true, false, true);
        emit PaymentGateway.Paid(alice, amount, bytes32("ticket-1"));
        gateway.pay(amount, bytes32("ticket-1"));

        vm.stopPrank();
    }

    function test_PayRevertsOnZeroAmount() public {
        vm.startPrank(alice);
        usdc.approve(address(gateway), 0);

        vm.expectRevert(PaymentGateway.AmountZero.selector);
        gateway.pay(0, bytes32("nada"));
    }

    function test_PayRevertsWithoutApprove() public {
        uint256 amount = 50 * 10 ** 6;

        vm.startPrank(alice);
        // Sin approve previo → debería fallar
        vm.expectRevert();
        gateway.pay(amount, bytes32("test"));
    }

    function testFuzz_PayAnyValidAmount(uint96 amount) public {
        vm.assume(amount > 0 && amount <= 1000 * 10 ** 6);

        vm.startPrank(alice);
        usdc.approve(address(gateway), amount);
        gateway.pay(amount, bytes32("fuzz"));

        assertEq(usdc.balanceOf(treasury), amount);
    }
}
```

Corré:

```bash
forge test -vv
```

Esperás 5 tests en verde, incluyendo el fuzz test que prueba con cientos de inputs aleatorios.

---

## Parte 6 — Reentrancy: el ataque que rompió The DAO

**Reentrancy** es **EL** bug más famoso de Ethereum. En 2016 alguien drenó $60M de The DAO con esta técnica. Hoy es trivial defenderse, pero hay que entenderlo.

### El ataque, conceptualmente

Imaginá un contrato vulnerable así:

```solidity
// MAL — no hagas esto
contract VulnerableBank {
    mapping(address => uint256) public balance;

    function deposit() external payable {
        balance[msg.sender] += msg.value;
    }

    function withdraw() external {
        uint256 bal = balance[msg.sender];
        require(bal > 0);

        // 1. Mandamos el ETH al usuario
        (bool ok,) = msg.sender.call{value: bal}("");
        require(ok);

        // 2. Después actualizamos el saldo a 0
        balance[msg.sender] = 0;
    }
}
```

El bug: en el paso 1, **transferimos antes de actualizar el saldo**. Si `msg.sender` es un contrato malicioso, su `receive()` puede volver a llamar `withdraw()` antes de que el `balance[msg.sender] = 0` se ejecute. Resultado: drena el contrato 1 ETH a la vez.

### Cómo se ve un atacante

```solidity
contract Attacker {
    VulnerableBank public bank;

    constructor(VulnerableBank _bank) payable {
        bank = _bank;
        bank.deposit{value: 1 ether}();
    }

    function attack() external {
        bank.withdraw();
    }

    receive() external payable {
        if (address(bank).balance >= 1 ether) {
            bank.withdraw();   // ← re-entry: vuelvo a llamar withdraw
        }
    }
}
```

### Cómo se cierra

**3 maneras**, en orden de preferencia:

1. **Patrón Checks-Effects-Interactions**: actualizá el state ANTES de transferir. Pone el `balance[...] = 0` ANTES del `call{value: ...}`.
2. **`ReentrancyGuard` de OpenZeppelin** (lo que usamos en `PaymentGateway`): un mutex que impide entradas concurrentes.
3. **`safeTransferFrom` con tokens estándar**: ERC-20 transferFrom no permite re-entry naturalmente porque devuelve antes de llamar al callback (y los tokens decentes no tienen callbacks).

### En nuestro `PaymentGateway`

Aplicamos las 3 defensas de una:

- ✅ Usamos `nonReentrant` (mutex de OZ).
- ✅ Movemos los USDC **antes** de emitir evento o ejecutar `_onPaid`. Si `_onPaid` quiere hacer cosas peligrosas (como mintar NFTs y enviarlos a `payer`), el guard lo cubre.
- ✅ Usamos `safeTransferFrom` que revierte si el token devuelve `false` (algunos ERC-20 viejos lo hacen sin revertir).

> 💡 **Tarea para casa**: armar un test que intente hacer reentrancy contra `PaymentGateway` y comprobar que falla. Pista: hagan que `_onPaid` haga algo arbitrario en una subclass de prueba.

---

## Parte 7 — Deploy del PaymentGateway a Sepolia

### 7.1 Direcciones de USDC en Sepolia

USDC oficial de Circle en Sepolia:

```
0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238
```

Para conseguir USDC de testnet hay 2 opciones:

- **Faucet de Circle**: https://faucet.circle.com (login Google) → seleccionar Sepolia → te tira 10 USDC.
- **Mintear desde testnet bridges** (ej: Aave, Compound v3 deployments en Sepolia tienen sus propios faucets).

### 7.2 Variables de entorno

Tu `.env`:

```bash
SEPOLIA_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
ETHERSCAN_API_KEY=tu_api_key
USDC_SEPOLIA=0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238
TREASURY=0xtu_address_de_metamask
```

```bash
source .env
```

### 7.3 Script de deploy

Creá `script/DeployPaymentGateway.s.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {PaymentGateway} from "../src/PaymentGateway.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract DeployPaymentGateway is Script {
    function run() external returns (PaymentGateway gateway) {
        IERC20 usdc = IERC20(vm.envAddress("USDC_SEPOLIA"));
        address treasury = vm.envAddress("TREASURY");

        vm.startBroadcast();
        gateway = new PaymentGateway(usdc, treasury);
        vm.stopBroadcast();

        console.log("PaymentGateway deployed at:", address(gateway));
    }
}
```

Deployar:

```bash
forge script script/DeployPaymentGateway.s.sol \
  --rpc-url $SEPOLIA_RPC_URL \
  --account dev \
  --broadcast
```

Te devuelve la address del PaymentGateway. **Guardala**:

```bash
export GATEWAY=0xtu_payment_gateway
```

### 7.4 Verificar en Etherscan

```bash
forge verify-contract $GATEWAY \
  src/PaymentGateway.sol:PaymentGateway \
  --chain sepolia \
  --constructor-args $(cast abi-encode "constructor(address,address)" $USDC_SEPOLIA $TREASURY) \
  --etherscan-api-key $ETHERSCAN_API_KEY \
  --watch
```

Andá a `https://sepolia.etherscan.io/address/$GATEWAY#code` — vas a ver el source verificado y todas las funciones públicas.

---

## Parte 8 — Probar el flow completo

Ahora hacemos el flujo end-to-end desde la terminal.

### 8.1 Aprobar USDC al PaymentGateway

```bash
# 50 USDC con 6 decimales = 50_000_000
cast send $USDC_SEPOLIA "approve(address,uint256)" $GATEWAY 50000000 \
  --rpc-url $SEPOLIA_RPC_URL \
  --account dev
```

Pone allowance del PaymentGateway en 50 USDC contra tu wallet.

### 8.2 Verificar el allowance

```bash
cast call $USDC_SEPOLIA "allowance(address,address)(uint256)" \
  $(cast wallet address --account dev) $GATEWAY \
  --rpc-url $SEPOLIA_RPC_URL
# 50000000
```

### 8.3 Llamar `pay()`

```bash
cast send $GATEWAY "pay(uint256,bytes32)" 50000000 0x$(echo -n "primera-prueba" | xxd -p) \
  --rpc-url $SEPOLIA_RPC_URL \
  --account dev
```

Tarda ~15 segundos. El receipt incluye el evento `Paid(payer=tu_address, amount=50000000, action=primera-prueba)`.

### 8.4 Verificar en Etherscan

Abrí `https://sepolia.etherscan.io/address/$GATEWAY` → tab **"Events"**:

- Vas a ver `Paid(...)` con tu address y los parámetros.
- En la pestaña **"Read Contract"** podés ver `usdc()` y `treasury()` configurados correctamente.
- En **"Internal Txns"** vas a ver el `transferFrom` que el PaymentGateway hizo internamente.

### 8.5 Confirmar saldo del treasury

```bash
cast call $USDC_SEPOLIA "balanceOf(address)(uint256)" $TREASURY \
  --rpc-url $SEPOLIA_RPC_URL
# 50000000  (= 50 USDC)
```

✅ **Cobraste tu primer pago en blockchain.** Esa misma operación, hecha desde un frontend con MetaMask, es lo que vamos a armar en clase 3.

---

## Cierre — qué nos llevamos

Después de esta clase tienen:

- [ ] Entienden ERC-20 (especialmente `approve` + `transferFrom`)
- [ ] Tienen `PaymentGateway.sol` escrito, testeado y deployado en Sepolia
- [ ] El contrato está verificado en Etherscan (cualquiera puede leer el source)
- [ ] Probaron el flow completo desde `cast`: approve → pay → ver evento
- [ ] Saben qué es reentrancy y cómo lo cierra OZ con `nonReentrant`

**En clase 3** vamos a:
- Reemplazar `cast` por una dApp Next.js + wagmi + RainbowKit.
- Usuarios reales conectando MetaMask y pagando desde el browser.
- Onramp testnet propio (`TestnetOnramp.sol`) que mintea USDC fake cuando "pagás con tarjeta".
- Deploy de la dApp a Vercel.

---

## Tarea para clase 3

Antes del próximo sábado:

1. `PaymentGateway` deployado en Sepolia + verificado en Etherscan (entregable: la URL `sepolia.etherscan.io/address/...#code`).
2. Hicieron al menos **2 pagos** desde `cast` con `action` distintas (entregable: las 2 URLs de tx de Etherscan).
3. Tu address de `treasury` muestra el saldo USDC acumulado.
4. (Bonus) Escriban un test que intente reentrancy y pase.

---

## Si algo falla

| Síntoma | Causa probable | Fix |
|---|---|---|
| `Error: ERC20: insufficient allowance` | No aprobaste o aprobaste menos que el `pay` | Re-aprobá con la cantidad correcta (paso 8.1) |
| `Error: ERC20: transfer amount exceeds balance` | No tenés USDC en tu wallet | Pedí USDC al faucet de Circle |
| `Error: gateway.pay reverted` sin razón clara | El allowance está en 0 (o expiró) | Aprobá de nuevo |
| `forge install` falla | Sin red, o submodules confundidos | `forge install --no-git` o `git submodule update --init --recursive` |
| El test fuzz falla en algún input | Posible bug | Subir el rango con `vm.assume` o revisar lógica |
| `verify-contract` dice "Already Verified" | Está OK, ya lo tenías verificado | Ignorar — lo abrís y está bien |
| Etherscan no muestra el evento | A veces tarda 30-60s | Refrescar después de un minuto |
