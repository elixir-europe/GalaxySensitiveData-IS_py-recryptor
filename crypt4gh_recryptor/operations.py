#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2023 Barcelona Supercomputing Center (BSC), Spain
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
import io
import shutil
import sys
import logging

import crypt4gh.header
import crypt4gh.keys
import crypt4gh.lib

class MultiStreamReader(io.RawIOBase):
    '''
    This implementation has been inspired on
    
    https://github.com/python/cpython/blob/a43fd45918cef48187053d7c56d3b9bb902151d0/Lib/socket.py#L626-L740
    '''
    def __init__(self, *instreams: "IO[bytes]"):
        super().__init__()
        # Getting a logger focused on specific classes
        self.logger = logging.getLogger(dict(inspect.getmembers(self))['__module__'] + '::' + self.__class__.__name__)
        
        # Right now, hard-coded
        self._mode = "rb"
        self._reading = True
        self._writing = False
        self._instreams = instreams
    
    def readinto(self, b) -> "int":
        self._checkClosed()
        self._checkReadable()
        
        # Fast path
        numread = 0
        for i_in, instream in enumerate(self._instreams):
            partial_bytes = instream.read(len(b)-numread)
            # TODO: should we raise an error in non blocking cases?
            if partial_bytes is not None:
                partial_numread = len(partial_bytes)
                b[numread:numread+partial_numread] = partial_bytes
                numread += partial_numread
                if numread == len(b):
                    break
        
        # This one is for next read
        if i_in > 0:
            self._instreams = self._instreams[i_in:]
        
        return numread
    
    def write(self, b):
        self._checkClosed()
        # It should fail
        self._checkWritable()
        
        # it is a no-op
        pass
        
    def readable(self):
        if self.closed:
            raise ValueError("I/O operations on closed stream")
        
        return self._reading
    
    def writable(self):
        if self.closed:
            raise ValueError("I/O operations on closed stream")
        
        return self._writing
    
    def seekable(self):
        if self.closed:
            raise ValueError("I/O operations on closed stream")
        
        return super().seekable()
    
    def fileno(self):
        self._checkClosed()
        
        raise OSError("This stream is based on several streams, so no underlying fileno")
    
    @property
    def mode(self):
        return self._mode
    
    @property
    def name(self):
        return ''
    
    def close(self):
        if self.closed:
            return
        
        super().close()
        for instream in self._instreams:
            instream.close()
        self._instreams = None


logger = logging.getLogger(__name__)

def do_decrypt_payload(payload_file: "str", header_file: "str", decryption_key_file: "str", output_file: "str", sender_key_file: "Optional[str]" = None, skip_header: "bool" = False, decryption_passphrase: "Optional[str]" = None) -> "int":
    try:
        decryption_key = crypt4gh.keys.get_private_key(decryption_key_file, lambda: decryption_passphrase)
    except:
        logger.exception(f"Unable to read decryption key from {decryption_key_file}")
        return 1
    
    if sender_key_file is not None:
        try:
            sender_pub_key = crypt4gh.keys.get_public_key(sender_key_file)
        except:
            logger.exception(f"Unable to read sender key from {sender_key_file}")
            return 2
    else:
        sender_pub_key = None
    
    try:
        hstream = open(header_file, mode="rb")
        pstream = open(payload_file, mode="rb")
        if skip_header:
            # This one is going to be discarded
            _ = crypt4gh.header.parse(pstream)
        istream = MultiStreamReader(hstream, pstream)
    except:
        logger.exception(f"Unable to open either header from {header_file} or payload from {payload_file} in order to decrypt the latter")
        return 3
        
    try:
        with open(output_file, mode="wb") as ostream:
            keys = [(0, decryption_key, None)]
            crypt4gh.lib.decrypt(
                keys,
                istream,
                ostream,
                sender_pubkey=sender_pub_key
            )
    except:
        logger.exception(f"Unable to decrypt to {output_file}")
        return 4
    
    return 0

def do_recrypt_header(input_file: "str", decryption_key_file: "str", encryption_key_files: "Sequence[str]", output_file: "str", decryption_passphrase: "Optional[str]" = None) -> "int":
    try:
        decryption_key = crypt4gh.keys.get_private_key(decryption_key_file, lambda: decryption_passphrase)
        private_key = [(0, decryption_key, None)]
    except:
        logger.exception(f"Unable to read decryption key from {decryption_key_file}")
        return 1
    
    try:
        encryption_keys = list(map(lambda encryption_key_file: (0, decryption_key, crypt4gh.keys.get_public_key(encryption_key_file)), encryption_key_files))
    except:
        logger.exception(f"Unable to read encryption keys from {' '.join(encryption_key_files)}")
        return 2
    
    try:
        with open(input_file, mode="rb") as istream:
            header_packets = do_recrypt_stream(istream, private_key, encryption_keys)
    except:
        logger.exception(f"Unable to read header from {input_file} in order to reencrypt it")
        return 3
        
    try:
        with open(output_file, mode="wb") as ostream:
            ostream.write(crypt4gh.header.serialize(header_packets))
    except:
        logger.exception(f"Unable to save reencrypted header in {output_file}")
        return 4
    
    return 0

def do_recrypt_stream(istream: "IO[bytes]", decryption_keys: "Sequence[Any]", encryption_keys: "Sequence[Any]") -> "Any":
    # This one is going to be discarded
    header_packets = crypt4gh.header.parse(istream)
    
    return crypt4gh.header.reencrypt(header_packets, decryption_keys, encryption_keys, trim=False)

def do_save_header_and_payload(input_file: "str", output_file: "str", payload_file: "Optional[str]" = None) -> "int":
    try:
        with open(input_file, mode="rb") as iH, open(output_file, mode="wb") as oH:
            do_save_header_stream(iH, oH)
            if payload_file is not None:
                with open(payload_file, mode="wb") as pH:
                    shutil.copyfileobj(iH, pH)
    except:
        logger.exception(f"Unable to extract header from {input_file} or to save it in {output_file}")
        return 5
    
    return 0
    
def do_save_header_stream(istream: "IO[bytes]", ostream: "IO[bytes]") -> None:
    header_packets = crypt4gh.header.parse(istream)
    
    ostream.write(crypt4gh.header.serialize(header_packets))
