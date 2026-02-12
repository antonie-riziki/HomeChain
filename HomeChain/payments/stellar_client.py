from stellar_sdk import (
    Server, 
    Keypair, 
    TransactionBuilder, 
    Network,
    Asset,
    Account,
    SorobanServer,
    scval
)
from stellar_sdk.contract import ContractClient
from stellar_sdk.exceptions import NotFoundError, BadResponseError, BadRequestError
from django.conf import settings
import requests
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class StellarEscrowClient:
    """Stellar blockchain integration for escrow payments"""
    
    def __init__(self):
        # Use testnet for development
        self.horizon_url = "https://horizon-testnet.stellar.org"
        self.soroban_url = "https://soroban-testnet.stellar.org"
        self.network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE
        
        # Production settings
        if getattr(settings, 'STELLAR_NETWORK', 'testnet') == 'public':
            self.horizon_url = "https://horizon.stellar.org"
            self.soroban_url = "https://soroban.stellar.org"
            self.network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE
        
        self.horizon_server = Server(self.horizon_url)
        self.soroban_server = SorobanServer(self.soroban_url)
        
        # Platform fee account
        self.platform_keypair = Keypair.from_secret(settings.STELLAR_PLATFORM_SECRET)
        
        # Contract ID from environment
        self.contract_id = settings.STELLAR_ESCROW_CONTRACT_ID
        self.contract_client = ContractClient(
            self.contract_id,
            self.soroban_server,
            self.network_passphrase
        )
    
    def create_escrow_account(self, employer_secret=None):
        """Create a new Stellar account for escrow"""
        try:
            escrow_keypair = Keypair.random()
            
            # Fund on testnet
            if getattr(settings, 'STELLAR_NETWORK', 'testnet') == 'testnet':
                url = f"https://friendbot.stellar.org?addr={escrow_keypair.public_key}"
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                logger.info(f"Created escrow account: {escrow_keypair.public_key}")
            
            return {
                'public_key': escrow_keypair.public_key,
                'secret_key': escrow_keypair.secret,
            }
        except Exception as e:
            logger.error(f"Failed to create escrow account: {str(e)}")
            raise
    
    def create_escrow(self, employer_secret, worker_public, amount, job_id, contract_id):
        """Create a new escrow contract on Stellar (alias for create_escrow_contract)"""
        return self.create_escrow_contract(employer_secret, worker_public, amount, job_id, contract_id)
    
    def create_escrow_contract(self, employer_secret, worker_public, amount, job_id, contract_id):
        """Create a new escrow contract on Stellar"""
        try:
            employer_keypair = Keypair.from_secret(employer_secret)
            
            # Convert amount to stroops (1 XLM = 10,000,000 stroops)
            # For USDC, 1 USDC = 10,000,000 stroops
            amount_stroops = int(Decimal(str(amount)) * Decimal('10000000'))
            
            # Get employer account
            employer_account = self.horizon_server.load_account(employer_keypair.public_key)
            
            # Contract parameters
            params = [
                scval.to_address(employer_keypair.public_key),
                scval.to_address(worker_public),
                scval.to_int128(amount_stroops),
                scval.to_address(settings.STELLAR_USDC_CONTRACT),  # USDC contract
                scval.to_uint32(job_id),
                scval.to_uint32(contract_id)
            ]
            
            # Invoke contract
            tx = self.contract_client.invoke_contract(
                "create_escrow",
                params,
                employer_keypair,
                employer_account.sequence
            )
            
            # Submit transaction
            response = self.horizon_server.submit_transaction(tx)
            tx_hash = response['hash']
            
            # Extract escrow ID from response (you'll need to parse this based on your contract)
            escrow_id = f"escrow_{job_id}_{contract_id}"
            
            logger.info(f"Created escrow contract: {escrow_id}, tx: {tx_hash}")
            
            return {
                'escrow_id': escrow_id,
                'transaction_hash': tx_hash,
                'contract_id': self.contract_id,
                'status': 'created'
            }
            
        except Exception as e:
            logger.error(f"Failed to create escrow contract: {str(e)}")
            raise
    
    def fund_escrow(self, employer_secret, escrow_id, amount):
        """Fund the escrow contract"""
        try:
            employer_keypair = Keypair.from_secret(employer_secret)
            employer_account = self.horizon_server.load_account(employer_keypair.public_key)
            
            amount_stroops = int(Decimal(str(amount)) * Decimal('10000000'))
            
            # First approve USDC transfer
            self._approve_token_transfer(
                employer_keypair,
                self.contract_id,
                amount_stroops
            )
            
            # Fund escrow
            params = [scval.to_uint32(escrow_id)]
            
            tx = self.contract_client.invoke_contract(
                "fund_escrow",
                params,
                employer_keypair,
                employer_account.sequence
            )
            
            response = self.horizon_server.submit_transaction(tx)
            
            logger.info(f"Funded escrow: {escrow_id}, tx: {response['hash']}")
            
            return {
                'escrow_id': escrow_id,
                'transaction_hash': response['hash'],
                'status': 'funded'
            }
            
        except Exception as e:
            logger.error(f"Failed to fund escrow: {str(e)}")
            raise
    
    def release_payment(self, contract, approved_by):
        """Release payment from escrow"""
        try:
            # Get keypair of approver
            if approved_by == contract.employer:
                keypair = Keypair.from_secret(contract.employer.stellar_secret_key)
                is_employer = True
            else:
                keypair = Keypair.from_secret(contract.worker.stellar_secret_key)
                is_employer = False
            
            account = self.horizon_server.load_account(keypair.public_key)
            
            # Approve completion
            params = [
                scval.to_uint32(contract.escrow.stellar_escrow_id),
                scval.to_bool(is_employer)
            ]
            
            tx = self.contract_client.invoke_contract(
                "approve_completion",
                params,
                keypair,
                account.sequence
            )
            
            response = self.horizon_server.submit_transaction(tx)
            
            logger.info(f"Released payment for escrow: {contract.escrow.stellar_escrow_id}")
            
            return {
                'transaction_hash': response['hash'],
                'status': 'released'
            }
            
        except Exception as e:
            logger.error(f"Failed to release payment: {str(e)}")
            raise
    
    def _approve_token_transfer(self, keypair, spender, amount):
        """Approve USDC token transfer"""
        try:
            token_contract = ContractClient(
                settings.STELLAR_USDC_CONTRACT,
                self.soroban_server,
                self.network_passphrase
            )
            
            account = self.horizon_server.load_account(keypair.public_key)
            
            params = [
                scval.to_address(keypair.public_key),
                scval.to_address(spender),
                scval.to_int128(amount)
            ]
            
            tx = token_contract.invoke_contract(
                "approve",
                params,
                keypair,
                account.sequence
            )
            
            response = self.horizon_server.submit_transaction(tx)
            return response
            
        except Exception as e:
            logger.error(f"Failed to approve token transfer: {str(e)}")
            raise
    
    def get_escrow_status(self, escrow_id):
        """Get escrow status from blockchain"""
        try:
            params = [scval.to_uint32(escrow_id)]
            
            result = self.contract_client.invoke_contract(
                "get_escrow",
                params,
                source=None
            )
            
            # Parse result - adjust based on your contract return format
            status_map = {0: 'PENDING', 1: 'FUNDED', 2: 'COMPLETED', 3: 'DISPUTED'}
            
            return {
                'status': status_map.get(result[0], 'UNKNOWN'),
                'employer_approved': result[1],
                'worker_approved': result[2],
                'completed': result[3] if len(result) > 3 else False
            }
            
        except Exception as e:
            logger.error(f"Failed to get escrow status: {str(e)}")
            raise
    
    def get_account_balance(self, public_key):
        """Get account balance from Stellar"""
        try:
            account = self.horizon_server.accounts().account_id(public_key).call()
            balances = {}
            
            for balance in account['balances']:
                if balance['asset_type'] == 'native':
                    balances['XLM'] = float(balance['balance'])
                else:
                    asset_code = balance.get('asset_code', 'UNKNOWN')
                    balances[asset_code] = float(balance['balance'])
            
            return balances
            
        except NotFoundError:
            return {'XLM': 0}
        except Exception as e:
            logger.error(f"Failed to get account balance: {str(e)}")
            raise
    
    def send_payment(self, from_secret, to_public, amount, asset='XLM'):
        """Send direct payment"""
        try:
            from_keypair = Keypair.from_secret(from_secret)
            from_account = self.horizon_server.load_account(from_keypair.public_key)
            
            if asset == 'XLM':
                stellar_asset = Asset.native()
                amount_stroops = str(amount)
            else:
                stellar_asset = Asset(asset, settings.STELLAR_USDC_ISSUER)
                amount_stroops = str(int(Decimal(str(amount)) * Decimal('10000000')))
            
            tx = TransactionBuilder(
                source_account=from_account,
                network_passphrase=self.network_passphrase,
                base_fee=100
            ).append_payment_op(
                destination=to_public,
                amount=amount_stroops,
                asset=stellar_asset
            ).build()
            
            tx.sign(from_keypair)
            response = self.horizon_server.submit_transaction(tx)
            
            return {
                'transaction_hash': response['hash'],
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Failed to send payment: {str(e)}")
            raise