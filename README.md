# Ritual Sovereign Agent

Sovereign AI agent deployed on **Ritual testnet** (Chain ID: 1979) using the official [Forge](https://book.getfoundry.sh/) deployment method.

## Deployed Contract

| Field | Value |
|---|---|
| Contract | `SovereignAgentConsumer` |
| Address | `0x24e638d25930290e20D6566f8f50Bf9853B87A14` |
| Network | Ritual Testnet (1979) |
| Deployer | `0x1Bd65a5500e05E963236bcf0344ff6a9037e2Dc2` |
| Deploy Tx | `0xc31ef9e9dfef6a9b3ab4e7cb1ab9d005616d4203dff7c2e5af3a90dff8020732` |

## What It Does

The contract calls the Ritual Sovereign Agent precompile (`0x080C`) to run a CLI harness (ZeroClaw) inside a TEE enclave. Results are delivered asynchronously via the `onSovereignAgentResult` callback from the official AsyncDelivery contract.

```
EOA → callSovereignAgent(input) → precompile 0x080C → TEE executes CLI → Phase 2 callback → onSovereignAgentResult()
```

## System Contracts Used

| Contract | Address |
|---|---|
| Sovereign Agent Precompile | `0x080C` |
| AsyncDelivery | `0x5A16214fF555848411544b005f7Ac063742f39F6` |
| RitualWallet | `0x532F0dF0896F353d8C3DD8cc134e8129DA2a3948` |
| TEEServiceRegistry | `0x9644e8562cE0Fe12b4deeC4163c064A8862Bf47F` |

## Project Structure

```
src/
  SovereignAgentConsumer.sol   # Official contract from ritual-foundation/ritual-dapp-skills
build_request.py               # Builds the 23-field ABI-encoded sovereign agent request
poll_result.py                 # Polls for Phase 2 callback results
foundry.toml                   # Foundry configuration
```

## How to Run

### Prerequisites

```bash
# Install Foundry
curl -fsSL https://foundry.paradigm.xyz | bash
foundryup

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Deploy

```bash
forge create src/SovereignAgentConsumer.sol:SovereignAgentConsumer \
  --rpc-url https://rpc.ritualfoundation.org \
  --private-key <YOUR_PRIVATE_KEY> \
  --broadcast
```

### Fund RitualWallet

```bash
cast send 0x532F0dF0896F353d8C3DD8cc134e8129DA2a3948 \
  "deposit(uint256)" 100000000 \
  --value 1000000000000000000 \
  --private-key <YOUR_PRIVATE_KEY> \
  --rpc-url https://rpc.ritualfoundation.org
```

### Call the Agent

```bash
# Build request
uv run --with eciespy --with eth-abi --with web3 python3 build_request.py

# Submit (replace REQUEST_INPUT with output from above)
cast send <CONSUMER_ADDRESS> \
  "callSovereignAgent(bytes)" <REQUEST_INPUT> \
  --private-key <YOUR_PRIVATE_KEY> \
  --rpc-url https://rpc.ritualfoundation.org \
  --gas-limit 900000
```

## Configuration

The agent uses Ritual's own LLM gateway (no external API key required):

- **CLI Type**: 6 (ZeroClaw)
- **Model**: `zai-org/GLM-4.7-FP8`
- **Prompt**: `Say hello world`

## Verified Transaction

| Step | Tx Hash |
|---|---|
| Contract deployment | `0xc31ef9e9dfef6a9b3ab4e7cb1ab9d005616d4203dff7c2e5af3a90dff8020732` |
| RitualWallet deposit | `0x7abbcf2c130ccacd6ae3b72c7ac09b684ae1905be7eb54ac695a46d136ec3bbc` |
| Sovereign agent call | `0x3b7159bc40e30647f972907d5a73790d66ef17d011af01142c36682d6c30f1fe` |

Phase 2 callback delivered successfully in 1.4s — the end-to-end sovereign agent loop is verified working.

## License

MIT — Contract source from [ritual-foundation/ritual-dapp-skills](https://github.com/ritual-foundation/ritual-dapp-skills).

## Links

- [Ritual Network](https://ritual.net)
- [Developer Docs](https://docs.ritualfoundation.org)
- [Block Explorer](https://explorer.ritualfoundation.org)
- [Agent Explorer](https://agents.ritualfoundation.org)
- [Testnet Faucet](https://faucet.ritualfoundation.org)

## Disclaimer

Testnet only. Use a burner wallet. The contract interacts with unaudited system contracts. No warranty provided.
