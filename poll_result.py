#!/usr/bin/env python3
"""轮询 SovereignAgentResultDelivered 事件，等待 Phase 2 结果。"""
import sys
import time
from web3 import Web3
from eth_abi.abi import decode

RPC_URL = "https://rpc.ritualfoundation.org"
CONSUMER = "0x24e638d25930290e20D6566f8f50Bf9853B87A14"
TX_HASH = "0x3b7159bc40e30647f972907d5a73790d66ef17d011af01142c36682d6c30f1fe"
FROM_BLOCK = 38642136
TIMEOUT = 300

w3 = Web3(Web3.HTTPProvider(RPC_URL))

event_sig = Web3.keccak(text="SovereignAgentResultDelivered(bytes32,bytes)")
tx_hash_clean = TX_HASH[2:] if TX_HASH.startswith("0x") else TX_HASH
job_topic = "0x" + tx_hash_clean.rjust(64, "0")

print(f"等待 Phase 2 结果（最多 {TIMEOUT}s）...")
print(f"监听合约: {CONSUMER}")
print(f"交易哈希: {TX_HASH}")
print()

start = time.time()
while time.time() - start < TIMEOUT:
    try:
        logs = w3.eth.get_logs({
            "address": Web3.to_checksum_address(CONSUMER),
            "topics": [event_sig, job_topic],
            "fromBlock": FROM_BLOCK,
            "toBlock": "latest",
        })
    except Exception as e:
        # 范围太大时缩小查询窗口
        current = w3.eth.block_number
        logs = w3.eth.get_logs({
            "address": Web3.to_checksum_address(CONSUMER),
            "topics": [event_sig, job_topic],
            "fromBlock": max(FROM_BLOCK, current - 5000),
            "toBlock": "latest",
        })

    if logs:
        raw_data = bytes(logs[0]["data"])
        (result_bytes,) = decode(["bytes"], raw_data)
        try:
            success, error, text, _, _, artifacts = decode(
                [
                    "bool",
                    "string",
                    "string",
                    "(string,string,string)",
                    "(string,string,string)",
                    "(string,string,string)[]",
                ],
                result_bytes,
            )
        except Exception:
            success, error, text = None, None, result_bytes.hex()[:200]
            artifacts = []

        elapsed = time.time() - start
        print(f"{'=' * 60}")
        print(f"✅ Phase 2 已交付！耗时 {elapsed:.1f}s")
        print(f"{'=' * 60}")
        print(f"成功: {success}")
        if error:
            print(f"错误: {error}")
        print(f"AI 回复: {text if text else '(空)'}")
        print(f"工件数量: {len(artifacts)}")
        print(f"{'=' * 60}")
        sys.exit(0)

    elapsed = time.time() - start
    print(f"\r  轮询中... {elapsed:.0f}s", end="", flush=True)
    time.sleep(2)

print(f"\n超时：{TIMEOUT}s 内未收到 Phase 2 结果", file=sys.stderr)
sys.exit(1)
