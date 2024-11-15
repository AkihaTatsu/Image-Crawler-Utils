from __future__ import annotations
import dataclasses
import itertools
import traceback
import unicodedata
from typing import Optional, Union
from collections.abc import Iterable

from image_crawler_utils.log import Log



@dataclasses.dataclass
class KeywordLogicTree:
    """
    A binary tree to record the logic structure of keywords.
    
    Attributes:
        simplify_tree(): Simplify the tree structure by cleaning "SINGLE" nodes and double "NOT" nodes.
        is_leaf(): Whether current tree is a leaf node.
        list_struct(): Return the structure of the tree in a list.
        all_keywords(): Return all keywords in this tree in a list.
        keyword_list_check(): Check whether current keyword list is valid.
        keyword_include_group_list(): Return a list of keyword groups. The images with valid keywords are a subset of the images from the result of  searching all keywords in the keyword group connected by "OR".
    """

    son1: Union[str, KeywordLogicTree] = ''
    son2: Union[str, KeywordLogicTree] = ''
    # Logic operator, should only be in "AND", "OR", "NOT", "SINGLE"; when it is "NOT" or "SINGLE", son1 should be omiited
    # "SINGLE" means this node has only one element son2. After building a tree, use simplify_tree() to simplify these nodes.
    logic_operator: str = "SINGLE"

    def __post_init__(self):
        if self.logic_operator not in ("AND", "OR", "NOT", "SINGLE"):
            self.logic_operator = "SINGLE"


    def __expr__(self):
        return build_standard_keyword_str(self)

    
    # Remove any "SINGLE" successor nodes except the current node, and simplify double negative structure
    def simplify_tree(self) -> None:
        """
        Simplify the tree structure by cleaning "SINGLE" nodes and double "NOT" nodes.
        """

        if type(self.son1) is not str:
            self.son1.simplify_tree()
        if type(self.son2) is not str:
            self.son2.simplify_tree()

        if type(self.son1) is not str:
            if self.son1.logic_operator == "SINGLE":
                self.son1 = self.son1.son2
            elif self.son1.logic_operator == "NOT":
                if type(self.son1.son2) is not str and self.son1.son2.logic_operator == "NOT":
                    self.son1 = self.son1.son2.son2

        if type(self.son2) is not str:
            if self.son2.logic_operator == "SINGLE":
                self.son2 = self.son2.son2
            elif self.son2.logic_operator == "NOT":
                if type(self.son2.son2) is not str and self.son2.son2.logic_operator == "NOT":
                    self.son2 = self.son2.son2.son2
                    

    # Check whether it is leaf node
    def is_leaf(self) -> bool:
        """
        Whether current tree is a leaf node.

        Returns:
            A boolean.
        """

        if (self.logic_operator == "NOT" or self.logic_operator == "SINGLE") and type(self.son2) is str:
            return True
        elif type(self.son1) == type(self.son2) and type(self.son1) is str:
            return True
        else:
            return False
        

    # Return this tree as list structure
    def list_struct(self) -> list:
        """
        Return the structure of the tree in a list.

        Returns:
            A list with the structure of this keyword tree.
        """

        if type(self.son2) is str:
            key_list2 = self.son2
        else:
            key_list2 = self.son2.list_struct()

        if self.logic_operator == "NOT" or self.logic_operator == "SINGLE":
            return [self.logic_operator, key_list2]
        else:
            if type(self.son1) is str:
                key_list1 = self.son1
            else:
                key_list1 = self.son1.list_struct()
            return [key_list1, self.logic_operator, key_list2]

    
    # Return all keywords in a list
    def all_keywords(self) -> list[str]:
        """
        Return all keywords in this tree in a list.

        Returns:
            A list with all the keywords in this tree.
        """

        if type(self.son1) is str:
            key_list1 = [self.son1]
        else:
            key_list1 = self.son1.all_keywords()        
        if type(self.son2) is str:
            key_list2 = [self.son2]
        else:
            key_list2 = self.son2.all_keywords()

        if self.logic_operator in ["NOT", "SINGLE"]:
            return key_list2
        elif self.logic_operator in ["AND", "OR"]:
            return list(set([*key_list1, *key_list2]))
    

    # Check if a keyword list is acceptable
    def keyword_list_check(self, keyword_list: Iterable[str]) -> bool:
        """
        Check whether current keyword list is valid.

        Parameters:
            keyword_list (list of strings): The keyword list to check.

        Returns:
            A boolean.
        """

        edited_keyword_list = [unicodedata.normalize("NFKC", keyword) for keyword in keyword_list]  # No full-width characters!

        def match_str(pattern, string):
            begin_asterisk = True if pattern[0] == '*' else False
            end_asterisk = True if pattern[-1] == '*' else False
            split_str_list = [split_str for split_str in pattern.split('*') if len(split_str) > 0]
            match_index = []
            for i in range(len(split_str_list)):
                previous = match_index[i - 1] + 1 if i > 0 else 0
                match_index.append(string[previous:].find(split_str_list[i]) + previous)
            for i in range(len(match_index) - 1):
                if match_index[i] >= match_index[i + 1]:
                    return False
            if not begin_asterisk and match_index[0] != 0:
                return False
            if not end_asterisk and match_index[-1] + len(split_str_list[-1]) != len(string):
                return False
            return True
        
        if len(edited_keyword_list) <= 0:
            return False
        if type(self.son1) is str:
            if self.logic_operator in ["AND", "OR"]:
                flag = False
                for key in keyword_list:
                    if match_str(self.son1, key):
                        flag = True
                res1 = flag
        else:
            res1 = self.son1.keyword_list_check(edited_keyword_list)
        if type(self.son2) is str:
            flag = False
            for key in keyword_list:
                if match_str(self.son2, key):
                    flag = True
            res2 = flag
        else:
            res2 = self.son2.keyword_list_check(edited_keyword_list)

        if self.logic_operator == "AND":
            return res1 and res2
        elif self.logic_operator == "OR":
            return res1 or res2
        elif self.logic_operator == "NOT":
            return not res2
        elif self.logic_operator == "SINGLE":
            return res2
        
    
    # Output keyword lists that "CONTAIN" all possible results
    # Example: for "A AND (B OR C)", search A can contain all possible results
    def keyword_include_group_list(self) -> list[list]:
        """
        Return a list of keyword groups. The images with valid keywords are a subset of the images from the result of  searching all keywords in the keyword group connected by "OR".

        Parameters:
            The keyword list to check.

        Returns:
            A list of keyword groups (i.e. lists of keywords).
        """

        if type(self.son2) is str:
            key_list_list2 = [[self.son2]]
        else:
            key_list_list2 = self.son2.keyword_include_group_list()
        
        if self.logic_operator == "SINGLE":
            return key_list_list2
        elif self.logic_operator == "NOT":
            return []
        else:
            if type(self.son1) is str:
                key_list_list1 = [[self.son1]]
            else:
                key_list_list1 = self.son1.keyword_include_group_list()
            
            if self.logic_operator == "AND":
                new_list = [*key_list_list1, *key_list_list2]
                return [new_list[i] for i in range(len(new_list))
                        if new_list[i] not in new_list[:i]]  # Remove same element
            elif self.logic_operator == "OR":
                new_list = [[*key_list1, *key_list2]
                            for key_list1 in key_list_list1 
                            for key_list2 in key_list_list2]
                return [new_list[i] for i in range(len(new_list)) 
                        if new_list[i] not in new_list[:i]]  # Remove same element



