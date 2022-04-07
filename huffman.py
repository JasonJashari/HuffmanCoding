import os
import sys
import pathlib
import json
from bitstring import BitArray

class TreeNode:
    def __init__(self, freq, char):
        self.freq = freq
        self.char = char
        self.left = None
        self.right = None
    
    def __lt__(self, other):
        return self.freq < other.freq

class Mapping:
    def __init__(self, tree):
        self.tree = tree
        self.mapping_dict = {}
        self.reverse_mapping_dict = {}
    
    def create_mapping(self):
        bit_code = ""
        root = self.tree.pop()
        self.map(root, bit_code)
    
    def map(self, root, bit_code):
        if root == None:
            return
        if root.char != None:
            self.mapping_dict[root.char] = bit_code
            self.reverse_mapping_dict[bit_code] = root.char
            return
        self.map(root.left, bit_code+"0")
        self.map(root.right, bit_code+"1")


def build_frequency(text):
    frequency = {}
    for character in text:
        if character in frequency:
            frequency[character] += 1
        else:
            frequency[character] = 1
    return frequency

def build_huffman_tree(stack):
    while len(stack) > 1:
        node_1 = stack.pop()
        node_2 = stack.pop()
        frequency = node_1.freq + node_2.freq

        merged = TreeNode(frequency, None)
        merged.left = node_1
        merged.right = node_2
        
        stack.insert(0,merged)
    return stack

def encode_text(text, mapping_dict):
    encoded_text = ""
    for character in text:
        encoded_text += mapping_dict[character]
    return encoded_text

def encode_mapping(reverse_mapping_dict):
    # convert dictionary to bit string
    # convert dictionary to bytes to bits
    res_bytes = json.dumps(reverse_mapping_dict).encode('utf-8')
    c = BitArray(res_bytes)
    
    return c.bin

def encode_text_tree(encoded_text, encoded_tree):
    # convert bit string to the form: tree info + encoded text + encoded tree
    extra_bits = len(encoded_tree)
    tree_info = '{0:016b}'.format(extra_bits)
    return tree_info + encoded_text + encoded_tree

def pad_encoded_text_tree(encoded_text_tree):
    # convert bit string to the form:
    # padding_info (8bits) + tree_info (16bits) + encoded_text + encoded_tree + padding_bits
    padding = 8 - (len(encoded_text_tree) % 8)
    for i in range(padding):
        encoded_text_tree += "0"
    padding_info = "{0:08b}".format(padding)

    return padding_info + encoded_text_tree


def compress(path):

    file_path, file_extension = os.path.splitext(path)
    output_file = file_path + ".bin"

    with open(path,'r') as file, open(output_file,'wb') as output:
        try:
            text = file.read()
            text = text.rstrip()
        except UnicodeDecodeError:
            print("Add the following encoding attribute to line 97 for opening the file:")
            print('open(path,\'r\',encoding="ISO-8859-1")')
            sys.exit()

        frequency = build_frequency(text)
        frequency = dict(sorted(frequency.items(), key=lambda kv:kv[1], reverse = True))

        stack = []
        for key, value in frequency.items():
            node = TreeNode(frequency[key],key)
            stack.append(node)
        
        # list holding huffman tree (in position 0)
        huffman_tree = build_huffman_tree(stack)

        mapping_obj = Mapping(huffman_tree)
        mapping_obj.create_mapping()
        mapping_dict = mapping_obj.mapping_dict
        reverse_mapping_dict = mapping_obj.reverse_mapping_dict

        encoded_text = encode_text(text, mapping_dict)
        encoded_tree = encode_mapping(reverse_mapping_dict)
        encoded_text_tree = encode_text_tree(encoded_text, encoded_tree)

        # ensure length of encoded bits is a multiple of 8
        padded_encoded_text_tree = pad_encoded_text_tree(encoded_text_tree)

        a = BitArray(bin = padded_encoded_text_tree)
        a.tofile(output)

    print("Compressed, file can be found at:")
    print(output_file)
    print()

def remove_padding_bits(bit_string):
    padding_info = bit_string[:8]
    padding_bits = int(padding_info, 2)

    # remove padding information from the start of string
    bit_string = bit_string[8:]

    # remove the padding bits from the end of string
    bit_string = bit_string[:-padding_bits]

    return bit_string

def get_encoded_text_mapping(bit_string):
    # form of current bit string:
    # tree_info (16bits) + encoded_text + encoded_tree

    tree_info = bit_string[:16]
    encoded_tree_bits = int(tree_info, 2)
    
    # remove tree information from the start of the string 
    bit_string = bit_string[16:]

    # remove and return the encoded tree from the end of the string
    encoded_tree = bit_string[-encoded_tree_bits:]
    bit_string = bit_string[:-encoded_tree_bits]

    return bit_string, encoded_tree

def decode_mapping(encoded_mapping):
    # convert bit string to dictionary
    # convert from bits to bytes to dictionary
    res_bytes = int(encoded_mapping, 2).to_bytes(len(encoded_mapping) // 8, byteorder='big')
    res_dict = json.loads(res_bytes.decode('utf-8'))
    
    return res_dict


def decode_bits(encoded_text, reverse_dict):
    decoded_text = ""
    code = ""

    for bit in encoded_text:
        code += bit
        if code in reverse_dict:
            decoded_text += reverse_dict[code]
            code = ""
    return decoded_text

def decompress(compressed_path):
    file_path, file_extension = os.path.splitext(compressed_path)
    output_file = file_path + "_decompressed.txt"

    with open(compressed_path, 'rb') as f, open(output_file,'w') as output:
        b = BitArray(f.read())
        b = b.bin

        b = remove_padding_bits(b)
        encoded_text, encoded_mapping = get_encoded_text_mapping(b)
        reverse_mapping_dict = decode_mapping(encoded_mapping)

        text = decode_bits(encoded_text, reverse_mapping_dict)

        output.write(text)

    print("Decompressed, file can be found at:")
    print(output_file)
    print()
        

def main():
    print("---------- Huffman Coding ----------")
    print("Please, enter one of the following: ")
    print("1. Compress file")
    print("2. Decompress file")
    print("3. Exit")
    print()
    option = input()
    os.system('clear')
    
    if option == "1":
        try:
            input_file = input("Please enter the name of the file to be compressed (including extension): ")
            input_file_path = pathlib.Path().absolute().joinpath(input_file)
            compress(input_file_path)
            main()
        except FileNotFoundError:
            print("File not found. Ensure file is in the same directory")
            print()
            main()
    if option == "2":
        try:
            compressed_file = input("Please enter the name of the file to be decompressed (including extension): ")
            compressed_path = pathlib.Path().absolute().joinpath(compressed_file)
            decompress(compressed_path)
            main()
        except OverflowError:
            print("Please enter a .bin file")
            print()
            main()
    if option == "3":
        print("Quitting application")
        sys.exit()
    else:
        main()


if __name__ == "__main__":
    main()