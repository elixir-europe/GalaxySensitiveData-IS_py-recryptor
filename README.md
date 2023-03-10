# GalaxySensitiveData-IS_py-recryptor
Repository for the python command line tool to recrypt


## Installation
Install the Python dependencies in a virtual environment:

```bash
python3 -m venv .py3env
source .py3env/bin/activate
pip install --upgrade pip wheel
pip install git+https://github.com/elixir-europe/GalaxySensitiveData-IS_py-recryptor.git
```

## Usage

```bash
crypt4gh-recryptor --full-help
```

```
usage: crypt4gh-recryptor [-h] [--full-help] {recrypt,decrypt,get-header} ...

Crypt4GH header recryptor

options:
  -h, --help            show this help message and exit
  --full-help           It returns full help (default: False)

operations:
  What to do with the input file, either recrypt or decrypt (or simply getting the header)

  {recrypt,decrypt,get-header}
    recrypt             Re-encryption params
    decrypt             Decryption params
    get-header          crypt4gh get header params

Operation 'recrypt'
usage: crypt4gh-recryptor recrypt [-h] --encryption-key ENCRYPTION_KEYS -i INPUT_FILE -o OUTPUT_FILE --decryption-key
                                  DECRYPTION_KEY

options:
  -h, --help            show this help message and exit
  --encryption-key ENCRYPTION_KEYS
                        The file(s) with the key(s) to reencrypt the header (default: None)
  -i INPUT_FILE, --input INPUT_FILE
                        The encrypted input file (or only its header) (default: None)
  -o OUTPUT_FILE, --output OUTPUT_FILE
                        The output file. Depending on the operation, it can be the reencrypted header, the decrypted contents of
                        the input file or the crypt4gh header from the input file (default: None)
  --decryption-key DECRYPTION_KEY
                        The file with the key to open the encrypted header (default: None)

Operation 'decrypt'
usage: crypt4gh-recryptor decrypt [-h] --header HEADER_FILE -i INPUT_FILE -o OUTPUT_FILE --decryption-key DECRYPTION_KEY

options:
  -h, --help            show this help message and exit
  --header HEADER_FILE  The alternate header file to be used to decrypt (default: None)
  -i INPUT_FILE, --input INPUT_FILE
                        The encrypted input file (or only its header) (default: None)
  -o OUTPUT_FILE, --output OUTPUT_FILE
                        The output file. Depending on the operation, it can be the reencrypted header, the decrypted contents of
                        the input file or the crypt4gh header from the input file (default: None)
  --decryption-key DECRYPTION_KEY
                        The file with the key to open the encrypted header (default: None)

Operation 'get-header'
usage: crypt4gh-recryptor get-header [-h] [--payload PAYLOAD_FILE] -i INPUT_FILE -o OUTPUT_FILE

options:
  -h, --help            show this help message and exit
  --payload PAYLOAD_FILE
                        The optional payload output file, where only the payload is saved (default: None)
  -i INPUT_FILE, --input INPUT_FILE
                        The encrypted input file (or only its header) (default: None)
  -o OUTPUT_FILE, --output OUTPUT_FILE
                        The output file. Depending on the operation, it can be the reencrypted header, the decrypted contents of
                        the input file or the crypt4gh header from the input file (default: None)

```

## Demo

```bash
# This step splits an encrypted crypt4gh file into its header and its payload
crypt4gh-recryptor get-header -i test_data/data-fega.c4gh -o /tmp/data-fega-header.c4gh --payload /tmp/data-fega-payload.c4g

# The decryption of the payload should complain (due wrong decryption key)
crypt4gh-recryptor decrypt --header /tmp/data-fega-header.c4gh -i /tmp/data-fega-payload.c4gh -o /tmp/data-fega-clear.txt --decryption-key test_data/fega.priv

# The decryption of the payload should work (due right decryption key)
crypt4gh-recryptor decrypt --header /tmp/data-fega-header.c4gh -i /tmp/data-fega-payload.c4gh -o /tmp/data-fega-clear.txt --decryption-key test_data/user_key.priv

cat /tmp/data-fega-clear.txt

# This one should re-encrypt the header with the compute node key
crypt4gh-recryptor recrypt -i /tmp/data-fega-header.c4gh -o /tmp/data-fega-compute-header.c4gh --decryption-key test_data/user_key.priv --encryption-key test_data/compute_node_key.pub

# And this one should decrypt the payload using the re-encrypted header
# and the compute node decryption key
crypt4gh-recryptor decrypt --header /tmp/data-fega-compute-header.c4gh -i /tmp/data-fega-payload.c4gh -o /tmp/data-fega-clear_compute.txt --decryption-key test_data/compute_node_key.priv

# So next one should return nothing
diff /tmp/data-fega-clear.txt /tmp/data-fega-clear_compute.txt
```