##### Functions


# Minimal length keyword group select
def min_len_keyword_group(keyword_group_list: Iterable[Iterable], below: Optional[int]=None) -> list[list]:
    """
    For a list of keyword groups (i.e. lists of keywords), get a list of keyword group with the smallest length.
    
    Parameters:
        keyword_group_list (list of list of string): A list of keyword groups.
        below (int): If not None, try return all keyword group with length below "below" parameter. If such groups don't exist, return the one with the smallest length.

    Returns:
        A list of keyword groups (i.e. lists of keywords)
    """
    if(len(keyword_group_list) <= 0):
        return []
    
    min_group_list = [keyword_group_list[0]]
    min_len = len(keyword_group_list[0])

    if below is not None:
        below_group_list = []
        
    for group in keyword_group_list:
        
        if below is not None and len(group) <= below and group not in below_group_list:
            below_group_list.append(group)

        if len(group) < min_len:
            min_len = len(group)
            min_group_list = [group]
        elif len(group) == min_len and group not in min_group_list:
            min_group_list.append(group)

    if len(below_group_list) > 0:
        return below_group_list
    else:
        return min_group_list


# Standard keyword string built from a tree
def build_standard_keyword_str(tree: KeywordLogicTree):
    """
    Build a standard keyword string from a tree.

    Returns:
        A standard keyword string.
    """

    if isinstance(tree.son1, str):
        res1 = tree.son1
    else:
        res1 = build_standard_keyword_str(tree.son1)
    if isinstance(tree.son2, str):
        res2 = tree.son2
    else:
        res2 = build_standard_keyword_str(tree.son2)

    if tree.logic_operator == "AND":
        return f'[{res1} AND {res2}]'
    elif tree.logic_operator == "OR":
        return f'[{res1} OR {res2}]'
    elif tree.logic_operator == "NOT":
        return f'[NOT {res2}]'
    elif tree.logic_operator == "SINGLE":
        return f'{res2}'
    

