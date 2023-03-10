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

import argparse
import sys

from .operations import (
    do_decrypt_payload,
    do_recrypt_header,
    do_save_header,
)

def main():
    ap = argparse.ArgumentParser(
        description="Crypt4GH header recryptor",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    sp = ap.add_subparsers(
        dest="operation",
        title="operations",
        description="What to do with the input file, either recrypt or decrypt (or simply getting the header)"
    )
    
    ap_r = sp.add_parser(
        "recrypt",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help="Re-encryption params",
    )
    
    ap_r.add_argument(
        "--encryption-key",
        dest="key_file",
        help="The file with the key to reencrypt the header"
    )
    
    ap_d = sp.add_parser(
        "decrypt",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help="Decryption params",
    )
    ap_d.add_argument(
        "--header",
        dest="header_file",
        required=True,
        help="The alternate header file to be used to decrypt"
    )
    
    ap_g = sp.add_parser(
        "get-header",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help="crypt4gh get header params",
    )
    
    for ap_ in (ap_r, ap_d, ap_g):
        ap_.add_argument(
            "-i",
            "--input",
            dest="input_file",
            required=True,
            help="The encrypted input file (or only its header)",
        )
        
        ap_.add_argument(
            "-o",
            "--output",
            dest="output_file",
            required=True,
            help="The output file. Depending on the operation, it can be the reencrypted header, the decrypted contents of the input file or the crypt4gh header from the input file",
        )
        
    for ap_ in (ap_r, ap_d):
        ap_.add_argument(
            "--decryption-key",
            dest="key_file",
            help="The file with the key to open the encrypted header"
        )
    
    ap.add_argument(
        "--full-help",
        dest="fullHelp",
        action="store_true",
        default=False,
        help="It returns full help",
    )
    
    args = ap.parse_args()

    fullHelp = args.fullHelp
    if args.operation is None:
        fullHelp = True

    if fullHelp:
        print(ap.format_help())

        # retrieve subparsers from parser
        subparsers_actions = [
            action
            for action in ap._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        # there will probably only be one subparser_action,
        # but better safe than sorry
        for subparsers_action in subparsers_actions:
            # get all subparsers and print help
            for choice, subparser in subparsers_action.choices.items():
                print("Operation '{}'".format(choice))
                print(subparser.format_help())

        sys.exit(0)
    
    retval = 1
    if args.operation == "decrypt":
        retval = do_decrypt_payload(args.input_file, args.header_file, args.decryption_key, args.output_file)
    elif args.operation == "recrypt":
        retval = do_recrypt_header(args.input_file, args.decryption_key, args.encryption_key, args.output_file)
    elif args.operation == "get-header":
        retval = do_save_header(args.input_file, args.output_file)
    
    sys.exit(retval)
    

if __name__ == "__main__":
    main()
