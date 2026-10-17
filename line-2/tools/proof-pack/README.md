# Proof Pack

Share an Ethereum account/storage witness with repeated trie nodes stored once.
Proof Pack verifies the original evidence against the caller's explicit state
root, address and exact slot set before packing, then expands and verifies it
again. Unpack exports the existing `state-witness/1` format for other line tools.
Python 3.9+ standard library only; keep the sibling `state-witness/` folder.

From the repository root, run the real historical ZTO demonstration offline:

```sh
python3 -B line-2/tools/proof-pack/pack.py demo
```

When tried on 2026-10-17, ZTO's two requested absent slots shared a trie node.
The 17 node occurrences became 16 unique nodes; compact JSON fell from **14,076
to 13,094 bytes** (982 bytes, about 7%). Expansion preserved the entire original
witness and verified the same account and slot results. The real ZTO/IMD pool
trial also verified its nonzero storage value:

```sh
python3 -B line-2/tools/proof-pack/pack.py demo --pool
```

That fixture has 17 unique nodes and no repetition. Its compact JSON **grew from
14,617 to 14,704 bytes** because the reference table adds overhead. Packing is
useful for shared nodes, not a guarantee of compression. Counts compare compact
JSON with identical serialization settings, not whitespace in source files.
Both examples reuse ancestor evidence unchanged and need no network. Demo roots
are historical RPC observations, not authenticated consensus checkpoints.

## Caller-supplied evidence

Commands print only JSON to stdout and write no files. Supply an independently
authenticated state root, the intended account and every requested slot:

```sh
python3 -B line-2/tools/proof-pack/pack.py pack \
  line-2/tools/state-witness/examples/zto-mainnet.json \
  --state-root 0x70c13580735123b57c0a9a24692875f4ef366b04c69d92af9f539561e626d512 \
  --address 0xd782bdea4ef02a0bd391eb9089470c8080f0a68e \
  --slot 0x0 --slot 0x1
```

Save stdout to a workspace path of your choice. Use `verify saved-pack.json`
with the same flags to print verified state, or `unpack saved-pack.json` to
print an ordinary witness. Never redirect onto the input file: the shell would
truncate it before Python starts. No checkpoint is read from the pack metadata.
Omit `--slot` for an account-only proof; repeat it for multiple slots.

`proof-pack/1` contains exactly `format`, `nodes` and `witness`. `nodes` is an
array of unique lowercase 0x-prefixed node byte strings. In the embedded witness,
only `proof.accountProof` and each `proof.storageProof[].proof` become arrays of
zero-based integer indices into `nodes`. Other metadata remains data. Node order
is first encounter order; proof-node ordering and repeated occurrences survive
expansion. Hex letter case is normalized; arbitrary original JSON whitespace and
key order are not preserved. No deletion of unrelated proof nodes is attempted.

The decoder rejects booleans/floats/strings as indices, out-of-range references,
unused or duplicate dictionary nodes, noncanonical node hex, oversized lists,
unknown top-level fields and failed proofs. Input, compact output and expanded
witness are bounded to 1,000,000 bytes; at most 64 slots and 128 nodes per proof.
All input paths and symlink targets must stay inside the current workspace.
Duplicate JSON keys and non-finite constants are rejected. Exit 1 gives generic
error JSON on stderr and no partial success; argument errors exit 2.

Fifteen adversarial and real-chain tests passed, covering both real fixtures,
immutability, empty tries, changed claims/nodes/references, caller expectations,
metadata independence, malformed structures and clean CLI failure:

```sh
python3 -B -m unittest discover -s line-2/tools/proof-pack -p 'test_*.py' -v
```

This is an alternate evidence serialization, not a new trust source. It does not
verify consensus, finality, contract behavior, ABI, storage layout, token balances
or current prices. Native ETH balance is the account's balance. The tool imports
the sibling verifier but never calls its network capture helpers. It reads only
workspace inputs, does not access environment variables, wallets or secrets,
and never signs, sends, pays, posts or deploys. No new coin is needed.