##### Functions related to construction of a keyword tree


# Build element list from string and do some cleaning up
def __from_str_to_elem_list(keyword_str, log: Log=Log()):
    def replace_clean_str(original_str, search_str, replace_str, cleanup_replace_str=True):
        new_str = original_str
        if type(search_str) in [list, tuple, set]:
            for string in search_str:
                while(string) in new_str:
                    new_str = new_str.replace(string, replace_str)
        else:
            while(search_str) in new_str:
                new_str = new_str.replace(search_str, replace_str)
        if cleanup_replace_str:
            while len(replace_str) > 0 and replace_str + replace_str in new_str:
                new_str = new_str.replace(replace_str + replace_str, replace_str)
        return new_str
    
    new_str = unicodedata.normalize("NFKC", keyword_str).strip()  # No full-width characters!
    if len(new_str) == 0:  # Empty!
        return []
    new_str = new_str.replace('[', ' [ ')
    new_str = new_str.replace(']', ' ] ')
    new_str = replace_clean_str(new_str, ' ', '_')
    new_str = replace_clean_str(new_str, '**', '*')

    word_to_symbol = {"AND": '&', "OR": '|', "NOT": '!'}
    for word, symbol in word_to_symbol.items():
        new_str = replace_clean_str(new_str, 
                                    f'_{word}_', 
                                    f'_{symbol}_', 
                                    cleanup_replace_str=False)
    for symbol in word_to_symbol.values():
        new_str = replace_clean_str(new_str, 
                                    [f'_{symbol}_',
                                     f'_{symbol}',
                                     f'{symbol}_'],
                                    f'{symbol}', 
                                    cleanup_replace_str=False)
        
    new_str = replace_clean_str(new_str, '!!', '')

    if '&&' in new_str or '||' in new_str:
        log.critical("Invalid keyword syntax.")
        return None

    # Split but insert split str into the middle
    def advanced_split(original_str_list, split_str, keep=True):
        new_str_list = original_str_list
        for i in range(len(new_str_list)):
            changed_str = new_str_list[i].split(split_str)
            if keep:
                changed_str_2 = []
                for j in range(len(changed_str) - 1):
                    changed_str_2.append(changed_str[j])
                    changed_str_2.append(split_str)
                changed_str_2.append(changed_str[-1])
                new_str_list[i] = changed_str_2
            else:
                new_str_list[i] = changed_str
        return list(itertools.chain.from_iterable(new_str_list))

    operator_list = ['&', '|', '!', '[', ']']
    new_str_list = [new_str]
    for operator in operator_list:
        new_str_list = advanced_split(new_str_list, operator)
    new_str_list = [item.strip('_') for item in new_str_list if len(item) > 0 and item != '_']

    return new_str_list


