"""
Deploy BSC Native Flashloan Arbitrage Contract
"""

import json
import os
from web3 import Web3
from solcx import compile_source, install_solc, set_solc_version
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compile_contract():
    """Compile the BSC flashloan contract"""
    logger.info("Compiling BSC Flashloan Arbitrage contract...")
    
    # Read contract source
    contract_path = os.path.join("..", "contracts", "BSCFlashloanArbitrage.sol")
    absolute_path = os.path.abspath(contract_path)
    
    logger.info(f"Looking for contract at: {absolute_path}")
    
    if not os.path.exists(absolute_path):
        logger.error(f"Contract file not found: {absolute_path}")
        # Try alternative path
        alt_path = os.path.join("..", "..", "contracts", "BSCFlashloanArbitrage.sol")
        absolute_alt_path = os.path.abspath(alt_path)
        logger.info(f"Trying alternative path: {absolute_alt_path}")
        
        if os.path.exists(absolute_alt_path):
            contract_path = alt_path
            absolute_path = absolute_alt_path
        else:
            logger.error(f"Contract file not found in alternative path either")
            return None, None
        
    with open(absolute_path, 'r', encoding='utf-8') as file:
        contract_source = file.read()
        
    logger.info(f"Contract source loaded: {len(contract_source)} characters")
    
    try:
        # Install and set Solidity version
        install_solc('0.8.19')
        set_solc_version('0.8.19')
        
        # Compile contract
        compiled_sol = compile_source(
            contract_source,
            output_values=['abi', 'bin']
        )
        
        # Get contract interface
        contract_id, contract_interface = compiled_sol.popitem()
        
        bytecode = contract_interface['bin']
        abi = contract_interface['abi']
        
        logger.info("✅ Contract compiled successfully")
        logger.info(f"   Bytecode size: {len(bytecode)} characters")
        logger.info(f"   ABI functions: {len(abi)} items")
        
        return bytecode, abi
        
    except Exception as e:
        logger.error(f"❌ Compilation failed: {e}")
        return None, None

def deploy_contract():
    """Deploy the compiled contract to BSC"""
    logger.info("Deploying BSC Flashloan Arbitrage contract...")
    
    # Setup Web3
    rpc_url = os.getenv('BSC_RPC_URL', 'https://bsc-dataseed1.binance.org/')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        logger.error("❌ Failed to connect to BSC")
        return None, None
        
    logger.info(f"✅ Connected to BSC: Block {w3.eth.block_number}")
    
    # Setup account
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        logger.error("❌ No private key configured")
        return None, None
        
    account = w3.eth.account.from_key(private_key)
    balance = w3.eth.get_balance(account.address)
    balance_bnb = w3.from_wei(balance, 'ether')
    
    logger.info(f"📄 Deployer: {account.address}")
    logger.info(f"💰 Balance: {balance_bnb:.4f} BNB")
    
    if balance_bnb < 0.01:
        logger.error("❌ Insufficient BNB for deployment (need at least 0.01 BNB)")
        return None, None
    
    # Compile contract
    bytecode, abi = compile_contract()
    if not bytecode or not abi:
        return None, None
    
    try:
        # Create contract
        contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        
        # Get gas price
        gas_price = w3.eth.gas_price
        logger.info(f"⛽ Gas price: {w3.from_wei(gas_price, 'gwei'):.1f} gwei")
        
        # Build deployment transaction
        transaction = contract.constructor().build_transaction({
            'from': account.address,
            'gas': 3000000,  # High gas limit for complex contract
            'gasPrice': gas_price,
            'nonce': w3.eth.get_transaction_count(account.address)
        })
        
        # Estimate actual gas
        estimated_gas = w3.eth.estimate_gas(transaction)
        transaction['gas'] = estimated_gas + 100000  # Add buffer
        
        gas_cost = w3.from_wei(transaction['gas'] * gas_price, 'ether')
        logger.info(f"💸 Estimated deployment cost: {gas_cost:.6f} BNB")
        
        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        logger.info(f"📤 Deployment transaction sent: {tx_hash.hex()}")
        logger.info("⏳ Waiting for confirmation...")
        
        # Wait for confirmation
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if receipt.status == 1:
            contract_address = receipt.contractAddress
            actual_gas_used = receipt.gasUsed
            actual_cost = w3.from_wei(actual_gas_used * gas_price, 'ether')
            
            logger.info("🎉 Contract deployed successfully!")
            logger.info(f"📍 Contract address: {contract_address}")
            logger.info(f"💰 Actual cost: {actual_cost:.6f} BNB")
            logger.info(f"⛽ Gas used: {actual_gas_used:,}")
            
            # Save deployment info
            deployment_info = {
                'contract_address': contract_address,
                'deployer': account.address,
                'deployment_tx': tx_hash.hex(),
                'gas_used': actual_gas_used,
                'deployment_cost_bnb': float(actual_cost),
                'block_number': receipt.blockNumber,
                'abi': abi
            }
            
            with open('bsc_flashloan_deployment.json', 'w') as f:
                json.dump(deployment_info, f, indent=2)
                
            logger.info("💾 Deployment info saved to bsc_flashloan_deployment.json")
            
            return contract_address, abi
            
        else:
            logger.error("❌ Deployment transaction failed")
            return None, None
            
    except Exception as e:
        logger.error(f"❌ Deployment error: {e}")
        return None, None

def verify_deployment(contract_address, abi):
    """Verify the deployed contract"""
    logger.info(f"🔍 Verifying deployed contract at {contract_address}")
    
    # Setup Web3
    rpc_url = os.getenv('BSC_RPC_URL', 'https://bsc-dataseed1.binance.org/')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    try:
        # Check contract code
        code = w3.eth.get_code(contract_address)
        if len(code) > 2:
            logger.info(f"✅ Contract has code: {len(code)} bytes")
        else:
            logger.error("❌ Contract has no code")
            return False
            
        # Create contract instance
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=abi
        )
        
        # Test contract functions
        owner = contract.functions.getOwner().call()
        logger.info(f"✅ Contract owner: {owner}")
        
        # Check if contract can receive BNB
        balance = w3.eth.get_balance(contract_address)
        logger.info(f"💰 Contract balance: {w3.from_wei(balance, 'ether'):.6f} BNB")
        
        logger.info("✅ Contract verification successful!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

def main():
    """Main deployment process"""
    logger.info("🚀 BSC Flashloan Arbitrage Contract Deployment")
    logger.info("=" * 60)
    
    # Deploy contract
    contract_address, abi = deploy_contract()
    
    if contract_address and abi:
        # Verify deployment
        if verify_deployment(contract_address, abi):
            logger.info("🎉 Deployment and verification completed successfully!")
            logger.info(f"📍 Your contract is ready at: {contract_address}")
            logger.info("💡 You can now use this contract for flashloan arbitrage!")
            
            # Update .env file with new contract address
            env_path = '.env'
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_content = f.read()
                
                # Update or add contract address
                if 'BSC_FLASHLOAN_CONTRACT=' in env_content:
                    env_content = env_content.replace(
                        f"BSC_FLASHLOAN_CONTRACT=",
                        f"BSC_FLASHLOAN_CONTRACT={contract_address}"
                    )
                else:
                    env_content += f"\nBSC_FLASHLOAN_CONTRACT={contract_address}\n"
                
                with open(env_path, 'w') as f:
                    f.write(env_content)
                    
                logger.info("📝 Updated .env with new contract address")
        else:
            logger.error("❌ Deployment verification failed")
    else:
        logger.error("❌ Deployment failed")

if __name__ == "__main__":
    main()
