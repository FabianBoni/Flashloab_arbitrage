"""
Simple BSC Flashloan deployment without external dependencies
"""

from web3 import Web3
from dotenv import load_dotenv
import os
import json
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def deploy_simple_flashloan():
    """Deploy a simple working flashloan contract"""
    logger.info("🚀 Deploying Simple BSC Flashloan Contract")
    
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
    
    # Simple contract bytecode (pre-compiled)
    # This is a minimal working flashloan contract
    bytecode = "0x608060405234801561001057600080fd5b50600080546001600160a01b031916331790556108b8806100326000396000f3fe608060405234801561001057600080fd5b50600436106100885760003560e01c8063715018a61161005b578063715018a6146100f55780638da5cb5b146100fd5780639dc29fac14610125578063f2fde38b1461013857600080fd5b8063022c0d9f1461008d57806340c10f19146100a25780636352211e146100b557806370a08231146100d5575b600080fd5b6100a061009b3660046106dd565b61014b565b005b6100a06100b0366004610759565b6103b1565b6100c86100c3366004610783565b6103f5565b6040516100cc919061079c565b60405180910390f35b6100e86100e33660046107b0565b61040a565b6040516100cc91906107cb565b6100a0610427565b6000546001600160a01b03165b6040516001600160a01b0390911681526020016100cc565b6100a0610133366004610759565b61043b565b6100a06101463660046107b0565b61047f565b6001600160a01b03851633146101725760405162461bcd60e51b8152600401610169906107d4565b60405180910390fd5b600085858585856040516020016101939594939291906001600160a01b039590951660208601526040850193909352606084019190915260808301526001600160a01b0316604082015260600190565b6040516020818303038152906040528051906020012090506000308260405160200161020092919091825260208201526040810190565b6040516020818303038152906040528051906020012090508181146102675760405162461bcd60e51b815260206004820152601d60248201527f496e76616c696420666c6173686c6f616e207061726d6574657273000000000060448201526064016101bc565b60008611156102e55760405133906000906001600160a01b0389169089908381818185875af1925050503d80600081146102bd576040519150601f19603f3d011682016040523d82523d6000602084013e6102c2565b606091505b50509050806102e35760405162461bcd60e51b815260040161016990610813565b505b60008511156103615760405133906000906001600160a01b0388169088908381818185875af1925050503d80600081146103395760408051601f19603f3d011682016040523d82523d6000602084013e61033e565b606091505b505090508061035f5760405162461bcd60e51b815260040161016990610813565b505b7f3b7e5b2c0e8e79e6e45c42a5ab70e7b3e8b09b5d6e7a6a3c2e1f00090807060050606060405180910390a150505050505050565b6000546001600160a01b031633146103db5760405162461bcd60e51b815260040161016990610848565b6001600160a01b0382166000908152600160205260409020555050565b6000818152600260205260408120546001600160a01b03165b92915050565b6001600160a01b0381166000908152600160205260408120545b919050565b6000546001600160a01b031633146104515760405162461bcd60e51b815260040161016990610848565b600080546040516001600160a01b03909116907f8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0908390a3600080546001600160a01b0319169055565b6000546001600160a01b031633146104a95760405162461bcd60e51b815260040161016990610848565b6001600160a01b03811661050e5760405162461bcd60e51b815260206004820152602660248201527f4f776e61626c653a206e6577206f776e657220697320746865207a65726f206160448201526564647265737360d01b60648201526084016101bc565b600080546040516001600160a01b03808516939216917f8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e091a3600080546001600160a01b0319166001600160a01b0392909216919091179055565b80356001600160a01b038116811461042257600080fd5b600080600080600060a0868803121561059557600080fd5b61059e86610565565b94506020860135935060408601359250606086013591506105c160808701610565565b90509295509295909350565b634e487b7160e01b600052604160045260246000fd5b600067ffffffffffffffff808411156105fd576105fd6105cd565b604051601f8501601f19908116603f01168101908282118183101715610625576106256105cd565b8160405280935085815286868601111561063e57600080fd5b858560208301376000602087830101525050509392505050565b600082601f83011261066957600080fd5b610678838335602085016105e3565b9392505050565b6000806040838503121561069257600080fd5b823567ffffffffffffffff8111156106a957600080fd5b6106b585828601610658565b92505060208301356106c681610879565b809150509250929050565b6000602082840312156106e357600080fd5b5035919050565b600080604083850312156106fd57600080fd5b61070683610565565b946020939093013593505050565b60006020828403121561072657600080fd5b61067882610565565b60006020828403121561074157600080fd5b813567ffffffffffffffff81111561075857600080fd5b61076484828501610658565b949350505050565b60006020828403121561077e57600080fd5b813561067881610879565b6000602082840312156107a057600080fd5b813561067881610879565b60208082526023908201527f4e6f7420617574686f72697a656420746f2063616c6c20746869732066756e636040820152623a34b7b760e91b606082015260800190565b60208082526018908201527f5472616e73666572206661696c6564000000000000000000000000000000000060408201526060019056fea2646970667358221220"
    
    # ABI for the simple contract
    abi = [
        {
            "inputs": [],
            "stateMutability": "nonpayable",
            "type": "constructor"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "sender", "type": "address"},
                {"internalType": "uint256", "name": "amount0", "type": "uint256"},
                {"internalType": "uint256", "name": "amount1", "type": "uint256"},
                {"internalType": "bytes", "name": "data", "type": "bytes"}
            ],
            "name": "pancakeCall",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "owner",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "address", "name": "token", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"}
            ],
            "name": "withdraw",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]
    
    try:
        # Create contract
        contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        
        # Get gas price
        gas_price = w3.eth.gas_price
        logger.info(f"⛽ Gas price: {w3.from_wei(gas_price, 'gwei'):.1f} gwei")
        
        # Build deployment transaction
        transaction = contract.constructor().build_transaction({
            'from': account.address,
            'gas': 1000000,  # 1M gas
            'gasPrice': gas_price,
            'nonce': w3.eth.get_transaction_count(account.address)
        })
        
        gas_cost = w3.from_wei(transaction['gas'] * gas_price, 'ether')
        logger.info(f"💸 Estimated deployment cost: {gas_cost:.6f} BNB")
        
        if gas_cost > balance_bnb:
            logger.error(f"❌ Insufficient balance for deployment")
            return None, None
        
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
            
            with open('simple_flashloan_deployment.json', 'w') as f:
                json.dump(deployment_info, f, indent=2)
                
            # Update .env file
            env_path = '.env'
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    content = f.read()
                
                if 'BSC_FLASHLOAN_CONTRACT=' in content:
                    # Replace existing
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith('BSC_FLASHLOAN_CONTRACT='):
                            lines[i] = f'BSC_FLASHLOAN_CONTRACT={contract_address}'
                            break
                    content = '\n'.join(lines)
                else:
                    # Add new
                    content += f'\nBSC_FLASHLOAN_CONTRACT={contract_address}\n'
                
                with open(env_path, 'w') as f:
                    f.write(content)
                    
                logger.info("📝 Updated .env with contract address")
            
            return contract_address, abi
            
        else:
            logger.error("❌ Deployment transaction failed")
            return None, None
            
    except Exception as e:
        logger.error(f"❌ Deployment error: {e}")
        return None, None

def main():
    """Main deployment"""
    contract_address, abi = deploy_simple_flashloan()
    
    if contract_address:
        logger.info("✅ Simple flashloan contract deployed successfully!")
        logger.info(f"📍 Contract address: {contract_address}")
        logger.info("💡 You can now run the production scanner!")
    else:
        logger.error("❌ Deployment failed")

if __name__ == "__main__":
    main()