# build_binary_tree func
def __build_binary_tree(element_list, log: Log=Log()) -> Optional[KeywordLogicTree]:
    if len(element_list) == 0:  # Empty!
        return KeywordLogicTree()

    operator_dict = {'&': "AND", '|': "OR", '!': "NOT"}
    two_elem_operands = ['&', '|']
    one_elem_operands = ['!']
    edited_element_list = ['['] + element_list + [']']
    operand_priority = {
        '[': 15,
        ']': 15,
        '!': 14,
        '&': 5,
        '|': 4,
    }  # Bigger the number, higher the priority
    operand_stack = []
    keyword_stack = []

    # Define the operand popping func
    def pop_operand_stack(push_elem):
        last_elem = push_elem
        while (push_elem == ']' and last_elem != '[') or (len(operand_stack) > 0 
            and operand_priority[last_elem] <= operand_priority[operand_stack[-1]]):
            # Pop operand stack and do operations
            popped_operand = operand_stack.pop()
            last_elem = popped_operand
            if popped_operand in one_elem_operands:
                keyword = keyword_stack.pop()
                node = KeywordLogicTree(
                    logic_operator=operator_dict[popped_operand],
                    son2=keyword,
                )
                keyword_stack.append(node)
            elif popped_operand in two_elem_operands:
                keyword1 = keyword_stack.pop()
                keyword2 = keyword_stack.pop()
                node = KeywordLogicTree(
                    son1=keyword2,
                    logic_operator=operator_dict[popped_operand],
                    son2=keyword1,
                )
                keyword_stack.append(node)
            elif popped_operand in ['[']:
                operand_stack.append(popped_operand)
                break
            else:
                raise ValueError(f'Invalid operand: {popped_operand}')
        operand_stack.append(push_elem)
        if len(operand_stack) > 2 and operand_stack[-1] == ']' and operand_stack[-2] == '[':
            operand_stack.pop()
            operand_stack.pop()

    # Running the pushing and popping
    try:
        for elem in edited_element_list:
            if elem not in operand_priority.keys():
                keyword_stack.append(elem)
                if operand_stack[-1] in one_elem_operands:
                    node = KeywordLogicTree(
                        logic_operator=operator_dict[operand_stack[-1]],
                        son2=keyword_stack.pop(),
                    )
                    keyword_stack.append(node)
                    operand_stack.pop()
                    pop_operand_stack(push_elem=operand_stack.pop())
            else:
                pop_operand_stack(push_elem=elem)
        return KeywordLogicTree(logic_operator='SINGLE', son2=keyword_stack[0])
    except Exception as e:
        output_msg_base = f"Invalid keyword syntax"
        log.critical(f"{output_msg_base}.\n{traceback.format_exc()}", output_msg=f"{output_msg_base} because {e}")
        raise ValueError(f"{output_msg_base}.")
    

# Construct keyword tree
def construct_keyword_tree(keyword_str: str, log: Log=Log()) -> Optional[KeywordLogicTree]:
    """
    Use a standard syntax to represent logic relationship of keywords.
    Use ' AND ' / '&', ' OR ' / '|', ' NOT ' / '!' to represent logic operators.
    Use '[', ']' to increase logic priority.
    Any space between two keywords will be replaced with '_' and consider them as one keyword.
    Example: A B + [C (extra) OR NOT D] -> A_B AND [C_(extra) OR NOT D]

    Parameters:
        keyword_str (str): A string of keywords.
        log (crawler_utils.log.Log, optional): The logging config.

    Returns:
        If successful, returns a KeywordLogicTree.
        If failed, return None.
    """

    # Check result
    res = __build_binary_tree(__from_str_to_elem_list(keyword_str), log=log)
    res.simplify_tree()  # Simplify the tree
    return res
    

# Convert keyword list (like [A, B, C]) into a tree for (A OR B OR C)
def keyword_list_tree(keyword_list: Iterable[str], log: Log=Log()) -> Optional[KeywordLogicTree]:
    """
    Convert a list of keywords into a keyword tree connected by "OR".
    e.g. ['A', 'B', 'C'] -> [['A' OR 'B'] OR 'C']

    Parameters:
        keyword_str (Iterable(str)): A list of strings.
        log (crawler_utils.log.Log, optional): The logging config.

    Returns:
        If successful, returns a KeywordLogicTree.
        If failed, return None.
    """

    new_kw_list = [key.strip() for key in keyword_list if len(key.strip()) > 0]  # Remove '' and space-only string, and space at words' both sides
    return construct_keyword_tree(' | '.join(new_kw_list), log=log)
