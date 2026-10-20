import unittest

import compiler
from compiler import (
    BinaryOp,
    Number,
    parse,
    parse_addition,
    parse_multiplication,
    parse_number_or_group,
    tokenizer,
)


# 계산 결과만 보면 결합 순서를 놓칠 수 있으니 트리 모양을 비교하자!
def ast_shape(node):
    if isinstance(node, Number):
        return node.value
    if isinstance(node, BinaryOp):
        return (node.operator, ast_shape(node.left), ast_shape(node.right))
    raise AssertionError(f"알 수 없는 AST 노드: {node!r}")


class ParserTests(unittest.TestCase):
    def test_expression_structure(self):
        cases = [
            ("0", 0),
            ("42", 42),
            (" \t12 +\r\n34", ("+", 12, 34)),
            ("2 + 3 * 4", ("+", 2, ("*", 3, 4))),
            ("2 * 3 + 4", ("+", ("*", 2, 3), 4)),
            ("(2 + 3) * 4", ("*", ("+", 2, 3), 4)),
            ("2 * (3 + 4)", ("*", 2, ("+", 3, 4))),
            ("((2 + 3) * (4 + 5))", ("*", ("+", 2, 3), ("+", 4, 5))),
            ("2 + 3 * 4 + 5", ("+", ("+", 2, ("*", 3, 4)), 5)),
            ("2 + 3 + 4", ("+", ("+", 2, 3), 4)),
            ("2 * 3 * 4", ("*", ("*", 2, 3), 4)),
            ("((7))", 7),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                node = parse(tokenizer(source))
                self.assertEqual(ast_shape(node), expected)

    def test_number_or_group_consumes_one_integer(self):
        tokens = tokenizer("2 + 34 * 5")
        node, position = parse_number_or_group(tokens, 2)
        self.assertEqual(ast_shape(node), 34)
        self.assertEqual(position, 3)
        self.assertEqual(tokens[position][0], "STAR")

    def test_number_or_group_consumes_closing_parenthesis(self):
        tokens = tokenizer("(2 + 3) * 4")
        node, position = parse_number_or_group(tokens, 0)
        self.assertEqual(ast_shape(node), ("+", 2, 3))
        self.assertEqual(position, 5)
        self.assertEqual(tokens[position][0], "STAR")

    def test_multiplication_leaves_plus_for_addition(self):
        tokens = tokenizer("2 * 3 + 4")
        node, position = parse_multiplication(tokens, 0)
        self.assertEqual(ast_shape(node), ("*", 2, 3))
        self.assertEqual(position, 3)
        self.assertEqual(tokens[position][0], "PLUS")

    def test_addition_leaves_closing_parenthesis_for_number_or_group(self):
        tokens = tokenizer("2 + 3)")
        node, position = parse_addition(tokens, 0)
        self.assertEqual(ast_shape(node), ("+", 2, 3))
        self.assertEqual(position, 3)
        self.assertEqual(tokens[position][0], "RPAREN")

    def test_syntax_error_reports_source_position(self):
        cases = [
            ("", 0),
            (" \t\n", 3),
            ("+2", 0),
            ("*2", 0),
            ("2 +", 3),
            ("2 *", 3),
            ("2 + * 3", 4),
            ("()", 1),
            ("(", 1),
            ("(2 + 3", 6),
            ("2 + 3)", 5),
            ("2 3", 2),
            ("2(3)", 1),
            ("(2)3", 3),
            ("2 ** 3", 3),
            ("2 ++ 3", 3),
        ]
        for source, position in cases:
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, f"^위치 {position}:"):
                    parse(tokenizer(source))


class CodeGeneratorTests(unittest.TestCase):
    def test_generates_python_from_manually_connected_nodes(self):
        node = BinaryOp("*", BinaryOp("+", Number(2), Number(3)), Number(4))
        python_source = compiler.generate_python(node)
        self.assertIsInstance(python_source, str)
        self.assertEqual(eval(python_source, {"__builtins__": {}}), 20)

    def test_rejects_unknown_node(self):
        with self.assertRaises(TypeError):
            compiler.generate_python(None)


class CompilerTests(unittest.TestCase):
    def test_generated_python_evaluates_correctly(self):
        cases = [
            ("0", 0),
            ("42", 42),
            ("2 + 3 * 4", 14),
            ("(2 + 3) * 4", 20),
            ("2 * (3 + 4)", 14),
            ("((2 + 3) * (4 + 5))", 45),
            ("2 + 3 * 4 + 5", 19),
            ("2 * 3 + 4", 10),
            ("0007 + 03", 10),
            (" \t12 +\r\n34", 46),
            ("2 + 3 + 4", 9),
            ("2 * 3 * 4", 24),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                python_source = compiler.compile_source(source)
                self.assertIsInstance(python_source, str)
                self.assertEqual(eval(python_source, {"__builtins__": {}}), expected)

    def test_invalid_source_is_rejected_before_code_generation(self):
        for source in ("2 +", "2 / 3"):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    compiler.compile_source(source)


if __name__ == "__main__":
    unittest.main()
