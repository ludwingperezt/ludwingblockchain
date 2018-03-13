import hashlib
import json
import requests
from time import time
from urllib.parse import urlparse

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # Crear el bloque inicial
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """Crea un nuevo bloque y lo agrega a la cadena

        :param proof: <int> La 'prueba', dada por el algorítmo 'Proof of work'
        :param previous_hash: (Opcional) <str> Hash del bloque previo
        :return: <Dict> Nuevo bloque
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Re-iniciar la lista de transacciones
        self.current_transactions = []
        self.chain.append(block)

        return block

    def new_transaction(self, sender, recipient, amount):
        """Agrega una nueva transacción a la lista de transacciones

        :param sender: <str> Dirección del remitente
        :param recipient: <str> Dirección del destinatario
        :param amount: <int> Monto de la transacción
        :return: <int> El índice del bloque que contendrá ésta transacción.
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """Genera el Hash SHA-256 de un bloque
        :param block: <dict> Bloque
        :return: <str>
        """
        
        # Asegurar que el diccionario está ordenado o se tendrán hashes inconsistentes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        """Retorna el último bloque de la cadena"""
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """Algorítmo simple Proof of Work
        - Encontrar un número 'p' tal que hash(p) contenga adelante 4 ceros, donde p es la previa p'
        - p es la prueba previa, y p' es la nueva prueba

        :param last_proof: <int>
        :return: <int>
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """Valida la prueba: hash(last_proof, proof) contiene 4 ceros al inicio?

        :param last_proof: <int> Prueba previa
        :param proof: <int> Prueba actual
        :return: <bool> True si es correcta, de lo contrario False
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'

    def register_node(self, address):
        """Agregar un nodo a la lista de nodos

        :param address: <str> Dirección del nodo: por ejemplo: 'http://198.135.120.6:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """Determina si la cadena recibida es válida

        :param chain: <list> Una cadena
        :return: <bool> True si es válida, de lo contrario False
        """
        last_block = chain[0]
        current_index = 1
        chain_length = len(chain)

        while current_index < chain_length:
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n------------\n")

            # Verificar que el hash del bloque es correcto
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Verificar que la prueba de trabajo es correcta
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1
        
        return True
    
    def resolve_conflicts(self):
        """Algoritmo de consenso: Resuelve los conflictos
        reemplazando la cadena local con la cadena más larga
        en la red.

        :return: <bool> True si la cadena fue reemplazada, de lo contrario False
        """

        neighbours = self.nodes
        new_chain = None

        # Solamente se buscan cadenas más largas que la local
        max_length = len(self.chain)

        # Obtener y verificar las cadenas de todos los nodos en nuestra red
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Verificar si la longitud es más larga para el presente nodo
                # Y si la cadena es válida

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Reemplazar la cadena local si es más larga y si es válida
        if new_chain:
            self.chain = new_chain
            return True

        return False
