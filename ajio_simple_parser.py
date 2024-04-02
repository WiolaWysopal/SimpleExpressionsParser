import math
import operator

from graphviz import Digraph

class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"

class Lexer:
    def __init__(self, text):
        self.text = text.replace(" ", "")
        self.position = 0

    def advance(self):
        self.position += 1

    def current_char(self):
        if self.position < len(self.text):
            return self.text[self.position]
        else:
            return None

    def tokenize(self):
        tokens = []
        while (current_char := self.current_char()) is not None:
            if current_char.isdigit() or (current_char == '.' and self.peek().isdigit()):
                tokens.append(self.number())
            elif current_char.isalpha() or (current_char == 's' and self.peek_ahead(4) == 'sqrt'):
                tokens.append(self.identifier())
            elif current_char in '+-*/()^':
                tokens.append(Token('OPERATOR', current_char))
                self.advance()
            else:
                raise ValueError(f"Illegal character: {current_char}")
        return tokens

    def number(self):
        num_str = ''
        while (current_char := self.current_char()) is not None and (current_char.isdigit() or current_char == '.'):
            num_str += current_char
            self.advance()
        if '.' in num_str:
            return Token('FLOAT', float(num_str))
        return Token('INTEGER', int(num_str))

    def identifier(self):
        id_str = ''
        while (current_char := self.current_char()) is not None and current_char.isalpha():
            id_str += current_char
            self.advance()
        return Token('IDENTIFIER', id_str)

    def peek(self):
        if self.position + 1 < len(self.text):
            return self.text[self.position + 1]
        else:
            return None

    def peek_ahead(self, n):
        end_pos = self.position + n
        if end_pos <= len(self.text):
            return self.text[self.position:end_pos]
        return None

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def parse(self):
        return self.expression()

    def expression(self):
        output_queue = []
        operator_stack = []
        while self.current_token() is not None:
            token = self.current_token()
            if token.type in ['INTEGER', 'FLOAT']:
                output_queue.append(token)
                self.advance()
            elif token.type == 'IDENTIFIER':
                self.advance()
                if self.current_token() and self.current_token().value == '(':
                    operator_stack.append(token)
                    operator_stack.append(self.current_token())  # '('
                    self.advance()
                else:
                    raise ValueError("Function call must be followed by parentheses")
            elif token.value in '+-*/^':
                while operator_stack and operator_stack[-1].value in '+-*/^' and \
                        self.precedence(operator_stack[-1]) >= self.precedence(token):
                    output_queue.append(operator_stack.pop())
                operator_stack.append(token)
                self.advance()
            elif token.value == '(':
                operator_stack.append(token)
                self.advance()
            elif token.value == ')':
                while operator_stack and operator_stack[-1].value != '(':
                    output_queue.append(operator_stack.pop())
                if operator_stack:
                    operator_stack.pop()  # Pop '('
                    if operator_stack and operator_stack[-1].type == 'IDENTIFIER':
                        output_queue.append(operator_stack.pop())
                self.advance()
        while operator_stack:
            output_queue.append(operator_stack.pop())
        return output_queue

    def precedence(self, token):
        if token.type == 'IDENTIFIER' or token.value == '^':
            return 4
        elif token.value in '*/':
            return 3
        elif token.value in '+-':
            return 2
        return 0

    def current_token(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        else:
            return None

    def advance(self):
        self.position += 1

    def build_expression_tree(self):
        stack = []
        for token in self.parse():
            if token.type in ['INTEGER', 'FLOAT']:
                stack.append(Node(token))
            elif token.type == 'OPERATOR':
                right = stack.pop()
                if not stack:
                    raise ValueError("Invalid expression.")
                left = stack.pop()
                stack.append(Node(token, left, right))
            elif token.type == 'IDENTIFIER':
                if not stack:
                    raise ValueError("Invalid function expression.")
                argument = stack.pop()
                stack.append(Node(token, argument, None))
        if len(stack) != 1:
            raise ValueError("Invalid expression.")
        return stack[0]

    def draw_tree(self):
        def add_node_edge(node, graph, parent=None):
            if node is None:
                return
            node_id = str(id(node))
            graph.node(node_id, label=str(node.value.value))
            if parent:
                graph.edge(str(id(parent)), node_id)
            add_node_edge(node.left, graph, node)
            add_node_edge(node.right, graph, node)

        tree_graph = Digraph()
        root = self.build_expression_tree()
        add_node_edge(root, tree_graph)
        tree_graph.render('output', format='png', view=True)
        return 'output.png'

class Evaluator:
    def __init__(self, postfix_tokens):
        self.postfix_tokens = postfix_tokens
        self.stack = []

    def evaluate(self):
        for token in self.postfix_tokens:
            if token.type in ['INTEGER', 'FLOAT']:
                self.stack.append(token.value)
            elif token.type == 'OPERATOR':
                self.evaluate_operator(token.value)
            elif token.type == 'IDENTIFIER':
                self.evaluate_function(token.value)
        if len(self.stack) != 1:
            raise ValueError("Error in evaluation.")
        return self.stack.pop()

    def evaluate_operator(self, operator_symbol):
        if len(self.stack) < 2:
            raise ValueError("Insufficient operands.")
        b = self.stack.pop()
        a = self.stack.pop()

        operation = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '^': operator.pow,
        }.get(operator_symbol)

        if operation is None:
            raise ValueError(f"Unknown operator: {operator_symbol}")
        self.stack.append(operation(a, b))

    def evaluate_function(self, function_name):
        if len(self.stack) < 1:
            raise ValueError("Insufficient operands for the function.")
        argument = self.stack.pop()

        function = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'cotan': lambda x: 1 / math.tan(x) if x != 0 else float('inf'),
            'exp': math.exp,
            'sqrt': math.sqrt,
        }.get(function_name)

        if function is None:
            raise ValueError(f"Unknown function: {function_name}")
        self.stack.append(function(argument))

def main():
    expression = "sqrt(3) + tan(4 * 2) - 1 / (( 2 ^ 2 ) + sin(0))"
    # expression = "8 - 2 * 3 + 7"
    lexer = Lexer(expression)
    tokens = lexer.tokenize()

    parser_for_evaluation = Parser(tokens)
    postfix_tokens = parser_for_evaluation.parse()
    
    rpn_expression = " ".join(str(token.value) for token in postfix_tokens)

    evaluator = Evaluator(postfix_tokens)
    result = evaluator.evaluate()

    print(f"Infix Expression: {expression}")
    print(f"RPN Expression: {rpn_expression}")
    print(f"Result: {result}")

    parser_for_tree = Parser(tokens)
    print("Parsing Tree has written to 'output.png' file")
    parser_for_tree.draw_tree()


if __name__ == "__main__":
    main()


