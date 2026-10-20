# 컴파일러를 만들어보자!!

# 기호-토큰 딕셔너리
symbol_kinds = {
    "+": "PLUS",
    "*": "STAR",
    "(": "LPAREN",
    ")": "RPAREN",
}

# AST에서 정수를 담은 노드
class Number:
    def __init__(self, value):
        self.value = value

# AST에서 연산자를 담은 노드
class BinaryOp:
    def __init__(self, value, left, right):
        self.operator = value
        self.left = left
        self.right = right

# 현재 위치에서 정수 '하나'를 읽는 함수
# 입력: (문자열, 숫자가 시작되는 인덱스)
# 출력: (이번 함수 호출로 읽은 정수, 다음 읽을 위치)
def read_integer(source: str, position: int):
    # 시작 인덱스가 가리키는 문자는 숫자다. 숫자가 아닌 문자를 만날 때까지 순회하면 된다.
    len_source = len(source)
    n = position
    nums = ''

    # 문자열 끝까지 순회
    # 중간에 숫자가 아닌 문자를 만나면 while문을 나옴
    # (이번 함수 호출로 읽은 정수, 다음 읽을 위치)를 return
    while len_source >= n + 1:
        if not source[n].isdigit() or not '0' <= source[n] <= '9':
            break
        else:
            nums = nums + source[n]
            n = n + 1
    return (int(nums), n)


# tokenizer 함수를 만들자!
# 입력: 원본 문자열
# 출력: 토큰을 입력 순서대로 받은 리스트
# 토큰 하나는 다음과 같은 튜플 형태(종류, 값, 위치)

def tokenizer(source):
    len_source = len(source)
    n = 0
    start = 0
    tokens = []

    while len_source >= n + 1:
        """
        1. 숫자를 만나면
            현재 위치를 토큰 시작 위치로 저장
            원본 문자열과 시작 위치를 read_integer 함수로 전송 후 반환된 정수 값으로 토큰 생성
            다음 위치는 그 함수가 반환한 위치로 갱신
        """
        if '0' <= source[n] <= '9':
            start = n
            integer_value, next_position = read_integer(source, start)
            token = ("INTEGER", integer_value, start)
            n = next_position
            tokens.append(token)

        # 2. 기호를 만나면 해당 토큰을 만들고 위치를 한 칸 이동
        elif source[n] in symbol_kinds:
            # (종류, 값, 위치)
            token = (symbol_kinds[source[n]], source[n], n)
            tokens.append(token)
            n = n + 1
        
        # 3. 공백(스페이스바, 탭, \n, \r)을 만나면 위치를 한 칸 이동
        elif source[n] in " \t\r\n":
            n = n + 1

        #4. 그 밖의 문자를 만나면 ValueError 발생. 오류 메시지에는 위치와 문자 표시!
        else:
            raise ValueError(f"위치 {n}: 허용하지 않은 문자 '{source[n]}'")
            
    # 5. 입력 끝에 도달하면 EOF 토큰을 추가하고 목록을 반환
    tokens.append(("EOF", None, len_source))
    return tokens


# 숫자 하나 또는 괄호로 묶인 표현식 하나를 읽자!
# position과 n은 문자열이 아니라 토큰 목록의 인덱스다.
# 출력: (만든 AST, 다음 읽을 토큰 위치)
def parse_number_or_group(tokens, position):
    kind, value, source_position = tokens[position]

    if kind == "INTEGER":
        return (Number(value), position + 1)

    elif kind == "LPAREN":
        node, n = parse_addition(tokens, position + 1)

        # 괄호 안을 다 읽었으니 닫는 괄호까지 여기서 소비해야 한다.
        if tokens[n][0] != "RPAREN":
            source_position = tokens[n][2]
            raise ValueError(f"위치 {source_position}: ')'가 필요합니다.")

        return (node, n + 1)

    else:
        raise ValueError(f"위치 {source_position}: 정수 또는 '('가 필요합니다.")


# 곱셈이 이어지는 동안 트리를 연결하고, 다른 토큰은 남겨 둔다.
def parse_multiplication(tokens, position):
    node, n = parse_number_or_group(tokens, position)

    while tokens[n][0] == "STAR":
        right, n = parse_number_or_group(tokens, n + 1)
        node = BinaryOp("*", node, right)

    return (node, n)


# 오른쪽 항의 곱셈까지 완성한 뒤 덧셈으로 연결하자!
def parse_addition(tokens, position):
    node, n = parse_multiplication(tokens, position)

    while tokens[n][0] == "PLUS":
        right, n = parse_multiplication(tokens, n + 1)
        # 지금까지 만든 트리를 왼쪽 자식으로 넣으면 왼쪽 결합이 된다.
        node = BinaryOp("+", node, right)

    return (node, n)


# tokenizer가 만든 토큰 목록을 받아 AST의 루트 노드를 반환한다.
def parse(tokens):
    node, n = parse_addition(tokens, 0)

    # 표현식을 읽고도 토큰이 남았다면 문법에 맞지 않는 입력이다.
    if tokens[n][0] != "EOF":
        kind, value, source_position = tokens[n]
        raise ValueError(f"위치 {source_position}: 예상하지 못한 토큰 '{value}'")

    return node


# AST를 따라가며 Python 코드 문자열을 만들자!
def generate_python(node):
    if isinstance(node, Number):
        return str(node.value)

    elif isinstance(node, BinaryOp):
        # 자식도 숫자나 연산 노드이므로 같은 함수로 변환하면 된다.
        left = generate_python(node.left)
        right = generate_python(node.right)

        # AST에서 정한 연산 순서가 유지되도록 괄호로 감싼다.
        return f"({left} {node.operator} {right})"

    else:
        raise TypeError("지원하지 않는 AST 노드입니다.")


# 원본 문자열을 받아 Python 코드 문자열로 바꾸는 전체 흐름
def compile_source(source):
    tokens = tokenizer(source)
    node = parse(tokens)
    return generate_python(node)
