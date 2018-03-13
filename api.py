"""
Tomado de "Learn Blockchains by Building One"
https://hackernoon.com/learn-blockchains-by-building-one-117428612f46
Autor: https://hackernoon.com/@vanflymen

"""
from blockchain import Blockchain
from uuid import uuid4
from flask import Flask, jsonify, request

# Instanciar el nodo
app = Flask(__name__)

# Generar una dirección global única para éste mando
node_identifier = str(uuid4()).replace('-', '')

# Instanciar la cadena
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    # Correr el algoritmo Proof of work para obtener la siguiente prueba
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Asignar recompensa por validar el bloque.
    # El remitente de la transacción es cero porque
    # se ha minado (validado) un bloque nuevo.
    blockchain.new_transaction(sender="0", recipient=node_identifier, amount=1)

    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)
    response = {
        'message': 'Bloque creado!',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }

    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Crea una nueva transacción
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes)
    }

    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consenus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced!',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)