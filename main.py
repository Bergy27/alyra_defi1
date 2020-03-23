'''
https://blockchain.info/rawblock/497153?format=hex
https://www.blockchain.com/btc/block/497153

https://blockchain.info/rawtx/2004dac5fb150bd477b958491892729d90c9d50bf561382ac4e4c23aad18480e?format=hex
https://blockchain.info/rawtx/b9bb64dc4f81e86b9a6ca8944f84f8f421cf104413f8928ee44222400a664b85?format=hex
https://www.blockchain.com/btc/tx/2004dac5fb150bd477b958491892729d90c9d50bf561382ac4e4c23aad18480e
'''

import datetime
import pprint
import requests
import sys
import json

SIZE_HEADER = 80
SIZE_VERSION = 4
SIZE_PREVIOUS_BLOC = 32
SIZE_MERKLE_ROOT = 32
SIZE_TIMESTAMP = 4
SIZE_BITS = 4
SIZE_NONCE = 4

CIBLE_MAX = ((2**16-1)*2**208)

HEX_TO_DEC = {
	"0" : 0,
	"1" : 1,
	"2" : 2,
	"3" : 3,
	"4" : 4,
	"5" : 5,
	"6" : 6,
	"7" : 7,
	"8" : 8,
	"9" : 9,
	"a" : 10,
	"b" : 11,
	"c" : 12,
	"d" : 13,
	"e" : 14,
	"f" : 15 
}
HEX = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f"]

def convertDecToHex(nmb):
	key_list = list(HEX_TO_DEC.keys())
	val_list = list(HEX_TO_DEC.values())

	final = []
	final.append(key_list[val_list.index(nmb%16)])
	result = nmb//16


	while result!=0:
		final.append(key_list[val_list.index(result%16)])
		result = result//16		

	final.reverse()
	return("0x"+"".join(final))



def convertHexToDec(nmb):
	power = 0
	result = 0
	for curr in nmb[::-1]:
		result += HEX_TO_DEC[curr]*16**power
		power +=1
	return result

def convertHexLittleEndiantoHex(nmb):
	splitBy2 = [nmb[i:i+2] for i in range(0, len(nmb), 2)]
	splitBy2.reverse()
	return "".join(splitBy2)

def getHeader(bloc):
	return bloc[:SIZE_HEADER*2], bloc[SIZE_HEADER*2:]

def getVersion(header):
	return convertHexLittleEndiantoHex(header[:SIZE_VERSION*2])

def getPreviousBloc(header):
	return convertHexLittleEndiantoHex(header[SIZE_VERSION*2:SIZE_VERSION*2+SIZE_PREVIOUS_BLOC*2])

def getMerkleRoot(header):
	return convertHexLittleEndiantoHex(header[SIZE_VERSION*2+SIZE_PREVIOUS_BLOC*2:SIZE_VERSION*2+SIZE_PREVIOUS_BLOC*2+SIZE_MERKLE_ROOT*2])

#timestamp to date
def getDate(header):
	timestamp_hex = convertHexLittleEndiantoHex(header[SIZE_VERSION*2+SIZE_PREVIOUS_BLOC*2+SIZE_MERKLE_ROOT*2:SIZE_VERSION*2+SIZE_PREVIOUS_BLOC*2+SIZE_MERKLE_ROOT*2+SIZE_TIMESTAMP*2])
	timestamp_dec = convertHexToDec(timestamp_hex)
	return datetime.datetime.fromtimestamp(timestamp_dec)

def getBits(header):
	return convertHexLittleEndiantoHex(header[SIZE_VERSION*2+SIZE_PREVIOUS_BLOC*2+SIZE_MERKLE_ROOT*2+SIZE_TIMESTAMP*2:SIZE_VERSION*2+SIZE_PREVIOUS_BLOC*2+SIZE_MERKLE_ROOT*2+SIZE_TIMESTAMP*2+SIZE_BITS*2])

def getNonce(header):
	return convertHexLittleEndiantoHex(header[SIZE_VERSION*2+SIZE_PREVIOUS_BLOC*2+SIZE_MERKLE_ROOT*2+SIZE_TIMESTAMP*2+SIZE_BITS*2:SIZE_VERSION*2+SIZE_PREVIOUS_BLOC*2+SIZE_MERKLE_ROOT*2+SIZE_TIMESTAMP*2+SIZE_BITS*2+SIZE_NONCE*2])

def calculateTarget(bits):
	exp_dec = convertHexToDec(bits[0:2])
	coeff_dec = convertHexToDec(bits[2:8])
	return coeff_dec * 2 ** (8*(exp_dec-3))

def getDifficulty(cible):
	return CIBLE_MAX/cible

def getVarInt(restOfBloc):
	if restOfBloc[:2]=="fd":
		return convertHexToDec(convertHexLittleEndiantoHex(restOfBloc[2:6])), restOfBloc[6:]
	elif restOfBloc[:2]=="fe":
		return convertHexToDec(convertHexLittleEndiantoHex(restOfBloc[2:10])), restOfBloc[10:]
	elif restOfBloc[:2]=="ff":
		return convertHexToDec(convertHexLittleEndiantoHex(restOfBloc[2:18])), restOfBloc[18:]
	else:
		return convertHexToDec(convertHexLittleEndiantoHex(restOfBloc[:2])), restOfBloc[2:]

