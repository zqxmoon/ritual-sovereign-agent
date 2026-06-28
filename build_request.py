#!/usr/bin/env python3
"""调用官方 SovereignAgentConsumer 合约，使用 Ritual LLM 网关（无需外部 API key）。"""
import os
import sys
import time

from ecies import encrypt as ecies_encrypt
from ecies.config import ECIES_CONFIG
from eth_abi.abi import encode
from web3 import Web3

ECIES_CONFIG.symmetric_nonce_length = 12

RPC_URL = "https://rpc.ritualfoundation.org"
REGISTRY = "0x9644e8562cE0Fe12b4deeC4163c064A8862Bf47F"
CONSUMER = "0x24e638d25930290e20D6566f8f50Bf9853B87A14"  # 官方部署的合约

TEE_REGISTRY_ABI = [{
    "name": "getServicesByCapability", "type": "function", "stateMutability": "view",
    "inputs": [{"name": "c", "type": "uint8"}, {"name": "v", "type": "bool"}],
    "outputs": [{"name": "", "type": "tuple[]", "components": [
        {"name": "node", "type": "tuple", "components": [
            {"name": "paymentAddress", "type": "address"}, {"name": "teeAddress", "type": "address"},
            {"name": "teeType", "type": "uint8"}, {"name": "publicKey", "type": "bytes"},
            {"name": "endpoint", "type": "string"}, {"name": "certPubKeyHash", "type": "bytes32"},
            {"name": "capability", "type": "uint8"}]},
        {"name": "isValid", "type": "bool"}, {"name": "workloadId", "type": "bytes32"}]}]
}]

w3 = Web3(Web3.HTTPProvider(RPC_URL))

# 1. 发现 TEE 执行器
print("发现 TEE 执行器...")
reg = w3.eth.contract(address=Web3.to_checksum_address(REGISTRY), abi=TEE_REGISTRY_ABI)
svc = reg.functions.getServicesByCapability(0, True).call()
if not svc:
    print("ERROR: 没有可用的执行器", file=sys.stderr)
    sys.exit(1)
node = svc[0][0]
executor = Web3.to_checksum_address(node[1])
pub = bytes(node[3])
print(f"执行器: {executor}")

# 2. 用 Ritual LLM 网关加密 secrets（不需要外部 API key）
secrets_json = b'{"LLM_PROVIDER":"ritual"}'
enc = ecies_encrypt(pub.hex(), secrets_json)

# 3. 构造 23 字段请求
delivery_selector = Web3.keccak(text="onSovereignAgentResult(bytes32,bytes)")[:4]
consumer_addr = Web3.to_checksum_address(CONSUMER)
max_poll_block = 6000  # 官方默认值，最大偏移 70000

params = (
    executor,           # 0: executor
    500,                # 1: ttl
    b"",                # 2: userPublicKey
    5,                  # 3: pollInterval
    max_poll_block,     # 4: maxPollBlock
    "SOVEREIGN_AGENT_TASK",  # 5
    consumer_addr,      # 6: callbackAddr (官方合约)
    delivery_selector,  # 7: callbackSelector
    3_000_000,          # 8: gasLimit
    1_000_000_000,      # 9: maxFeePerGas
    100_000_000,        # 10: maxPriorityFeePerGas
    6,                  # 11: cliType (6=ZeroClaw)
    "Say hello world",  # 12: prompt
    enc,                # 13: encryptedSecrets
    ("", "", ""),       # 14: convoHistory (空，不需要 HuggingFace)
    ("", "", ""),       # 15: output
    [],                 # 16: skills
    ("", "", ""),       # 17: systemPrompt
    "zai-org/GLM-4.7-FP8",  # 18: model (Ritual 网关)
    [],                 # 19: tools
    5,                  # 20: maxTurns
    2048,               # 21: maxTokens
    "",                 # 22: rpcUrls
)

# 4. ABI 编码
REQUEST_TYPES = [
    "address", "uint256", "bytes", "uint64", "uint64", "string",
    "address", "bytes4", "uint256", "uint256", "uint256", "uint16",
    "string", "bytes", "(string,string,string)", "(string,string,string)",
    "(string,string,string)[]", "(string,string,string)", "string", "string[]",
    "uint16", "uint32", "string",
]
request_input = encode(REQUEST_TYPES, list(params))

print(f"请求大小: {len(request_input)} bytes")
print(f"REQUEST_INPUT=0x{request_input.hex()}")

# 5. 编码 callSovereignAgent(bytes) calldata
func_sig = Web3.keccak(text="callSovereignAgent(bytes)")[:4]
calldata = func_sig + encode(["bytes"], [request_input])
print(f"CALLDATA=0x{calldata.hex()}")
