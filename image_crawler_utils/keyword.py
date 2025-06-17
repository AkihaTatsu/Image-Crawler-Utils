from __future__ import annotations
import dataclasses
import itertools
import traceback
import unicodedata
from typing import Optional, Union
from collections.abc import Iterable

from .log import Log



##### Constants


ESCAPE_CHAR_DICT = {
    '\\\\': 'Ａ',
    '\\[': 'Ｂ',
    '\\]': 'Ｃ',
    '\\&': 'Ｄ',
    '\\|': 'Ｅ',
    '\\!': 'Ｆ',
}
OPERATOR_DICT = {'&': "AND", '|': "OR", '!': "NOT"}
BINARY_OPERATORS = ['&', '|']
UNARY_OPERATORS = ['!']
OPERATOR_PRIORITY = {
    '[': 15,
    ']': 15,
    '!': 14,
    '&': 5,
    '|': 4,
}  # Bigger the number, higher the priority


##### KeywordLogicTree


@dataclasses.dataclass
class KeywordLogicTree:
    """
    A binary tree to record the logic structure of keywords.
    """

    lchild: Union[str, KeywordLogicTree] = ''
    """Left child."""
    rchild: Union[str, KeywordLogicTree] = ''
    """Right child."""
    logic_operator: str = "SINGLE"
    """
    Logic operator. Can be one of \"AND\", \"OR\", \"NOT\" or \"SINGLE\".
    
    When it is \"NOT\" or \"SINGLE\", lchild should be omiited.
    
    \"SINGLE\" means this node has only one element rchild. After building a tree, use simplify_tree() to simplify these nodes.
    """


    def __post_init__(self):
        if isinstance(self.lchild, str):
            self.lchild = unicodedata.normalize("NFKC", self.lchild.strip())
        if isinstance(self.rchild, str):
            self.rchild = unicodedata.normalize("NFKC", self.rchild.strip())
        if self.logic_operator not in ("AND", "OR", "NOT", "SINGLE"):
            self.logic_operator = "SINGLE"
    

    # Check if it's empty
    def is_empty(self) -> bool:
        """
        Check whether current KeywordLogicTree is empty.

        Returns:
            A boolean denoting whether current tree is empty.
        """

        if self.logic_operator == "SINGLE" and self.rchild == '':
            return True
        else:
            return False
                    

    # Check whether it is leaf node
    def is_leaf(self) -> bool:
        """
        Whether current tree is a leaf node.

        Returns:
            A boolean denoting whether current node is a leaf node.
        """

        if (self.logic_operator == "NOT" or self.logic_operator == "SINGLE") and isinstance(self.rchild, str):
            return True
        elif type(self.lchild) == type(self.rchild) and isinstance(self.lchild, str):
            return True
        else:
            return False

    
    # Remove any "SINGLE" successor nodes except the current node, and simplify double negative structure
    def simplify_tree(self) -> None:
        """
        Simplify the tree structure, including: NOT NOT key -> key and SINGLE key -> key.

            + If you create a KeywordLogicTree through the functions provided, ``.simplify_tree()`` will be automatically executed.
        """

        if isinstance(self.lchild, KeywordLogicTree):
            self.lchild.simplify_tree()
        if isinstance(self.rchild, KeywordLogicTree):
            self.rchild.simplify_tree()

        if isinstance(self.lchild, KeywordLogicTree):
            if self.lchild.logic_operator == "SINGLE":
                self.lchild = self.lchild.rchild
            elif self.lchild.logic_operator == "NOT":
                if isinstance(self.lchild.rchild, KeywordLogicTree) and self.lchild.rchild.logic_operator == "NOT":
                    self.lchild = self.lchild.rchild.rchild

        if isinstance(self.rchild, KeywordLogicTree):
            if self.rchild.logic_operator == "SINGLE":
                self.rchild = self.rchild.rchild
            elif self.rchild.logic_operator == "NOT":
                if isinstance(self.rchild.rchild, KeywordLogicTree) and self.rchild.rchild.logic_operator == "NOT":
                    self.rchild = self.rchild.rchild.rchild

        if self.logic_operator == "SINGLE" and isinstance(self.rchild, KeywordLogicTree):
            self.logic_operator = self.rchild.logic_operator
            self.lchild = self.rchild.lchild
            self.rchild = self.rchild.rchild
        

    # Return this tree as list structure
    def list_struct(self) -> list:
        """
        Returns the structure of current tree as a recursive :py:class:`list`.

            + For example, standard keyword string "A AND B OR C" will be returned as ``[['A', 'AND', 'B'], 'OR', 'C']``.

        Returns:
            A list with the structure of this keyword tree.
        """

        if isinstance(self.rchild, str):
            key_list2 = self.rchild
        else:
            key_list2 = self.rchild.list_struct()

        if self.logic_operator == "NOT" or self.logic_operator == "SINGLE":
            return [self.logic_operator, key_list2]
        else:
            if isinstance(self.lchild, str):
                key_list1 = self.lchild
            else:
                key_list1 = self.lchild.list_struct()
            return [key_list1, self.logic_operator, key_list2]
        

    # Return this tree as a standard keyword string
    def standard_keyword_string(self) -> str:
        """
        Returns the reconstructed standard keyword string.
                    
            + The result may not be the same as the string that is used to construct the KeywordLogicTree.
            + For example, standard keyword string "A AND B OR C" will be returned as "[[A AND B] OR C]".

        Returns:
            A standard keyword string.
        """

        if isinstance(self.lchild, str):
            res1 = self.lchild
            for key in ESCAPE_CHAR_DICT.keys():
                res1 = res1.replace(key[1], key)
        else:
            res1 = self.lchild.standard_keyword_string()
        if isinstance(self.rchild, str):
            res2 = self.rchild
            for key in ESCAPE_CHAR_DICT.keys():
                res2 = res2.replace(key[1], key)
        else:
            res2 = self.rchild.standard_keyword_string()

        if self.logic_operator == "AND":
            return f'[{res1} AND {res2}]'
        elif self.logic_operator == "OR":
            return f'[{res1} OR {res2}]'
        elif self.logic_operator == "NOT":
            return f'[NOT {res2}]'
        elif self.logic_operator == "SINGLE":
            return f'{res2}'

    
    # Return all keywords in a list
    def all_keywords(self) -> list[str]:
        """
        Return all keywords in this tree in a list.

        Returns:
            A list with all the keywords in this tree.
        """

        if isinstance(self.lchild, str):
            key_list1 = [self.lchild]
        else:
            key_list1 = self.lchild.all_keywords()        
        if isinstance(self.rchild, str):
            key_list2 = [self.rchild]
        else:
            key_list2 = self.rchild.all_keywords()

        if self.logic_operator in ["NOT", "SINGLE"]:
            return key_list2
        elif self.logic_operator in ["AND", "OR"]:
            return list(set([*key_list1, *key_list2]))
    

    # Check if a keyword list is acceptable
    def keyword_list_check(self, keyword_list: Iterable[str]) -> bool:
        """
        Check whether the keyword list matches this tree.

            + For example, keyword list ``['A', 'B']``, ``['C', 'D']`` and ``['A', 'B', 'C']`` match "A AND B OR C", while keyword list ``['B', 'D']`` cannot match "A AND B OR C".

        Args:
            keyword_list (list[str]): The keyword list to check.

        Returns:
            A boolean denoting if the keyword list matches this tree.
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
        if isinstance(self.lchild, str):
            if self.logic_operator in ["AND", "OR"]:
                flag = False
                for key in keyword_list:
                    if match_str(self.lchild, key):
                        flag = True
                res1 = flag
        else:
            res1 = self.lchild.keyword_list_check(edited_keyword_list)
        if isinstance(self.rchild, str):
            flag = False
            for key in keyword_list:
                if match_str(self.rchild, key):
                    flag = True
            res2 = flag
        else:
            res2 = self.rchild.keyword_list_check(edited_keyword_list)

        if self.logic_operator == "AND":
            return res1 and res2
        elif self.logic_operator == "OR":
            return res1 or res2
        elif self.logic_operator == "NOT":
            return not res2
        elif self.logic_operator == "SINGLE":
            return res2
        
    
    # Output keyword groups that "CONTAIN" all possible results
    def keyword_include_group_list(self) -> list[list[str]]:
        """
        Returns a list of keyword groups (list of keywords) which are minimal supersets of current tree.

            + For example:

                + For "A AND B OR C", its minimal supersets are ``['A', 'C']`` and ``['B', 'C']``.

                    + That is, if you search "A OR C" or "B OR C", you can get all results that match "A AND B OR C". 

                + For "A AND [B OR C]", its minimal supersets are ``['A']`` and ``['B', 'C']``.

            + Useful for websites that have a restriction on the number of keywords when seaching.

        Returns:
            A list of keyword groups (i.e. lists of keywords).
        """

        if isinstance(self.rchild, str):
            key_list_list2 = [[self.rchild]]
        else:
            key_list_list2 = self.rchild.keyword_include_group_list()
        
        if self.logic_operator == "SINGLE":
            return key_list_list2
        elif self.logic_operator == "NOT":
            return []
        else:
            if isinstance(self.lchild, str):
                key_list_list1 = [[self.lchild]]
            else:
                key_list_list1 = self.lchild.keyword_include_group_list()
            
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


##### Functions related to construction of a keyword tree


# Build element list from string and do some cleaning up
def __from_str_to_elem_list(keyword_str):
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
    
    # Replace escape character with full-width codes (as string itself has been NFKC normalized)
    for key, value in ESCAPE_CHAR_DICT.items():
        new_str = new_str.replace(key, value)

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

    # Check if there are TWO_ELEM_OPERANDS that are adjacent to each other
    
    if len(new_str_list) > 1:
        for i in range(len(new_str_list) - 1):
            if new_str_list[i] in BINARY_OPERATORS and new_str_list[i + 1] in BINARY_OPERATORS:
                raise SyntaxError(f"Binary operators cannot be adjacent to each other.")

    # Restore escape characters
    restore_char_dict = {value: key[1] 
                         for key, value in ESCAPE_CHAR_DICT.items()}
    for i in range(len(new_str_list)):
        for key, value in restore_char_dict.items():
            new_str_list[i] = new_str_list[i].replace(key, value)

    return new_str_list


# build_binary_tree func
def __build_binary_tree(element_list, log: Log=Log()) -> KeywordLogicTree:
    if len(element_list) == 0:  # Empty!
        return KeywordLogicTree()

    edited_element_list = ['['] + element_list + [']']
    operator_stack = []
    keyword_stack = []

    # Define the operator popping func
    def pop_operator_stack(push_elem):
        last_elem = push_elem
        while (push_elem == ']' and last_elem != '[') or (len(operator_stack) > 0 
            and OPERATOR_PRIORITY[last_elem] <= OPERATOR_PRIORITY[operator_stack[-1]]):
            # Pop operator stack and do operations
            popped_operator = operator_stack.pop()
            last_elem = popped_operator
            if popped_operator in UNARY_OPERATORS:
                keyword = keyword_stack.pop()
                node = KeywordLogicTree(
                    logic_operator=OPERATOR_DICT[popped_operator],
                    rchild=keyword,
                )
                keyword_stack.append(node)
            elif popped_operator in BINARY_OPERATORS:
                keyword1 = keyword_stack.pop()
                keyword2 = keyword_stack.pop()
                node = KeywordLogicTree(
                    lchild=keyword2,
                    logic_operator=OPERATOR_DICT[popped_operator],
                    rchild=keyword1,
                )
                keyword_stack.append(node)
            elif popped_operator in ['[']:
                operator_stack.append(popped_operator)
                break
            else:
                raise ValueError(f'Invalid operator: {popped_operator}')
        operator_stack.append(push_elem)
        if len(operator_stack) > 2 and operator_stack[-1] == ']' and operator_stack[-2] == '[':
            operator_stack.pop()
            operator_stack.pop()

    # Running the pushing and popping
    try:
        for elem in edited_element_list:
            if elem not in OPERATOR_PRIORITY.keys():
                keyword_stack.append(elem)
                if operator_stack[-1] in UNARY_OPERATORS:
                    node = KeywordLogicTree(
                        logic_operator=OPERATOR_DICT[operator_stack[-1]],
                        rchild=keyword_stack.pop(),
                    )
                    keyword_stack.append(node)
                    operator_stack.pop()
                    pop_operator_stack(push_elem=operator_stack.pop())
            else:
                pop_operator_stack(push_elem=elem)
        return KeywordLogicTree(logic_operator='SINGLE', rchild=keyword_stack[0])
    except Exception as e:
        output_msg_base = f"Invalid keyword syntax"
        log.critical(f"{output_msg_base}.\n{traceback.format_exc()}", output_msg=f"{output_msg_base} because {e}")
        raise ValueError(f"{output_msg_base}.")
    

# Construct keyword tree
def construct_keyword_tree(
    keyword_str: str, 
    log: Log=Log(),
) -> KeywordLogicTree:
    """
    Use a standard syntax to represent logic relationship of keywords.
    Use ' AND ' / '&', ' OR ' / '|', ' NOT ' / '!' to represent logic operators.

    Use '[', ']' to increase logic priority.

    + Any space between two keywords will be replaced with '_' and thus be considered as one keyword.

        + Example: "A B & [C (extra) OR NOT D]" -> "A_B AND [C_(extra) OR NOT D]"

    Args:
        keyword_str (str): A string of keywords.
        log (image_crawler_utils.log.Log, None): The logging config.

    Returns:
        If successful, returns a KeywordLogicTree.
        If failed, return None.
    """

    # Check result
    res = __build_binary_tree(__from_str_to_elem_list(keyword_str), log=log)
    res.simplify_tree()  # Simplify the tree
    return res
    

# Convert keyword list (like [A, B, C]) into a tree for (A OR B OR C)
def construct_keyword_tree_from_list(
    keyword_list: Iterable[str], 
    connect_symbol: str='OR', 
    log: Log=Log(),
) -> KeywordLogicTree:
    """
    Convert a list of keywords into a keyword tree connected by connect_symbol (default is "OR").

    e.g. ``['A', 'B', 'C']`` -> ``[['A' OR 'B'] OR 'C']``

    Args:
        keyword_str (Iterable(str)): A list of strings.
        connect_symbol (str): Logic symbol of connection. Must be one of 'AND', 'OR', '&' or '|'.
        log (image_crawler_utils.log.Log, None): The logging config.

    Returns:
        If successful, returns a KeywordLogicTree.
        If failed, return None.
    """

    connect_symbol_pool = BINARY_OPERATORS + [OPERATOR_DICT[operator] for operator in BINARY_OPERATORS]
    connect_symbol = connect_symbol.strip()
    if connect_symbol not in connect_symbol_pool:
        log.warning(f"Connection symbol {connect_symbol} is not one of {connect_symbol_pool} and will be set to 'OR' (default).")
        connect_symbol = 'OR'
    new_kw_list = [key.strip() for key in keyword_list if len(key.strip()) > 0]  # Remove '' and space-only string, and space at words' both sides
    return construct_keyword_tree((f' {connect_symbol} ').join(new_kw_list), log=log)


##### Other Functions


# Minimal length keyword group select
def min_len_keyword_group(
    keyword_group_list: Iterable[Iterable],
    below: Optional[int]=None,
) -> list[list]:
    """
    For a list of keyword groups (i.e. lists of keywords), get a list of keyword group with the smallest length, or all keyword groups whose length are no larger than ``below``.
    
    Args:
        keyword_group_list (list[list[str]]): A list of keyword groups.
        below (int): If not None, try return all keyword group with length below "below" parameter. If such groups don't exist, return the one with the smallest length.

    Returns:
        A list of keyword groups (i.e. lists of keywords)
    """
    if(len(keyword_group_list) <= 0):
        return []
    
    min_group_list = [keyword_group_list[0]]
    min_len = len(keyword_group_list[0])
    below_group_list = []
        
    for group in keyword_group_list:
        
        if below is not None and len(group) <= below and group not in below_group_list:
            below_group_list.append(group)

        if len(group) < min_len:
            min_len = len(group)
            min_group_list = [group]
        elif len(group) == min_len and group not in min_group_list:
            min_group_list.append(group)

    if below is not None and len(below_group_list) > 0:
        return below_group_list
    else:
        return min_group_list
    