def getNmbOfTransactions(restOfBloc):
	if restOfBloc[:2]=="fd":
		return convertHexToDec(convertHexLittleEndiantoHex(restOfBloc[2:6])), restOfBloc[6:]
	elif restOfBloc[:2]=="fe":
		return convertHexToDec(convertHexLittleEndiantoHex(restOfBloc[2:10])), restOfBloc[10:]
	elif restOfBloc[:2]=="ff":
		return convertHexToDec(convertHexLittleEndiantoHex(restOfBloc[2:18])), restOfBloc[18:]
	else:
		return convertHexToDec(convertHexLittleEndiantoHex(restOfBloc[:2])), restOfBloc[2:]

def getVersionOfTransaction(restOfBloc):
	return convertHexToDec(convertHexLittleEndiantoHex(restOfBloc[:8])), restOfBloc[8:]

def getHashLastTransaction(restOfBloc):
	return restOfBloc[:64], restOfBloc[64:]

def getOutputIndex(restOfBloc):
	return restOfBloc[:8], restOfBloc[8:]


def getScripSIG(restOfBloc, size):
	return restOfBloc[:size*2], restOfBloc[size*2:]

def getScript(restOfBloc, size):
	return restOfBloc[:size*2], restOfBloc[size*2:]


def getSequence(restOfBloc):
	return restOfBloc[:8], restOfBloc[8:]

def getAmount(restOfBloc):
	return satoshiToBTC(convertHexToDec(convertHexLittleEndiantoHex(restOfBloc[:16]))), restOfBloc[16:]

def satoshiToBTC(amount):
	return amount/100000000

def getLockTime(restOfBloc):
	locktime = convertHexToDec(convertHexLittleEndiantoHex(restOfBloc[:8]))
	if locktime<500000000:
		return locktime, restOfBloc[8:]
	else:
		return datetime.datetime.fromtimestamp(locktime), restOfBloc[8:]	

def getStackItem(restOfBloc, size):
	return restOfBloc[:size*2], restOfBloc[size*2:]



res = requests.get("https://blockchain.info/rawblock/{}?format=hex".format(sys.argv[1]))
bloc = res.text

header, restOfBloc = getHeader(bloc)
bits = getBits(header)
target = calculateTarget(bits)
json_bloc = {
	"version" : getVersion(header),
	"previous_block" : getPreviousBloc(header),
	"merkle_root" : getMerkleRoot(header),
	"date" : str(getDate(header)),
	"bits" : bits,
	"target" : target,
	"difficulty" : getDifficulty(target),
	"nonce" : getNonce(header),
	"transactions" : [],
}

numberofTransactions, restOfBloc = getNmbOfTransactions(restOfBloc)
json_bloc["number_of_transactions"] = numberofTransactions

#transaction = 1
while numberofTransactions>0:
	transaction = {}

	version, restOfBloc = getVersionOfTransaction(restOfBloc)
	transaction["version"] = version

	if restOfBloc[:4]=="0001":
		restOfBloc = restOfBloc[4:]
		witness=True
	else:
		witness=False


	numberOfInput, restOfBloc = getVarInt(restOfBloc)
	numberOfInputCopy = numberOfInput
	transaction["number_of_inputs"] = numberOfInput

	transaction["inputs"] = []
	#Loop on inputs
	while numberOfInput>0:
		hashLastTransaction, restOfBloc = getHashLastTransaction(restOfBloc)
		outputIndex, restOfBloc = getOutputIndex(restOfBloc)
		sizeOfScriptSIG, restOfBloc = getVarInt(restOfBloc)
		scriptSIG, restOfBloc = getScripSIG(restOfBloc, sizeOfScriptSIG)
		sequence, restOfBloc = getSequence(restOfBloc)

		transaction["inputs"].append({
			"hash_last_transaction" : hashLastTransaction,
			"output_index" : outputIndex,
			"sig_script" : scriptSIG,
			"sequence" : sequence
		})

		numberOfInput-=1

	numberofOutput, restOfBloc = getVarInt(restOfBloc)
	transaction["number_of_outputs"] = numberofOutput
	transaction["outputs"] = []

	#Loop on outputs
	while numberofOutput>0:
		amount, restOfBloc = getAmount(restOfBloc)
		sizeOfScript, restOfBloc = getVarInt(restOfBloc)
		script, restOfBloc = getScript(restOfBloc, sizeOfScript)
		transaction["outputs"].append({
			"amount" : amount,
			"script" : script
		})
		numberofOutput-=1

	if witness:
		tmp = 0
		while (numberOfInputCopy>0):
			transaction["inputs"][tmp]["witness"] = []
			numberOfStackItem, restOfBloc = getVarInt(restOfBloc)
			while numberOfStackItem>0:
				sizeOfStackItems, restOfBloc = getVarInt(restOfBloc)
				stackItem, restOfBloc = getStackItem(restOfBloc, sizeOfStackItems)
				transaction["inputs"][tmp]["witness"].append(stackItem)
				numberOfStackItem-=1
			numberOfInputCopy-=1
			tmp+=1


	locktime, restOfBloc = getLockTime(restOfBloc)
	transaction["locktime"] = str(locktime)
	json_bloc["transactions"].append(transaction)
	numberofTransactions-=1

with open(sys.argv[1]+'.json', 'w', encoding='utf-8') as f:
    json.dump(json_bloc, f, ensure_ascii=False, indent=4)
	

